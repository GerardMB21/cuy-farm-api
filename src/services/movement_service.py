from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

from src.models import Gender, Movement, MovementCreate, MovementType
from src.services.yard_service import get_yard
from src.utils import db
from src.utils.http import ConflictError, NotFoundError

# notDefined is tracked as babies, since their sex is not yet known.
TOTAL_FIELD = {
    Gender.MALE: "totalMales",
    Gender.FEMALE: "totalFemales",
    Gender.NOT_DEFINED: "totalBabies",
}


def _adjust_totals(yard_id: str, deltas: dict[str, int]) -> dict:
    names, values, sets, conditions = {}, {}, [], ["attribute_exists(id)"]
    for i, (field, delta) in enumerate(deltas.items()):
        names[f"#f{i}"] = field
        values[f":d{i}"] = delta
        sets.append(f"#f{i} = #f{i} + :d{i}")
        if delta < 0:
            values[f":min{i}"] = -delta
            conditions.append(f"#f{i} >= :min{i}")
    return {
        "Update": {
            "TableName": db.YARDS_TABLE,
            "Key": db.serialize({"id": yard_id}),
            "UpdateExpression": "SET " + ", ".join(sets),
            "ExpressionAttributeNames": names,
            "ExpressionAttributeValues": db.serialize(values),
            "ConditionExpression": " AND ".join(conditions),
        }
    }


def create_movement(data: MovementCreate) -> Movement:
    get_yard(data.fromYardId)
    if data.toYardId:
        get_yard(data.toYardId)

    movement = Movement(**data.model_dump())
    field = TOTAL_FIELD[movement.genderFrom]
    quantity = movement.quantity

    if movement.type == MovementType.ADD:
        adjustments = [_adjust_totals(movement.fromYardId, {field: quantity})]
    elif movement.type == MovementType.TRANSFER:
        adjustments = [
            _adjust_totals(movement.fromYardId, {field: -quantity}),
            _adjust_totals(movement.toYardId, {field: quantity}),
        ]
    elif movement.type == MovementType.DEFINE:
        target = TOTAL_FIELD[movement.genderTo]
        if movement.toYardId:
            adjustments = [
                _adjust_totals(movement.fromYardId, {field: -quantity}),
                _adjust_totals(movement.toYardId, {target: quantity}),
            ]
        else:
            # Same item can't appear twice in a transaction, so both fields go in one update.
            adjustments = [_adjust_totals(movement.fromYardId, {field: -quantity, target: quantity})]
    else:
        adjustments = [_adjust_totals(movement.fromYardId, {field: -quantity})]

    try:
        db.transact_write(
            [
                {
                    "Put": {
                        "TableName": db.MOVEMENTS_TABLE,
                        "Item": db.serialize(movement.model_dump(mode="json", exclude_none=True)),
                    }
                },
                *adjustments,
            ]
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "TransactionCanceledException":
            raise ConflictError("Not enough animals in the origin yard for this movement")
        raise
    return movement


def get_movement(movement_id: str) -> Movement:
    item = db.get_item(db.MOVEMENTS_TABLE, {"id": movement_id})
    if item is None:
        raise NotFoundError(f"Movement '{movement_id}' not found")
    return Movement(**item)


def list_movements(yard_id: str | None = None) -> list[Movement]:
    condition = None
    if yard_id:
        condition = Attr("fromYardId").eq(yard_id) | Attr("toYardId").eq(yard_id)
    return [Movement(**item) for item in db.scan_items(db.MOVEMENTS_TABLE, condition)]

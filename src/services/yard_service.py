from botocore.exceptions import ClientError

from src.models import Yard, YardCreate, YardUpdate
from src.utils import db
from src.utils.http import ConflictError, NotFoundError


def _name_key(name: str) -> dict[str, str]:
    return {"id": name.strip().casefold()}


def _is_cancelled(exc: ClientError) -> bool:
    return exc.response["Error"]["Code"] == "TransactionCanceledException"


def create_yard(data: YardCreate) -> Yard:
    # Initial counts are the yard's starting stock.
    yard = Yard(
        **data.model_dump(),
        totalMales=data.initialMales or 0,
        totalFemales=data.initialFemales or 0,
        totalBabies=data.initialBabies or 0,
    )
    try:
        db.transact_write(
            [
                {
                    "Put": {
                        "TableName": db.YARD_NAMES_TABLE,
                        "Item": db.serialize({**_name_key(yard.name), "yardId": yard.id}),
                        "ConditionExpression": "attribute_not_exists(id)",
                    }
                },
                {
                    "Put": {
                        "TableName": db.YARDS_TABLE,
                        "Item": db.serialize(yard.model_dump(exclude_none=True, exclude={"total"})),
                        "ConditionExpression": "attribute_not_exists(id)",
                    }
                },
            ]
        )
    except ClientError as exc:
        if _is_cancelled(exc):
            raise ConflictError(f"A yard named '{yard.name}' already exists")
        raise
    return yard


def get_yard(yard_id: str) -> Yard:
    item = db.get_item(db.YARDS_TABLE, {"id": yard_id})
    if item is None:
        raise NotFoundError(f"Yard '{yard_id}' not found")
    return Yard(**item)


def list_yards() -> list[Yard]:
    return [Yard(**item) for item in db.scan_items(db.YARDS_TABLE)]


def update_yard(yard_id: str, data: YardUpdate) -> Yard:
    current = get_yard(yard_id)
    updated = current.model_copy(update={"name": data.name})

    operations = [
        {
            "Put": {
                "TableName": db.YARDS_TABLE,
                "Item": db.serialize(updated.model_dump(exclude_none=True, exclude={"total"})),
                "ConditionExpression": "attribute_exists(id)",
            }
        }
    ]
    if updated.name != current.name:
        operations += [
            {
                "Put": {
                    "TableName": db.YARD_NAMES_TABLE,
                    "Item": db.serialize({**_name_key(updated.name), "yardId": yard_id}),
                    "ConditionExpression": "attribute_not_exists(id)",
                }
            },
            {
                "Delete": {
                    "TableName": db.YARD_NAMES_TABLE,
                    "Key": db.serialize(_name_key(current.name)),
                }
            },
        ]

    try:
        db.transact_write(operations)
    except ClientError as exc:
        if _is_cancelled(exc):
            raise ConflictError(f"A yard named '{updated.name}' already exists")
        raise
    return updated


def delete_yard(yard_id: str) -> None:
    yard = get_yard(yard_id)
    db.transact_write(
        [
            {"Delete": {"TableName": db.YARDS_TABLE, "Key": db.serialize({"id": yard_id})}},
            {"Delete": {"TableName": db.YARD_NAMES_TABLE, "Key": db.serialize(_name_key(yard.name))}},
        ]
    )

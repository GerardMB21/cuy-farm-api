from src.models import MovementCreate
from src.services import movement_service
from src.utils.http import handler, parse_body, response


@handler
def create(event, context):
    movement = movement_service.create_movement(MovementCreate(**parse_body(event)))
    return response(201, movement.model_dump(mode="json"))


@handler
def list_all(event, context):
    yard_id = (event.get("queryStringParameters") or {}).get("yardId")
    movements = movement_service.list_movements(yard_id)
    return response(200, [m.model_dump(mode="json") for m in movements])


@handler
def get(event, context):
    movement = movement_service.get_movement(event["pathParameters"]["movementId"])
    return response(200, movement.model_dump(mode="json"))

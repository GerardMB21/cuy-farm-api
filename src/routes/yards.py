from src.models import YardCreate, YardUpdate
from src.services import yard_service
from src.utils.http import handler, parse_body, response


@handler
def create(event, context):
    yard = yard_service.create_yard(YardCreate(**parse_body(event)))
    return response(201, yard.model_dump())


@handler
def list_all(event, context):
    return response(200, [y.model_dump() for y in yard_service.list_yards()])


@handler
def get(event, context):
    yard = yard_service.get_yard(event["pathParameters"]["yardId"])
    return response(200, yard.model_dump())


@handler
def update(event, context):
    yard = yard_service.update_yard(event["pathParameters"]["yardId"], YardUpdate(**parse_body(event)))
    return response(200, yard.model_dump())


@handler
def delete(event, context):
    yard_service.delete_yard(event["pathParameters"]["yardId"])
    return response(204)

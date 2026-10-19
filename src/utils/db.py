import os
from typing import Any

import boto3
from boto3.dynamodb.conditions import ConditionBase
from boto3.dynamodb.types import TypeSerializer

YARDS_TABLE = os.environ.get("YARDS_TABLE", "cuy-farm-api-yards")
YARD_NAMES_TABLE = os.environ.get("YARD_NAMES_TABLE", "cuy-farm-api-yard-names")
MOVEMENTS_TABLE = os.environ.get("MOVEMENTS_TABLE", "cuy-farm-api-movements")

_resource = None
_serializer = TypeSerializer()


def get_resource():
    global _resource
    if _resource is None:
        _resource = boto3.resource("dynamodb")
    return _resource


def get_table(table_name: str):
    return get_resource().Table(table_name)


def put_item(table_name: str, item: dict[str, Any], condition: ConditionBase | None = None) -> None:
    kwargs: dict[str, Any] = {"Item": item}
    if condition is not None:
        kwargs["ConditionExpression"] = condition
    get_table(table_name).put_item(**kwargs)


def get_item(table_name: str, key: dict[str, Any]) -> dict[str, Any] | None:
    return get_table(table_name).get_item(Key=key).get("Item")


def delete_item(table_name: str, key: dict[str, Any]) -> None:
    get_table(table_name).delete_item(Key=key)


def update_item(table_name: str, key: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    names = {f"#{k}": k for k in values}
    placeholders = {f":{k}": v for k, v in values.items()}
    expression = "SET " + ", ".join(f"#{k} = :{k}" for k in values)
    response = get_table(table_name).update_item(
        Key=key,
        UpdateExpression=expression,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=placeholders,
        ConditionExpression="attribute_exists(id)",
        ReturnValues="ALL_NEW",
    )
    return response["Attributes"]


def scan_items(table_name: str, filter_expression: ConditionBase | None = None) -> list[dict[str, Any]]:
    table = get_table(table_name)
    kwargs: dict[str, Any] = {}
    if filter_expression is not None:
        kwargs["FilterExpression"] = filter_expression

    items: list[dict[str, Any]] = []
    while True:
        response = table.scan(**kwargs)
        items.extend(response.get("Items", []))
        if "LastEvaluatedKey" not in response:
            return items
        kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]


def transact_write(operations: list[dict[str, Any]]) -> None:
    """Run low-level TransactWriteItems operations atomically across tables.

    Operations use the DynamoDB wire format, e.g.
    {"Put": {"TableName": ..., "Item": serialize(item)}}.
    """
    get_resource().meta.client.transact_write_items(TransactItems=operations)


def serialize(item: dict[str, Any]) -> dict[str, Any]:
    return {k: _serializer.serialize(v) for k, v in item.items()}

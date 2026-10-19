import json
from decimal import Decimal
from functools import wraps
from typing import Any, Callable

from botocore.exceptions import ClientError
from pydantic import ValidationError


class ApiError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class NotFoundError(ApiError):
    def __init__(self, message: str = "Not found"):
        super().__init__(404, message)


class ConflictError(ApiError):
    def __init__(self, message: str):
        super().__init__(409, message)


def _default(value: Any):
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    raise TypeError(f"Cannot serialize {type(value)}")


def response(status_code: int, body: Any = None) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=_default) if body is not None else "",
    }


def parse_body(event: dict[str, Any]) -> dict[str, Any]:
    try:
        return json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        raise ApiError(400, "Request body must be valid JSON")


def handler(func: Callable[[dict, Any], dict]) -> Callable[[dict, Any], dict]:
    """Translate validation and service errors into HTTP responses."""

    @wraps(func)
    def wrapper(event, context):
        try:
            return func(event, context)
        except ValidationError as exc:
            return response(422, {"message": "Validation error", "errors": exc.errors(include_url=False, include_context=False)})
        except ApiError as exc:
            return response(exc.status_code, {"message": exc.message})
        except ClientError as exc:
            print(f"DynamoDB error: {exc}")
            return response(500, {"message": "Internal server error"})

    return wrapper

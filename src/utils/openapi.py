from typing import Any

from pydantic import BaseModel
from pydantic.json_schema import models_json_schema

from src.models import Movement, MovementCreate, Yard, YardCreate, YardUpdate

_MODELS: list[type[BaseModel]] = [Yard, YardCreate, YardUpdate, Movement, MovementCreate]


def _ref(model: type[BaseModel]) -> dict[str, str]:
    return {"$ref": f"#/components/schemas/{model.__name__}"}


def _json(schema: dict[str, Any]) -> dict[str, Any]:
    return {"application/json": {"schema": schema}}


def _body(model: type[BaseModel]) -> dict[str, Any]:
    return {"required": True, "content": _json(_ref(model))}


def _ok(description: str, schema: dict[str, Any]) -> dict[str, Any]:
    return {"description": description, "content": _json(schema)}


def _error(description: str) -> dict[str, Any]:
    return {"description": description, "content": _json({"$ref": "#/components/schemas/Error"})}


def _path_param(name: str) -> dict[str, Any]:
    return {"name": name, "in": "path", "required": True, "schema": {"type": "string"}}


_VALIDATION_ERROR = _error("Validation error")
_NOT_FOUND = _error("Not found")


def build_spec() -> dict[str, Any]:
    _, defs = models_json_schema(
        # Response models use serialization mode so computed fields (Yard.total) are included.
        [(m, "serialization" if m in (Yard, Movement) else "validation") for m in _MODELS],
        ref_template="#/components/schemas/{model}",
    )
    schemas = defs["$defs"]
    schemas["Error"] = {
        "type": "object",
        "properties": {"message": {"type": "string"}, "errors": {"type": "array", "items": {"type": "object"}}},
        "required": ["message"],
    }

    yard_id = _path_param("yardId")
    movement_id = _path_param("movementId")

    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Cuy Farm API",
            "version": "0.1.0",
            "description": "Manage cuy farm yards and the movements that adjust their totals.",
        },
        "tags": [{"name": "Yards"}, {"name": "Movements"}],
        "paths": {
            "/yards": {
                "get": {
                    "tags": ["Yards"],
                    "summary": "List yards",
                    "responses": {"200": _ok("Yards", {"type": "array", "items": _ref(Yard)})},
                },
                "post": {
                    "tags": ["Yards"],
                    "summary": "Create a yard",
                    "requestBody": _body(YardCreate),
                    "responses": {
                        "201": _ok("Created yard", _ref(Yard)),
                        "409": _error("Yard name already exists"),
                        "422": _VALIDATION_ERROR,
                    },
                },
            },
            "/yards/{yardId}": {
                "parameters": [yard_id],
                "get": {
                    "tags": ["Yards"],
                    "summary": "Get a yard",
                    "responses": {"200": _ok("Yard", _ref(Yard)), "404": _NOT_FOUND},
                },
                "patch": {
                    "tags": ["Yards"],
                    "summary": "Rename a yard",
                    "requestBody": _body(YardUpdate),
                    "responses": {
                        "200": _ok("Updated yard", _ref(Yard)),
                        "404": _NOT_FOUND,
                        "409": _error("Yard name already exists"),
                        "422": _VALIDATION_ERROR,
                    },
                },
                "delete": {
                    "tags": ["Yards"],
                    "summary": "Delete a yard",
                    "responses": {"204": {"description": "Deleted"}, "404": _NOT_FOUND},
                },
            },
            "/movements": {
                "get": {
                    "tags": ["Movements"],
                    "summary": "List movements",
                    "parameters": [
                        {
                            "name": "yardId",
                            "in": "query",
                            "required": False,
                            "description": "Only return movements involving this yard",
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": _ok("Movements", {"type": "array", "items": _ref(Movement)})},
                },
                "post": {
                    "tags": ["Movements"],
                    "summary": "Register a movement",
                    "description": (
                        "Adjusts yard totals transactionally. `notDefined` gender is counted as babies. "
                        "`define` moves `quantity` animals from `genderFrom` to `genderTo` (never `notDefined`), "
                        "either on the same yard or into `toYardId`."
                    ),
                    "requestBody": _body(MovementCreate),
                    "responses": {
                        "201": _ok("Created movement", _ref(Movement)),
                        "404": _NOT_FOUND,
                        "409": _error("Not enough animals in the yard"),
                        "422": _VALIDATION_ERROR,
                    },
                },
            },
            "/movements/{movementId}": {
                "parameters": [movement_id],
                "get": {
                    "tags": ["Movements"],
                    "summary": "Get a movement",
                    "responses": {"200": _ok("Movement", _ref(Movement)), "404": _NOT_FOUND},
                },
            },
        },
        "components": {"schemas": schemas},
    }

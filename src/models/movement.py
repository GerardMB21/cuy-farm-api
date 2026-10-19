from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class MovementType(StrEnum):
    ADD = "add"
    TRANSFER = "transfer"
    SOLD = "sold"
    DEAD = "dead"


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    NOT_DEFINED = "notDefined"


class MovementCreate(BaseModel):
    fromYardId: str
    toYardId: str | None = None
    type: MovementType
    gender: Gender
    quantity: int = Field(gt=0)
    price: int | None = Field(default=None, ge=0)
    reason: str | None = None

    @model_validator(mode="after")
    def check_destination(self):
        if self.type == MovementType.TRANSFER:
            if not self.toYardId:
                raise ValueError("toYardId is required for transfer movements")
            if self.toYardId == self.fromYardId:
                raise ValueError("toYardId must differ from fromYardId")
        return self


class Movement(MovementCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    createdAt: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

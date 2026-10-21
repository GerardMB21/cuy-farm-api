from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class MovementType(StrEnum):
    ADD = "add"
    TRANSFER = "transfer"
    SOLD = "sold"
    DEAD = "dead"
    DEFINE = "define"


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    NOT_DEFINED = "notDefined"


class MovementCreate(BaseModel):
    fromYardId: str
    toYardId: str | None = None
    type: MovementType
    genderFrom: Gender
    genderTo: Gender | None = None
    quantity: int = Field(gt=0)
    price: int | None = Field(default=None, ge=0)
    reason: str | None = None

    @model_validator(mode="after")
    def check_destination(self):
        if self.type == MovementType.TRANSFER and not self.toYardId:
            raise ValueError("toYardId is required for transfer movements")
        if self.type in (MovementType.TRANSFER, MovementType.DEFINE) and self.toYardId == self.fromYardId:
            raise ValueError("toYardId must differ from fromYardId; omit it to define on the same yard")
        return self

    @model_validator(mode="after")
    def check_gender_to(self):
        if self.type != MovementType.DEFINE:
            if self.genderTo is not None:
                raise ValueError("genderTo is only allowed for define movements")
            return self
        if self.genderTo is None:
            raise ValueError("genderTo is required for define movements")
        if self.genderTo == Gender.NOT_DEFINED:
            raise ValueError("genderTo cannot be notDefined")
        if self.genderTo == self.genderFrom:
            raise ValueError("genderTo must differ from genderFrom")
        return self


class Movement(MovementCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    createdAt: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_gender(cls, data):
        # Movements stored before genderFrom/genderTo used a single `gender` field.
        if isinstance(data, dict) and "gender" in data and "genderFrom" not in data:
            data = {**data, "genderFrom": data["gender"]}
            del data["gender"]
        return data

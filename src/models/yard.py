from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class Yard(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(min_length=1)
    initialMales: int | None = Field(default=None, ge=0)
    initialFemales: int | None = Field(default=None, ge=0)
    initialBabies: int | None = Field(default=None, ge=0)
    totalMales: int = Field(default=0, ge=0)
    totalFemales: int = Field(default=0, ge=0)
    totalBabies: int = Field(default=0, ge=0)


class YardCreate(BaseModel):
    name: str = Field(min_length=1)
    initialMales: int | None = Field(default=None, ge=0)
    initialFemales: int | None = Field(default=None, ge=0)
    initialBabies: int | None = Field(default=None, ge=0)


class YardUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)

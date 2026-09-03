from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClassCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=255)


class ClassUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    code: str | None = Field(default=None, min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=255)


class ClassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    description: str | None
    created_at: datetime
    updated_at: datetime

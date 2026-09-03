from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AcademicSessionCreate(BaseModel):
    name: str = Field(min_length=4, max_length=20)
    is_current: bool = False


class AcademicSessionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=4, max_length=20)
    is_current: bool | None = None


class AcademicSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_current: bool
    created_at: datetime

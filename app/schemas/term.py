from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TermCreate(BaseModel):
    academic_session_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=20)


class TermUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=20,
    )


class TermResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    academic_session_id: int
    name: str
    created_at: datetime

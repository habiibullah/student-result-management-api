from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class TermCreate(BaseModel):
    school_days: int | None = Field(default=None, gt=0)
    academic_session_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=20)


    closing_date: date | None = None
    next_term_resumption_date: date | None = None


class TermUpdate(BaseModel):
    school_days: int | None = Field(default=None, gt=0)
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=20,
    )

    closing_date: date | None = None
    next_term_resumption_date: date | None = None


class TermResponse(BaseModel):
    school_days: int | None
    model_config = ConfigDict(from_attributes=True)

    id: int
    academic_session_id: int
    name: str
    created_at: datetime


    closing_date: date | None
    next_term_resumption_date: date | None

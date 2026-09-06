from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TermReportCommentCreate(BaseModel):
    student_id: int = Field(gt=0)
    academic_session_id: int = Field(gt=0)
    term_id: int = Field(gt=0)

    teacher_comment: str | None = Field(
        default=None,
        max_length=1000,
    )

    principal_comment: str | None = Field(
        default=None,
        max_length=1000,
    )


class TermReportCommentUpdate(BaseModel):
    teacher_comment: str | None = Field(
        default=None,
        max_length=1000,
    )

    principal_comment: str | None = Field(
        default=None,
        max_length=1000,
    )


class TermReportCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    academic_session_id: int
    term_id: int

    teacher_comment: str | None
    principal_comment: str | None

    created_at: datetime
    updated_at: datetime

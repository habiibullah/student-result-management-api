from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StudentBehaviouralAssessmentCreate(BaseModel):
    student_id: int = Field(gt=0)
    academic_session_id: int = Field(gt=0)
    term_id: int = Field(gt=0)

    punctuality: int | None = Field(default=None, ge=1, le=5)
    neatness: int | None = Field(default=None, ge=1, le=5)
    honesty: int | None = Field(default=None, ge=1, le=5)
    politeness: int | None = Field(default=None, ge=1, le=5)
    attentiveness: int | None = Field(default=None, ge=1, le=5)
    cooperation: int | None = Field(default=None, ge=1, le=5)


class StudentBehaviouralAssessmentUpdate(BaseModel):
    punctuality: int | None = Field(default=None, ge=1, le=5)
    neatness: int | None = Field(default=None, ge=1, le=5)
    honesty: int | None = Field(default=None, ge=1, le=5)
    politeness: int | None = Field(default=None, ge=1, le=5)
    attentiveness: int | None = Field(default=None, ge=1, le=5)
    cooperation: int | None = Field(default=None, ge=1, le=5)


class StudentBehaviouralAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    academic_session_id: int
    term_id: int

    punctuality: int | None
    neatness: int | None
    honesty: int | None
    politeness: int | None
    attentiveness: int | None
    cooperation: int | None

    created_at: datetime
    updated_at: datetime

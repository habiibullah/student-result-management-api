from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EnrollmentCreate(BaseModel):
    student_id: int = Field(gt=0)
    class_id: int = Field(gt=0)
    academic_session_id: int = Field(gt=0)


class EnrollmentUpdate(BaseModel):
    class_id: int | None = Field(default=None, gt=0)
    academic_session_id: int | None = Field(default=None, gt=0)


class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    class_id: int
    academic_session_id: int
    created_at: datetime

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TeachingAssignmentCreate(BaseModel):
    teacher_id: int = Field(gt=0)
    subject_id: int = Field(gt=0)
    class_id: int = Field(gt=0)
    academic_session_id: int = Field(gt=0)


class TeachingAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    teacher_id: int
    subject_id: int
    class_id: int
    academic_session_id: int
    created_at: datetime

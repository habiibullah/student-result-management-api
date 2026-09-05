from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StudentScoreCreate(BaseModel):
    student_id: int = Field(gt=0)
    assessment_id: int = Field(gt=0)
    score: float = Field(ge=0)


class StudentScoreUpdate(BaseModel):
    score: float = Field(ge=0)


class StudentScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    assessment_id: int
    score: float
    created_at: datetime
    updated_at: datetime

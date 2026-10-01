from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StudentScoreCreate(BaseModel):
    student_id: int = Field(gt=0)
    assessment_id: int = Field(gt=0)
    score: float = Field(ge=0)


class StudentScoreUpdate(BaseModel):
    score: float = Field(ge=0)


class StudentScoreBulkItem(BaseModel):
    student_id: int = Field(gt=0)
    score: float = Field(ge=0)


class StudentScoreBulkCreate(BaseModel):
    assessment_id: int = Field(gt=0)
    scores: list[StudentScoreBulkItem] = Field(min_length=1)


class AssessmentScoreProgressResponse(BaseModel):
    assessment_id: int
    total_students: int
    scores_entered: int
    scores_remaining: int
    is_complete: bool


class StudentScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    assessment_id: int
    score: float
    created_at: datetime
    updated_at: datetime

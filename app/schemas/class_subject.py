from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClassSubjectCreate(BaseModel):
    class_id: int = Field(gt=0)
    subject_id: int = Field(gt=0)
    academic_session_id: int = Field(gt=0)


class ClassSubjectBulkCreate(BaseModel):
    class_id: int = Field(gt=0)
    academic_session_id: int = Field(gt=0)
    subject_ids: list[int] = Field(min_length=1)

    @field_validator("subject_ids")
    @classmethod
    def validate_subject_ids(cls, value: list[int]) -> list[int]:
        if any(subject_id <= 0 for subject_id in value):
            raise ValueError("All subject IDs must be greater than zero")

        if len(value) != len(set(value)):
            raise ValueError("Subject IDs must be unique")

        return value


class ClassSubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    class_id: int
    subject_id: int
    academic_session_id: int
    created_at: datetime

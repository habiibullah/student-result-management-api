from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AssessmentCreate(BaseModel):
    class_id: int = Field(gt=0)
    subject_id: int = Field(gt=0)
    academic_session_id: int = Field(gt=0)
    term_id: int = Field(gt=0)

    assessment_type: str
    sequence: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=50)
    max_score: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_assessment(self):
        assessment_type = self.assessment_type.upper()

        if assessment_type == "CA":
            if self.sequence not in (1, 2, 3):
                raise ValueError("CA sequence must be 1, 2, or 3")

            if self.max_score != 10:
                raise ValueError("CA assessments must have a maximum score of 10")

        elif assessment_type == "EXAM":
            if self.sequence != 1:
                raise ValueError("Examination sequence must be 1")

            if self.max_score != 70:
                raise ValueError(
                    "Examination must have a maximum score of 70"
                )

        else:
            raise ValueError("assessment_type must be CA or EXAM")

        self.assessment_type = assessment_type

        return self


class AssessmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=50)


class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    class_id: int
    subject_id: int
    academic_session_id: int
    term_id: int
    assessment_type: str
    sequence: int
    name: str
    max_score: int
    created_at: datetime
    updated_at: datetime

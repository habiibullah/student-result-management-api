from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class PerformanceCommentBandCreate(BaseModel):
    minimum_average: float = Field(
        ge=0,
        le=100,
    )

    maximum_average: float = Field(
        ge=0,
        le=100,
    )

    teacher_comment: str = Field(
        min_length=1,
        max_length=1000,
    )

    principal_comment: str = Field(
        min_length=1,
        max_length=1000,
    )

    @model_validator(mode="after")
    def validate_average_range(self):
        if self.minimum_average > self.maximum_average:
            raise ValueError(
                "minimum_average cannot be greater "
                "than maximum_average"
            )

        return self


class PerformanceCommentBandUpdate(BaseModel):
    minimum_average: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    maximum_average: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    teacher_comment: str | None = Field(
        default=None,
        min_length=1,
        max_length=1000,
    )

    principal_comment: str | None = Field(
        default=None,
        min_length=1,
        max_length=1000,
    )


class PerformanceCommentBandResponse(BaseModel):
    id: int
    school_id: int

    minimum_average: float
    maximum_average: float

    teacher_comment: str
    principal_comment: str

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }

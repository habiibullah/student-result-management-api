from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class GradingScaleCreate(BaseModel):
    grade: str = Field(
        min_length=1,
        max_length=10,
    )

    minimum_score: float = Field(
        ge=0,
        le=100,
    )

    maximum_score: float = Field(
        ge=0,
        le=100,
    )

    remark: str | None = Field(
        default=None,
        max_length=255,
    )

    @model_validator(mode="after")
    def validate_score_range(self):
        if self.minimum_score > self.maximum_score:
            raise ValueError(
                "minimum_score cannot be greater than maximum_score"
            )

        return self


class GradingScaleUpdate(BaseModel):
    grade: str | None = Field(
        default=None,
        min_length=1,
        max_length=10,
    )

    minimum_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    maximum_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    remark: str | None = Field(
        default=None,
        max_length=255,
    )


class GradingScaleResponse(BaseModel):
    id: int
    school_id: int
    grade: str
    minimum_score: float
    maximum_score: float
    remark: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }

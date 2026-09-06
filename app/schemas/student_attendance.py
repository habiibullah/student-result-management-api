from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StudentAttendanceCreate(BaseModel):
    student_id: int = Field(gt=0)
    academic_session_id: int = Field(gt=0)
    term_id: int = Field(gt=0)

    school_days: int = Field(gt=0)
    days_present: int = Field(ge=0)
    days_absent: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_attendance(self):
        if self.days_present > self.school_days:
            raise ValueError(
                "Days present cannot exceed school days"
            )

        if self.days_absent > self.school_days:
            raise ValueError(
                "Days absent cannot exceed school days"
            )

        if self.days_present + self.days_absent != self.school_days:
            raise ValueError(
                "Days present plus days absent must equal school days"
            )

        return self


class StudentAttendanceUpdate(BaseModel):
    school_days: int | None = Field(default=None, gt=0)
    days_present: int | None = Field(default=None, ge=0)
    days_absent: int | None = Field(default=None, ge=0)


class StudentAttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    academic_session_id: int
    term_id: int

    school_days: int
    days_present: int
    days_absent: int

    created_at: datetime
    updated_at: datetime

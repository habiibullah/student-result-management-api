from datetime import datetime

from pydantic import BaseModel, Field


class ReportSettingsCreate(BaseModel):
    report_title: str = Field(
        default="Student Report Sheet",
        min_length=1,
        max_length=255,
    )

    show_class_position: bool = True
    show_class_size: bool = True
    show_attendance: bool = True
    show_teacher_comment: bool = True
    show_principal_comment: bool = True
    show_school_motto: bool = True
    show_school_logo: bool = True
    show_grading_remarks: bool = True

    principal_designation: str = Field(
        default="Principal",
        min_length=1,
        max_length=100,
    )


class ReportSettingsUpdate(BaseModel):
    report_title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    show_class_position: bool | None = None
    show_class_size: bool | None = None
    show_attendance: bool | None = None
    show_teacher_comment: bool | None = None
    show_principal_comment: bool | None = None
    show_school_motto: bool | None = None
    show_school_logo: bool | None = None
    show_grading_remarks: bool | None = None

    principal_designation: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )


class ReportSettingsResponse(BaseModel):
    id: int
    school_id: int

    report_title: str
    show_class_position: bool
    show_class_size: bool
    show_attendance: bool
    show_teacher_comment: bool
    show_principal_comment: bool
    show_school_motto: bool
    show_school_logo: bool
    show_grading_remarks: bool
    principal_designation: str

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }

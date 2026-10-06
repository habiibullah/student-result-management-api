from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class StudentCreate(BaseModel):
    admission_number: str = Field(
        min_length=2,
        max_length=50,
    )
    first_name: str = Field(
        min_length=2,
        max_length=100,
    )
    last_name: str = Field(
        min_length=2,
        max_length=100,
    )
    date_of_birth: date | None = None
    gender: str | None = Field(
        default=None,
        max_length=20,
    )


class StudentUpdate(BaseModel):
    admission_number: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
    )
    first_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    last_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    date_of_birth: date | None = None
    gender: str | None = Field(
        default=None,
        max_length=20,
    )


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    school_id: int
    admission_number: str
    first_name: str
    last_name: str
    date_of_birth: date | None
    gender: str | None
    has_profile_photo: bool = False
    created_at: datetime

class ClassTeacherStudentRegistrationItem(StudentCreate):
    pass


class ClassTeacherBulkRegistrationRequest(BaseModel):
    class_id: int = Field(gt=0)
    academic_session_id: int = Field(gt=0)
    students: list[ClassTeacherStudentRegistrationItem] = Field(
        min_length=1,
        max_length=200,
    )


class ClassTeacherRegistrationSuccess(BaseModel):
    row: int
    student: StudentResponse
    enrollment_id: int


class ClassTeacherRegistrationError(BaseModel):
    row: int
    admission_number: str
    detail: str


class ClassTeacherBulkRegistrationResponse(BaseModel):
    submitted: int
    created: int
    rejected: int
    successes: list[ClassTeacherRegistrationSuccess]
    errors: list[ClassTeacherRegistrationError]
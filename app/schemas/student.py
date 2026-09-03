from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StudentCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    admission_number: str = Field(min_length=2, max_length=50)
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=20)


class StudentUpdate(BaseModel):
    email: EmailStr | None = None
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
    is_active: bool | None = None


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    admission_number: str
    first_name: str
    last_name: str
    date_of_birth: date | None
    gender: str | None
    created_at: datetime

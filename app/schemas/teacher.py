from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TeacherCreate(BaseModel):
    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    employee_number: str = Field(
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


class TeacherUpdate(BaseModel):
    email: EmailStr | None = None

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

    employee_number: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
    )

    is_active: bool | None = None


class TeacherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    employee_number: str
    first_name: str
    last_name: str
    created_at: datetime

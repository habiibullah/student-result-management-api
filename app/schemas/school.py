from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SchoolRegistrationRequest(BaseModel):
    school_name: str = Field(
        min_length=2,
        max_length=255,
    )

    school_slug: str = Field(
        min_length=2,
        max_length=150,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )

    school_email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None
    motto: str | None = Field(default=None, max_length=255)

    admin_email: EmailStr

    admin_password: str = Field(
        min_length=8,
        max_length=128,
    )


class SchoolRegistrationResponse(BaseModel):
    school_id: int
    school_name: str
    school_slug: str
    school_email: EmailStr | None
    admin_user_id: int
    admin_email: EmailStr
    role: str
    message: str


class SchoolUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
    )

    email: EmailStr | None = None

    phone: str | None = Field(
        default=None,
        max_length=50,
    )

    address: str | None = None

    motto: str | None = Field(
        default=None,
        max_length=255,
    )

    logo_url: str | None = Field(
        default=None,
        max_length=500,
    )

class SchoolResponse(BaseModel):
    id: int
    name: str
    slug: str
    email: EmailStr | None
    phone: str | None
    address: str | None
    motto: str | None
    logo_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }

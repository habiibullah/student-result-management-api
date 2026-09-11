from datetime import datetime

from pydantic import BaseModel, Field


class PlatformAdminCreate(BaseModel):
    email: str
    password: str = Field(
        min_length=8,
        max_length=128,
    )


class SchoolAdminCreate(BaseModel):
    email: str
    password: str = Field(
        min_length=8,
        max_length=128,
    )

    # Required when a platform admin creates the account.
    # School admins are automatically restricted to their own school.
    school_id: int | None = None


class AdminUserResponse(BaseModel):
    id: int
    email: str
    role: str
    account_type: str
    school_id: int | None
    is_active: bool
    created_at: datetime

class AdminStatusUpdate(BaseModel):
    is_active: bool

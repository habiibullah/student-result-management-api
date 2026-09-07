from datetime import datetime

from pydantic import BaseModel, Field


class SubscriptionCreate(BaseModel):
    subscription_plan_id: int = Field(gt=0)
    academic_session_id: int = Field(gt=0)
    term_id: int = Field(gt=0)


class SubscriptionStatusUpdate(BaseModel):
    status: str


class SubscriptionResponse(BaseModel):
    id: int
    school_id: int
    subscription_plan_id: int
    academic_session_id: int
    term_id: int
    status: str
    activated_at: datetime | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }

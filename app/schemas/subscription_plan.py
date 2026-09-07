from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class SubscriptionPlanCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    description: str | None = None

    price_per_term: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    max_students: int | None = Field(
        default=None,
        gt=0,
    )

    is_active: bool = True


class SubscriptionPlanUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    description: str | None = None

    price_per_term: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    max_students: int | None = Field(
        default=None,
        gt=0,
    )

    is_active: bool | None = None


class SubscriptionPlanResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price_per_term: Decimal
    max_students: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PaymentInitializeRequest(BaseModel):
    subscription_id: int


class PaymentVerifyRequest(BaseModel):
    transaction_id: str


class PaymentVerifyResponse(BaseModel):
    payment_id: int
    subscription_id: int
    flutterwave_transaction_id: str
    payment_status: str
    subscription_status: str
    verified_at: datetime

class PaymentInitializeResponse(BaseModel):
    payment_id: int
    subscription_id: int
    tx_ref: str
    amount: Decimal
    currency: str
    status: str
    payment_link: str


class PaymentTransactionResponse(BaseModel):
    id: int
    school_id: int
    subscription_id: int
    tx_ref: str
    flutterwave_transaction_id: str | None
    amount: Decimal
    currency: str
    status: str
    payment_provider: str
    payment_link: str | None
    verified_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )

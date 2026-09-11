from typing import Any

import httpx

from app.core.config import settings


FLUTTERWAVE_BASE_URL = "https://api.flutterwave.com/v3"


class FlutterwaveServiceError(Exception):
    pass


def _get_headers() -> dict[str, str]:
    if not settings.flutterwave_secret_key:
        raise FlutterwaveServiceError(
            "Flutterwave secret key is not configured"
        )

    return {
        "Authorization": (
            f"Bearer {settings.flutterwave_secret_key}"
        ),
        "Content-Type": "application/json",
    }


def initialize_payment(
    *,
    tx_ref: str,
    amount: str,
    currency: str,
    customer_email: str,
    customer_name: str,
    customer_phone: str | None = None,
    subscription_id: int,
) -> dict[str, Any]:
    if not settings.flutterwave_redirect_url:
        raise FlutterwaveServiceError(
            "Flutterwave redirect URL is not configured"
        )

    customer: dict[str, str] = {
        "email": customer_email,
        "name": customer_name,
    }

    if customer_phone:
        customer["phonenumber"] = customer_phone

    payload = {
        "tx_ref": tx_ref,
        "amount": amount,
        "currency": currency,
        "redirect_url": settings.flutterwave_redirect_url,
        "customer": customer,
        "customizations": {
            "title": "School Subscription Payment",
            "description": "Termly school subscription",
        },
        "meta": {
            "subscription_id": subscription_id,
        },
    }

    try:
        response = httpx.post(
            f"{FLUTTERWAVE_BASE_URL}/payments",
            headers=_get_headers(),
            json=payload,
            timeout=30.0,
        )
    except httpx.RequestError as exc:
        raise FlutterwaveServiceError(
            "Could not connect to Flutterwave"
        ) from exc

    if response.status_code >= 400:
        raise FlutterwaveServiceError(
            "Flutterwave payment initialization failed"
        )

    try:
        response_data = response.json()
    except ValueError as exc:
        raise FlutterwaveServiceError(
            "Invalid response received from Flutterwave"
        ) from exc

    payment_link = (
        response_data.get("data", {}).get("link")
    )

    if (
        response_data.get("status") != "success"
        or not payment_link
    ):
        raise FlutterwaveServiceError(
            "Flutterwave did not return a payment link"
        )

    return response_data


def verify_transaction(
    transaction_id: str,
) -> dict[str, Any]:
    try:
        response = httpx.get(
            (
                f"{FLUTTERWAVE_BASE_URL}/transactions/"
                f"{transaction_id}/verify"
            ),
            headers=_get_headers(),
            timeout=30.0,
        )
    except httpx.RequestError as exc:
        raise FlutterwaveServiceError(
            "Could not connect to Flutterwave"
        ) from exc

    if response.status_code >= 400:
        raise FlutterwaveServiceError(
            "Flutterwave transaction verification failed"
        )

    try:
        response_data = response.json()
    except ValueError as exc:
        raise FlutterwaveServiceError(
            "Invalid response received from Flutterwave"
        ) from exc

    if response_data.get("status") != "success":
        raise FlutterwaveServiceError(
            "Flutterwave could not verify the transaction"
        )

    return response_data

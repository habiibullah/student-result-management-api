from unittest.mock import Mock

import httpx
import pytest

from app.services import flutterwave_service


def test_verify_by_reference_success(monkeypatch):
    expected = {
        "status": "success",
        "data": {
            "id": 123456,
            "tx_ref": "acadivio-test-001",
            "status": "successful",
        },
    }

    def fake_get(url, **kwargs):
        assert url.endswith(
            "/transactions/verify_by_reference"
        )
        assert kwargs["params"] == {
            "tx_ref": "acadivio-test-001"
        }
        return Mock(
            status_code=200,
            json=lambda: expected,
        )

    monkeypatch.setattr(
        flutterwave_service,
        "_get_headers",
        lambda: {"Authorization": "Bearer test-key"},
    )
    monkeypatch.setattr(httpx, "get", fake_get)

    result = (
        flutterwave_service.verify_transaction_by_reference(
            "acadivio-test-001"
        )
    )

    assert result == expected


def test_verify_by_reference_rejects_empty_reference():
    with pytest.raises(
        flutterwave_service.FlutterwaveServiceError,
        match="Transaction reference is required",
    ):
        flutterwave_service.verify_transaction_by_reference("")


def test_verify_by_reference_handles_api_error(monkeypatch):
    monkeypatch.setattr(
        flutterwave_service,
        "_get_headers",
        lambda: {"Authorization": "Bearer test-key"},
    )
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: Mock(status_code=404),
    )

    with pytest.raises(
        flutterwave_service.FlutterwaveServiceError,
        match="reference lookup failed",
    ):
        flutterwave_service.verify_transaction_by_reference(
            "acadivio-test-001"
        )


def test_verify_by_reference_handles_connection_error(
    monkeypatch,
):
    def fake_get(*args, **kwargs):
        raise httpx.ConnectError(
            "Connection failed"
        )

    monkeypatch.setattr(
        flutterwave_service,
        "_get_headers",
        lambda: {"Authorization": "Bearer test-key"},
    )
    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(
        flutterwave_service.FlutterwaveServiceError,
        match="Could not connect to Flutterwave",
    ):
        flutterwave_service.verify_transaction_by_reference(
            "acadivio-test-001"
        )


def test_verify_by_reference_rejects_unsuccessful_response(
    monkeypatch,
):
    monkeypatch.setattr(
        flutterwave_service,
        "_get_headers",
        lambda: {"Authorization": "Bearer test-key"},
    )
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: Mock(
            status_code=200,
            json=lambda: {"status": "error"},
        ),
    )

    with pytest.raises(
        flutterwave_service.FlutterwaveServiceError,
        match="could not verify",
    ):
        flutterwave_service.verify_transaction_by_reference(
            "acadivio-test-001"
        )
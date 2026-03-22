"""Black-box tests for the QuickCart API."""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterable

import pytest
import requests


BASE_URL = os.getenv("QUICKCART_BASE_URL")
ROLL_NUMBER = os.getenv("QUICKCART_ROLL_NUMBER", "2024101115")
USER_ID = os.getenv("QUICKCART_USER_ID", "1")


def admin_headers() -> dict[str, str]:
    """Return headers for admin-style calls."""
    return {"X-Roll-Number": ROLL_NUMBER}


def user_headers() -> dict[str, str]:
    """Return headers for user-scoped calls."""
    return {"X-Roll-Number": ROLL_NUMBER, "X-User-ID": USER_ID}


def request_json(method: str, path: str, **kwargs: object) -> requests.Response:
    """Issue an HTTP request against QuickCart."""
    if not BASE_URL:
        pytest.skip("Set QUICKCART_BASE_URL to run QuickCart API tests")
    return requests.request(method, f"{BASE_URL}{path}", timeout=10, **kwargs)


def parse_json(response: requests.Response) -> object:
    """Parse and return a JSON payload."""
    return response.json()


def assert_json_object(response: requests.Response) -> dict[str, object]:
    """Assert that the response body is a JSON object."""
    payload = parse_json(response)
    assert isinstance(payload, dict)
    return payload


def assert_json_list(response: requests.Response) -> list[object]:
    """Assert that the response body is a JSON list."""
    payload = parse_json(response)
    assert isinstance(payload, list)
    return payload


def assert_contains_keys(payload: dict[str, object], keys: Iterable[str]) -> None:
    """Assert that a JSON object contains a minimal key set."""
    for key in keys:
        assert key in payload


def extract_nested_object(payload: dict[str, object], candidates: list[str]) -> dict[str, object]:
    """Return a nested object if present, else the payload itself."""
    for candidate in candidates:
        value = payload.get(candidate)
        if isinstance(value, dict):
            return value
    return payload


def test_missing_roll_number_header_returns_401() -> None:
    if not BASE_URL:
        pytest.skip("Set QUICKCART_BASE_URL to run QuickCart API tests")
    response = requests.get(f"{BASE_URL}/api/v1/admin/users", timeout=10)
    assert response.status_code == 401


def test_invalid_roll_number_header_returns_400() -> None:
    response = request_json(
        "GET",
        "/api/v1/admin/users",
        headers={"X-Roll-Number": "abc"},
    )
    assert response.status_code == 400


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/admin/users",
        "/api/v1/admin/carts",
        "/api/v1/admin/orders",
        "/api/v1/admin/products",
        "/api/v1/admin/coupons",
        "/api/v1/admin/tickets",
        "/api/v1/admin/addresses",
    ],
)
def test_admin_collection_endpoints_return_json_lists(path: str) -> None:
    response = request_json("GET", path, headers=admin_headers())
    assert response.status_code == 200
    assert_json_list(response)


def test_admin_user_lookup_returns_json_object() -> None:
    response = request_json("GET", "/api/v1/admin/users/1", headers=admin_headers())
    assert response.status_code == 200
    payload = assert_json_object(response)
    assert "user_id" in payload or "id" in payload


def test_profile_requires_user_id_header() -> None:
    response = request_json("GET", "/api/v1/profile", headers=admin_headers())
    assert response.status_code == 400


def test_profile_rejects_non_integer_user_header() -> None:
    response = request_json(
        "GET",
        "/api/v1/profile",
        headers={"X-Roll-Number": ROLL_NUMBER, "X-User-ID": "abc"},
    )
    assert response.status_code == 400


def test_profile_returns_json_object_for_valid_user() -> None:
    response = request_json("GET", "/api/v1/profile", headers=user_headers())
    assert response.status_code == 200
    payload = assert_json_object(response)
    assert "name" in payload or "user_id" in payload or "phone" in payload


def test_profile_update_rejects_short_name() -> None:
    response = request_json(
        "PUT",
        "/api/v1/profile",
        headers=user_headers(),
        json={"name": "A", "phone": "9876543210"},
    )
    assert response.status_code == 400


def test_profile_update_rejects_invalid_phone_length() -> None:
    response = request_json(
        "PUT",
        "/api/v1/profile",
        headers=user_headers(),
        json={"name": "Valid User", "phone": "12345"},
    )
    assert response.status_code == 400


def test_addresses_list_returns_json_list() -> None:
    response = request_json("GET", "/api/v1/addresses", headers=user_headers())
    assert response.status_code == 200
    assert_json_list(response)


@pytest.mark.parametrize(
    "body",
    [
        {
            "label": "HOME",
            "street": "12345 Sample Street",
            "city": "Hyderabad",
            "pincode": "500001",
            "is_default": False,
        },
        {
            "label": "OFFICE",
            "street": "98765 Office Road",
            "city": "Mumbai",
            "pincode": "400001",
            "is_default": True,
        },
    ],
)
def test_create_address_returns_expected_json_shape(body: dict[str, object]) -> None:
    response = request_json(
        "POST",
        "/api/v1/addresses",
        headers=user_headers(),
        json=body,
    )
    assert response.status_code in {200, 201}
    payload = assert_json_object(response)
    address = extract_nested_object(payload, ["address", "data"])
    assert_contains_keys(address, ["label", "street", "city", "pincode"])


@pytest.mark.parametrize(
    "body",
    [
        {
            "label": "HOSTEL",
            "street": "12345 Sample Street",
            "city": "Hyderabad",
            "pincode": "500001",
            "is_default": False,
        },
        {
            "label": "HOME",
            "street": "1234",
            "city": "Hyderabad",
            "pincode": "500001",
            "is_default": False,
        },
        {
            "label": "HOME",
            "street": "12345 Sample Street",
            "city": "H",
            "pincode": "500001",
            "is_default": False,
        },
        {
            "label": "HOME",
            "street": "12345 Sample Street",
            "city": "Hyderabad",
            "pincode": "50001",
            "is_default": False,
        },
    ],
)
def test_create_address_rejects_invalid_fields(body: dict[str, object]) -> None:
    response = request_json(
        "POST",
        "/api/v1/addresses",
        headers=user_headers(),
        json=body,
    )
    assert response.status_code == 400


def test_delete_nonexistent_address_returns_404() -> None:
    response = request_json(
        "DELETE",
        "/api/v1/addresses/999999",
        headers=user_headers(),
    )
    assert response.status_code == 404


def test_products_endpoint_returns_json_list() -> None:
    response = request_json("GET", "/api/v1/products", headers=user_headers())
    assert response.status_code == 200
    assert_json_list(response)


def test_single_product_lookup_for_invalid_id_returns_404() -> None:
    response = request_json("GET", "/api/v1/products/999999", headers=user_headers())
    assert response.status_code == 404


def test_cart_endpoint_returns_json_object() -> None:
    response = request_json("GET", "/api/v1/cart", headers=user_headers())
    assert response.status_code == 200
    assert_json_object(response)


@pytest.mark.parametrize("quantity", [0, -1])
def test_cart_add_rejects_non_positive_quantity(quantity: int) -> None:
    response = request_json(
        "POST",
        "/api/v1/cart/add",
        headers=user_headers(),
        json={"product_id": 1, "quantity": quantity},
    )
    assert response.status_code == 400


def test_cart_add_rejects_unknown_product() -> None:
    response = request_json(
        "POST",
        "/api/v1/cart/add",
        headers=user_headers(),
        json={"product_id": 999999, "quantity": 1},
    )
    assert response.status_code == 404


def test_cart_update_rejects_non_positive_quantity() -> None:
    response = request_json(
        "POST",
        "/api/v1/cart/update",
        headers=user_headers(),
        json={"product_id": 1, "quantity": 0},
    )
    assert response.status_code == 400


def test_cart_remove_rejects_unknown_product() -> None:
    response = request_json(
        "POST",
        "/api/v1/cart/remove",
        headers=user_headers(),
        json={"product_id": 999999},
    )
    assert response.status_code == 404


def test_wallet_endpoint_returns_json_object() -> None:
    response = request_json("GET", "/api/v1/wallet", headers=user_headers())
    assert response.status_code == 200
    payload = assert_json_object(response)
    assert "balance" in payload or "wallet_balance" in payload


@pytest.mark.parametrize("amount", [0, 100001])
def test_wallet_add_rejects_out_of_range_amount(amount: int) -> None:
    response = request_json(
        "POST",
        "/api/v1/wallet/add",
        headers=user_headers(),
        json={"amount": amount},
    )
    assert response.status_code == 400


@pytest.mark.parametrize("amount", [0, 999999])
def test_wallet_pay_rejects_invalid_amounts(amount: int) -> None:
    response = request_json(
        "POST",
        "/api/v1/wallet/pay",
        headers=user_headers(),
        json={"amount": amount},
    )
    assert response.status_code == 400


def test_loyalty_endpoint_returns_json_object() -> None:
    response = request_json("GET", "/api/v1/loyalty", headers=user_headers())
    assert response.status_code == 200
    assert_json_object(response)


def test_loyalty_redeem_rejects_zero_points() -> None:
    response = request_json(
        "POST",
        "/api/v1/loyalty/redeem",
        headers=user_headers(),
        json={"points": 0},
    )
    assert response.status_code == 400


def test_checkout_rejects_unknown_payment_method() -> None:
    response = request_json(
        "POST",
        "/api/v1/checkout",
        headers=user_headers(),
        json={"payment_method": "CHEQUE"},
    )
    assert response.status_code == 400


def test_checkout_rejects_missing_payment_method() -> None:
    response = request_json(
        "POST",
        "/api/v1/checkout",
        headers=user_headers(),
        json={},
    )
    assert response.status_code == 400


def test_orders_endpoint_returns_json_list() -> None:
    response = request_json("GET", "/api/v1/orders", headers=user_headers())
    assert response.status_code == 200
    assert_json_list(response)


def test_cancel_nonexistent_order_returns_404() -> None:
    response = request_json(
        "POST",
        "/api/v1/orders/999999/cancel",
        headers=user_headers(),
    )
    assert response.status_code == 404


def test_reviews_endpoint_returns_collection_shape() -> None:
    response = request_json("GET", "/api/v1/products/1/reviews", headers=user_headers())
    assert response.status_code == 200
    payload = parse_json(response)
    assert isinstance(payload, (list, dict))


def test_review_rejects_out_of_range_rating() -> None:
    response = request_json(
        "POST",
        "/api/v1/products/1/reviews",
        headers=user_headers(),
        json={"rating": 6, "comment": "Too high"},
    )
    assert response.status_code == 400


def test_review_rejects_empty_comment() -> None:
    response = request_json(
        "POST",
        "/api/v1/products/1/reviews",
        headers=user_headers(),
        json={"rating": 4, "comment": ""},
    )
    assert response.status_code == 400


def test_support_tickets_list_returns_json_list() -> None:
    response = request_json("GET", "/api/v1/support/tickets", headers=user_headers())
    assert response.status_code == 200
    assert_json_list(response)


@pytest.mark.parametrize(
    "body",
    [
        {"subject": "Hey", "message": "Need help"},
        {"subject": "Valid subject", "message": ""},
    ],
)
def test_support_ticket_creation_rejects_invalid_fields(body: dict[str, str]) -> None:
    response = request_json(
        "POST",
        "/api/v1/support/ticket",
        headers=user_headers(),
        json=body,
    )
    assert response.status_code == 400


def test_support_ticket_creation_returns_json_object() -> None:
    subject = f"Ticket {uuid.uuid4().hex[:8]}"
    message = "Please check the order ETA and confirm the latest delivery status."
    response = request_json(
        "POST",
        "/api/v1/support/ticket",
        headers=user_headers(),
        json={"subject": subject, "message": message},
    )
    assert response.status_code in {200, 201}
    payload = assert_json_object(response)
    assert "message" in payload or "ticket_id" in payload or "status" in payload


def test_support_ticket_status_transition_rejects_skipping_directly_to_closed() -> None:
    subject = f"Escalation {uuid.uuid4().hex[:8]}"
    create_response = request_json(
        "POST",
        "/api/v1/support/ticket",
        headers=user_headers(),
        json={
            "subject": subject,
            "message": "Created to verify ticket state transition validation.",
        },
    )
    assert create_response.status_code in {200, 201}
    created_payload = assert_json_object(create_response)
    ticket_id = created_payload.get("ticket_id") or created_payload.get("id")
    assert isinstance(ticket_id, int)

    update_response = request_json(
        "PUT",
        f"/api/v1/support/tickets/{ticket_id}",
        headers=user_headers(),
        json={"status": "CLOSED"},
    )
    assert update_response.status_code == 400


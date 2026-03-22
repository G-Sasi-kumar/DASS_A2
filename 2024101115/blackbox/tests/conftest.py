"""Pytest configuration and fixtures for QuickCart API tests."""

import os
import pytest
import requests


@pytest.fixture(scope="session")
def base_url():
    """Provide the QuickCart base URL for API tests."""
    url = os.getenv("QUICKCART_BASE_URL", "http://localhost:5000")
    return url


@pytest.fixture(scope="session")
def roll_number():
    """Provide the roll number for test requests."""
    return os.getenv("QUICKCART_ROLL_NUMBER", "2024101115")


@pytest.fixture(scope="session")
def user_id():
    """Provide the user ID for test requests."""
    return os.getenv("QUICKCART_USER_ID", "1")


@pytest.fixture(scope="session")
def admin_headers(roll_number):
    """Return headers for admin-style API calls."""
    return {"X-Roll-Number": roll_number}


@pytest.fixture(scope="session")
def user_headers(roll_number, user_id):
    """Return headers for user-scoped API calls."""
    return {"X-Roll-Number": roll_number, "X-User-ID": user_id}


@pytest.fixture(scope="session")
def ensure_api_ready(base_url):
    """Ensure the QuickCart API is available before tests run."""
    try:
        response = requests.get(f"{base_url}/api/v1/admin/users", timeout=5)
        if response.status_code != 401:
            pytest.skip("API not available or headers not required")
    except requests.ConnectionError:
        pytest.skip("QuickCart API not running")

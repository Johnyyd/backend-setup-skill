import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user_and_login(client: AsyncClient):
    # Since the user doesn't exist, we expect a 401
    response = await client.post(
        "/api/v1/auth/login/access-token",
        data={"username": "test@example.com", "password": "testpassword"},
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/users/",
        json={"email": "test@example.com", "password": "testpassword", "full_name": "Test User"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "test@example.com"

    # Now login
    login_response = await client.post(
        "/api/v1/auth/login/access-token",
        data={"username": "test@example.com", "password": "testpassword"},
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()["data"]
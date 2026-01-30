from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_register_user():
    response = client.post(
        "/auth/register",
        json={
            "email": "testuser_auth@northbridge.com",
            "password": "test123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_login_user():
    response = client.post(
        "/auth/login",
        data={
            "username": "testuser_auth@northbridge.com",
            "password": "test123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

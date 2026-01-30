from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_token():
    response = client.post(
        "/auth/login",
        data={
            "username": "testuser_auth@northbridge.com",
            "password": "test123",
        },
    )
    return response.json()["access_token"]


def test_deposit():
    token = get_token()
    response = client.post(
        "/bank/deposit",
        json={"amount": 50},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["balance"] >= 50


def test_transfer_insufficient_funds():
    token = get_token()
    response = client.post(
        "/bank/transfer",
        json={
            "to_email": "nonexistent@northbridge.com",
            "amount": 9999,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code in (400, 404)

"""
Auth Tests Module.
Why this file exists: Validates the authentication flow (login, token generation, protected routes).
Why this design was chosen: Security is critical; automated tests ensure we don't accidentally expose protected endpoints during future refactoring.
"""
from app.schemas.user import UserCreate
from app.repositories import user as crud_user
from app.core.config import settings

def test_login_success(client, db):
    # Setup user
    email = "test@enterprise.com"
    password = "TestPassword123"
    user_in = UserCreate(email=email, password=password, is_active=True)
    user = crud_user.get_by_email(db, email=email)
    if not user:
        crud_user.create(db, obj_in=user_in)

    login_data = {
        "username": email,
        "password": password,
    }
    r = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert tokens["access_token"]

def test_login_fail_wrong_password(client, db):
    login_data = {
        "username": "test@enterprise.com",
        "password": "wrongpassword",
    }
    r = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    assert r.status_code == 400

def test_read_users_me(client, db):
    # Login first
    login_data = {
        "username": "test@enterprise.com",
        "password": "TestPassword123",
    }
    r = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = r.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    r = client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "test@enterprise.com"

def test_read_users_me_unauthorized(client):
    r = client.get(f"{settings.API_V1_STR}/auth/me")
    assert r.status_code == 401

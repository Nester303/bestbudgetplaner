"""
Testy endpointów autoryzacji.
"""
import pytest


class TestRegister:
    def test_register_success(self, client, db):
        resp = client.post("/api/auth/register", json={
            "email": "new@example.com",
            "password": "securepassword123",
            "first_name": "Jan",
            "last_name": "Kowalski"
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert "access_token" in data
        assert data["user"]["email"] == "new@example.com"
        assert "password_hash" not in data["user"]

    def test_register_duplicate_email(self, client, db):
        payload = {"email": "dup@example.com", "password": "password123"}
        client.post("/api/auth/register", json=payload)
        resp = client.post("/api/auth/register", json=payload)
        assert resp.status_code == 409

    def test_register_short_password(self, client, db):
        resp = client.post("/api/auth/register", json={
            "email": "short@example.com",
            "password": "abc"
        })
        assert resp.status_code == 400

    def test_register_missing_fields(self, client, db):
        resp = client.post("/api/auth/register", json={})
        assert resp.status_code == 400


class TestLogin:
    def test_login_success(self, client, db):
        client.post("/api/auth/register", json={
            "email": "login@example.com",
            "password": "mypassword123"
        })
        resp = client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "mypassword123"
        })
        assert resp.status_code == 200
        assert "access_token" in resp.get_json()

    def test_login_wrong_password(self, client, db):
        client.post("/api/auth/register", json={
            "email": "wrong@example.com",
            "password": "correctpassword"
        })
        resp = client.post("/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client, db):
        resp = client.post("/api/auth/login", json={
            "email": "nobody@example.com",
            "password": "anything"
        })
        assert resp.status_code == 401


class TestProtectedRoutes:
    def test_me_authenticated(self, client, auth_headers):
        resp = client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert "email" in resp.get_json()

    def test_me_unauthenticated(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_invalid_token(self, client):
        resp = client.get("/api/auth/me",
                          headers={"Authorization": "Bearer invalidtoken"})
        assert resp.status_code == 422


class TestHealthCheck:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"

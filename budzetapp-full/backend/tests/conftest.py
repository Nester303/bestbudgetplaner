"""
Pytest fixtures — współdzielone między wszystkimi testami.
"""
import pytest
from app import create_app
from app.extensions import db as _db
from app.models.user import User


@pytest.fixture(scope="session")
def app():
    """Jedna instancja aplikacji na całą sesję testową."""
    application = create_app("testing")
    application.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": application.config["DATABASE_URL"],
        "WTF_CSRF_ENABLED": False,
        "RATELIMIT_ENABLED": False,
    })

    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app):
    """Baza danych — każdy test dostaje czystą transakcję (rollback po teście)."""
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        _db.session.bind = connection

        yield _db

        _db.session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(app):
    """Test client Flask."""
    return app.test_client()


@pytest.fixture
def auth_headers(client, db):
    """Zaloguj testowego użytkownika i zwróć nagłówek Authorization."""
    # Stwórz użytkownika
    user = User(email="test@example.com")
    user.set_password("testpassword123")
    db.session.add(user)
    db.session.commit()

    # Zaloguj
    resp = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword123"
    })
    token = resp.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client, db):
    """Zaloguj admina i zwróć nagłówek Authorization."""
    admin = User(email="admin@example.com", role="admin")
    admin.set_password("adminpassword123")
    db.session.add(admin)
    db.session.commit()

    resp = client.post("/api/auth/login", json={
        "email": "admin@example.com",
        "password": "adminpassword123"
    })
    token = resp.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

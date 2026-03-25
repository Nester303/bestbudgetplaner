"""
Testy CRUD transakcji.
"""
from datetime import datetime


class TestTransactions:
    def _create(self, client, headers, data=None):
        payload = data or {
            "title":  "Czynsz",
            "amount": "1800.00",
            "type":   "expense",
            "date":   datetime.utcnow().isoformat(),
        }
        return client.post("/api/transactions/", json=payload, headers=headers)

    def test_create_transaction(self, client, auth_headers):
        resp = self._create(client, auth_headers)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["title"] == "Czynsz"
        assert data["type"] == "expense"

    def test_list_transactions(self, client, auth_headers):
        self._create(client, auth_headers)
        self._create(client, auth_headers, {
            "title": "Wynagrodzenie", "amount": "5000",
            "type": "income", "date": datetime.utcnow().isoformat()
        })
        resp = client.get("/api/transactions/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["total"] >= 2

    def test_filter_by_type(self, client, auth_headers):
        self._create(client, auth_headers)
        resp = client.get("/api/transactions/?type=expense", headers=auth_headers)
        items = resp.get_json()["items"]
        assert all(t["type"] == "expense" for t in items)

    def test_get_single(self, client, auth_headers):
        created = self._create(client, auth_headers).get_json()
        resp = client.get(f"/api/transactions/{created['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["id"] == created["id"]

    def test_update_transaction(self, client, auth_headers):
        created = self._create(client, auth_headers).get_json()
        resp = client.put(
            f"/api/transactions/{created['id']}",
            json={"title": "Zaktualizowany czynsz"},
            headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.get_json()["title"] == "Zaktualizowany czynsz"

    def test_delete_transaction(self, client, auth_headers):
        created = self._create(client, auth_headers).get_json()
        resp = client.delete(f"/api/transactions/{created['id']}", headers=auth_headers)
        assert resp.status_code == 200
        # Sprawdź że zniknął
        resp2 = client.get(f"/api/transactions/{created['id']}", headers=auth_headers)
        assert resp2.status_code == 404

    def test_cannot_access_other_user_transaction(self, client, auth_headers, db):
        """Użytkownik A nie może widzieć transakcji użytkownika B."""
        from app.models.user import User
        from app.models.transaction import Transaction
        from datetime import datetime, timezone

        # Stwórz drugiego usera i jego transakcję bezpośrednio w DB
        user_b = User(email="userb@example.com")
        user_b.set_password("password123")
        db.session.add(user_b)
        db.session.flush()

        tx = Transaction(
            user_id=user_b.id,
            title="Tajny wydatek",
            amount=999,
            type="expense",
            date=datetime.now(timezone.utc)
        )
        db.session.add(tx)
        db.session.commit()

        # Użytkownik A próbuje pobrać transakcję B
        resp = client.get(f"/api/transactions/{tx.id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_requires_auth(self, client):
        resp = client.get("/api/transactions/")
        assert resp.status_code == 401

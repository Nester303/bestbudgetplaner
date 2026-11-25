"""Testy endpointów budżetu i faktur."""
from datetime import datetime, timezone, date


class TestBudgetSummary:
    def _add_tx(self, client, headers, title, amount, tx_type):
        return client.post("/api/transactions/", json={
            "title": title, "amount": str(amount),
            "type": tx_type,
            "date": datetime.now(timezone.utc).isoformat(),
        }, headers=headers)

    def test_summary_empty(self, client, auth_headers):
        resp = client.get("/api/budget/summary?year=2020&month=1",
                          headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["income_total"]  == 0.0
        assert data["expense_total"] == 0.0
        assert data["balance"]       == 0.0

    def test_summary_with_transactions(self, client, auth_headers):
        self._add_tx(client, auth_headers, "Wynagrodzenie", 5000, "income")
        self._add_tx(client, auth_headers, "Czynsz",        1500, "expense")
        now = datetime.now(timezone.utc)
        resp = client.get(
            f"/api/budget/summary?year={now.year}&month={now.month}",
            headers=auth_headers
        )
        data = resp.get_json()
        assert data["income_total"]  == 5000.0
        assert data["expense_total"] == 1500.0
        assert data["balance"]       == 3500.0

    def test_chart_returns_12_months(self, client, auth_headers):
        resp = client.get("/api/budget/chart?year=2026&granularity=month",
                          headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 12

    def test_by_category(self, client, auth_headers):
        resp = client.get("/api/budget/by-category?type=expense",
                          headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), list)

    def test_forecast(self, client, auth_headers):
        resp = client.get("/api/budget/forecast?months=3",
                          headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["forecast"]) == 3


class TestInvoices:
    INVOICE = {
        "buyer_name":    "Firma XYZ Sp. z o.o.",
        "buyer_nip":     "1234567890",
        "buyer_address": "ul. Testowa 1\n00-001 Warszawa",
        "buyer_email":   "firma@example.com",
        "currency":      "PLN",
        "issue_date":    date.today().isoformat(),
        "notes":         "Płatność w ciągu 14 dni",
        "items": [
            {"name": "Usługa programistyczna", "qty": 10,
             "unit": "godz.", "unit_price_net": 150.0, "vat_rate": 23},
            {"name": "Hosting miesięczny",     "qty": 1,
             "unit": "mies.", "unit_price_net": 49.99, "vat_rate": 23},
        ],
    }

    def test_create_invoice(self, client, auth_headers):
        resp = client.post("/api/invoices/", json=self.INVOICE,
                           headers=auth_headers)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["buyer_name"] == "Firma XYZ Sp. z o.o."
        assert float(data["net_total"]) > 0
        assert data["status"] == "unpaid"
        # Numer auto-generowany
        assert data["number"].startswith("FV/")

    def test_auto_number_format(self, client, auth_headers):
        resp = client.post("/api/invoices/", json=self.INVOICE,
                           headers=auth_headers)
        number = resp.get_json()["number"]
        parts = number.split("/")
        assert parts[0] == "FV"
        assert len(parts) == 4

    def test_list_invoices(self, client, auth_headers):
        client.post("/api/invoices/", json=self.INVOICE, headers=auth_headers)
        resp = client.get("/api/invoices/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["total"] >= 1

    def test_status_transition_paid(self, client, auth_headers):
        inv = client.post("/api/invoices/", json=self.INVOICE,
                          headers=auth_headers).get_json()
        resp = client.patch(f"/api/invoices/{inv['id']}/status",
                            json={"status": "paid"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "paid"

    def test_cannot_edit_paid_invoice(self, client, auth_headers):
        inv = client.post("/api/invoices/", json=self.INVOICE,
                          headers=auth_headers).get_json()
        client.patch(f"/api/invoices/{inv['id']}/status",
                     json={"status": "paid"}, headers=auth_headers)
        resp = client.put(f"/api/invoices/{inv['id']}",
                          json={"notes": "zmiana"}, headers=auth_headers)
        assert resp.status_code == 400

    def test_invalid_status_transition(self, client, auth_headers):
        inv = client.post("/api/invoices/", json=self.INVOICE,
                          headers=auth_headers).get_json()
        resp = client.patch(f"/api/invoices/{inv['id']}/status",
                            json={"status": "draft"}, headers=auth_headers)
        assert resp.status_code == 400

    def test_pdf_generation(self, client, auth_headers):
        inv = client.post("/api/invoices/", json=self.INVOICE,
                          headers=auth_headers).get_json()
        resp = client.get(f"/api/invoices/{inv['id']}/pdf",
                          headers=auth_headers)
        assert resp.status_code == 200
        assert resp.content_type == "application/pdf"
        # PDF zaczyna się od %PDF-
        assert resp.data[:4] == b"%PDF"


class TestGroups:
    def test_create_and_list_group(self, client, auth_headers):
        resp = client.post("/api/groups/",
                           json={"name": "Rodzina", "type": "family"},
                           headers=auth_headers)
        assert resp.status_code == 201
        assert resp.get_json()["my_role"] == "owner"

        groups = client.get("/api/groups/", headers=auth_headers).get_json()
        assert any(g["name"] == "Rodzina" for g in groups)

    def test_invite_nonexistent_user(self, client, auth_headers):
        grp = client.post("/api/groups/",
                          json={"name": "Test"}, headers=auth_headers).get_json()
        resp = client.post(f"/api/groups/{grp['id']}/members",
                           json={"email": "nobody@example.com"},
                           headers=auth_headers)
        assert resp.status_code == 404

    def test_leave_group(self, client, auth_headers, db):
        from app.models.user import User
        # Stwórz drugiego użytkownika
        u2 = User(email="member2@example.com")
        u2.set_password("pass12345")
        db.session.add(u2)
        db.session.commit()

        # Zaloguj
        r = client.post("/api/auth/login",
                        json={"email": "member2@example.com",
                              "password": "pass12345"})
        h2 = {"Authorization": f"Bearer {r.get_json()['access_token']}"}

        # Owner tworzy grupę i dodaje u2
        grp = client.post("/api/groups/",
                          json={"name": "TestLeave"}, headers=auth_headers).get_json()
        client.post(f"/api/groups/{grp['id']}/members",
                    json={"email": "member2@example.com"}, headers=auth_headers)

        # u2 opuszcza grupę
        resp = client.post(f"/api/groups/{grp['id']}/leave", headers=h2)
        assert resp.status_code == 200

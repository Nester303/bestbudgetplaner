"""
/api/invoices — faktury VAT z generowaniem PDF.
"""
from __future__ import annotations
import io
from datetime import date, datetime, timezone

from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from ..models.models import Invoice
from ..models.user import User
from ..services.pdf_invoice import generate_invoice_pdf

invoices_bp = Blueprint("invoices", __name__)


def _next_number(user_id: int) -> str:
    now   = datetime.now(timezone.utc)
    count = Invoice.query.filter(
        Invoice.user_id == user_id,
        db.extract("year",  Invoice.issue_date) == now.year,
        db.extract("month", Invoice.issue_date) == now.month,
    ).count()
    return f"FV/{now.year}/{now.month:02d}/{count + 1:03d}"


def _recalc(items: list) -> tuple[float, float, float]:
    net = vat = gross = 0.0
    for item in items:
        qty      = float(item.get("qty", 1))
        unit_net = float(item.get("unit_price_net", 0))
        vat_rate = float(item.get("vat_rate", 23))
        n = qty * unit_net
        v = n * vat_rate / 100
        net += n; vat += v; gross += n + v
    return round(net, 2), round(vat, 2), round(gross, 2)


def _invoice_data(inv: Invoice, user: User) -> dict:
    """Buduje słownik danych faktury do PDF — z danymi sprzedawcy z profilu."""
    seller_name = user.seller_name or f"{user.first_name or ''} {user.last_name or ''}".strip()
    return {
        "number":     inv.number,
        "issue_date": inv.issue_date.isoformat() if inv.issue_date else None,
        "due_date":   inv.due_date.isoformat()   if inv.due_date   else None,
        "currency":   inv.currency,
        "notes":      inv.notes,
        "payment_method": "transfer",
        "seller": {
            "name":         seller_name,
            "nip":          user.seller_nip     or "",
            "address":      user.seller_address or "",
            "email":        user.seller_email   or user.email,
            "bank_account": user.seller_bank    or "",
        },
        "buyer": {
            "name":    inv.buyer_name,
            "nip":     inv.buyer_nip,
            "address": inv.buyer_address,
            "email":   inv.buyer_email,
        },
        "items": inv.items or [],
    }


def _create_invoice_logic(user_id: int, group_id: int = None):
    """Wspólna logika tworzenia faktury (używana przez /invoices/ i /groups/<id>/invoices)."""
    data  = request.get_json(silent=True) or {}
    items = data.get("items", [])
    net, vat, gross = _recalc(items)

    inv = Invoice(
        user_id       = user_id,
        group_id      = group_id,
        number        = data.get("number") or _next_number(user_id),
        issue_date    = date.fromisoformat(data.get("issue_date", date.today().isoformat())),
        due_date      = date.fromisoformat(data["due_date"]) if data.get("due_date") else None,
        status        = data.get("status", "unpaid"),
        buyer_name    = data.get("buyer_name"),
        buyer_nip     = data.get("buyer_nip"),
        buyer_address = data.get("buyer_address"),
        buyer_email   = data.get("buyer_email"),
        net_total=net, vat_total=vat, gross_total=gross,
        currency      = data.get("currency", "PLN"),
        notes         = data.get("notes"),
        items         = items,
    )
    db.session.add(inv)
    db.session.commit()
    return jsonify(inv.to_dict()), 201


@invoices_bp.get("/")
@jwt_required()
def list_invoices():
    user_id  = get_jwt_identity()
    status   = request.args.get("status")
    page     = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    q = Invoice.query.filter_by(user_id=user_id)
    if status:
        q = q.filter_by(status=status)
    paginated = q.order_by(Invoice.issue_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    return jsonify({"items": [i.to_dict() for i in paginated.items],
                    "total": paginated.total, "page": paginated.page,
                    "pages": paginated.pages})


@invoices_bp.post("/")
@jwt_required()
def create_invoice():
    user_id = int(get_jwt_identity())
    return _create_invoice_logic(user_id=user_id)


@invoices_bp.get("/<int:iid>")
@jwt_required()
def get_invoice(iid):
    user_id = get_jwt_identity()
    return jsonify(Invoice.query.filter_by(id=iid, user_id=user_id).first_or_404().to_dict())


@invoices_bp.put("/<int:iid>")
@jwt_required()
def update_invoice(iid):
    user_id = get_jwt_identity()
    inv     = Invoice.query.filter_by(id=iid, user_id=user_id).first_or_404()
    if inv.status == "paid":
        return jsonify({"error": "Nie można edytować opłaconej faktury"}), 400

    data = request.get_json(silent=True) or {}
    for f in ("buyer_name", "buyer_nip", "buyer_address", "buyer_email",
              "due_date", "notes", "currency", "items"):
        if f in data:
            setattr(inv, f, data[f])
    if "items" in data:
        n, v, g = _recalc(data["items"])
        inv.net_total = n; inv.vat_total = v; inv.gross_total = g
    db.session.commit()
    return jsonify(inv.to_dict())


@invoices_bp.delete("/<int:iid>")
@jwt_required()
def delete_invoice(iid):
    user_id = get_jwt_identity()
    inv = Invoice.query.filter_by(id=iid, user_id=user_id).first_or_404()
    if inv.status == "paid":
        return jsonify({"error": "Nie można usunąć opłaconej faktury"}), 400
    db.session.delete(inv)
    db.session.commit()
    return jsonify({"message": "Usunięto"})


@invoices_bp.patch("/<int:iid>/status")
@jwt_required()
def update_status(iid):
    user_id = get_jwt_identity()
    inv     = Invoice.query.filter_by(id=iid, user_id=user_id).first_or_404()
    new_status = (request.get_json(silent=True) or {}).get("status")
    allowed = {"draft": ["unpaid", "cancelled"], "unpaid": ["paid", "cancelled"]}
    if new_status not in allowed.get(inv.status, []):
        return jsonify({"error": f"Niedozwolona zmiana: {inv.status} → {new_status}"}), 400
    inv.status = new_status
    db.session.commit()
    return jsonify(inv.to_dict())


@invoices_bp.get("/<int:iid>/pdf")
@jwt_required()
def download_pdf(iid):
    user_id = int(get_jwt_identity())
    inv  = Invoice.query.filter_by(id=iid, user_id=user_id).first_or_404()
    user = User.query.get(user_id)
    pdf  = generate_invoice_pdf(_invoice_data(inv, user))
    return send_file(io.BytesIO(pdf), mimetype="application/pdf",
                     as_attachment=True,
                     download_name=f"faktura_{inv.number.replace('/', '_')}.pdf")


@invoices_bp.post("/<int:iid>/send")
@jwt_required()
def send_invoice(iid):
    user_id = int(get_jwt_identity())
    inv  = Invoice.query.filter_by(id=iid, user_id=user_id).first_or_404()
    user = User.query.get(user_id)
    if not inv.buyer_email:
        return jsonify({"error": "Brak adresu email nabywcy"}), 400
    try:
        import resend
        resend.api_key = current_app.config.get("RESEND_API_KEY", "")
        pdf = generate_invoice_pdf(_invoice_data(inv, user))
        import base64
        resend.Emails.send({
            "from":    current_app.config.get("MAIL_DEFAULT_SENDER", "onboarding@resend.dev"),
            "to":      [inv.buyer_email],
            "subject": f"Faktura {inv.number}",
            "html":    f"<p>W załączniku faktura nr {inv.number} ({inv.gross_total} {inv.currency}).</p>",
            "attachments": [{
                "filename": f"faktura_{inv.number.replace('/', '_')}.pdf",
                "content":  list(pdf),
            }],
        })
        return jsonify({"message": f"Wysłano na {inv.buyer_email}"})
    except Exception as exc:
        current_app.logger.error("Mail error: %s", exc)
        return jsonify({"error": "Błąd wysyłki"}), 500

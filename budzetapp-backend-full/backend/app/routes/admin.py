"""
/api/admin — panel administracyjny (tylko role=admin)
"""
from functools import wraps

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from ..extensions import db
from ..models.user import User
from ..models.transaction import Transaction
from ..models.models import Group, Invoice, Event

admin_bp = Blueprint("admin", __name__)


def admin_required(f):
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        if get_jwt().get("role") != "admin":
            return jsonify({"error": "Brak uprawnień administratora"}), 403
        return f(*args, **kwargs)
    return decorated


# ── Statystyki ────────────────────────────────────────────────

@admin_bp.get("/stats")
@admin_required
def stats():
    return jsonify({
        "users":        User.query.count(),
        "transactions": Transaction.query.count(),
        "groups":       Group.query.count(),
        "invoices":     Invoice.query.count(),
        "events":       Event.query.count(),
        "active_users": User.query.filter_by(is_active=True).count(),
    })


# ── Użytkownicy ───────────────────────────────────────────────

@admin_bp.get("/users")
@admin_required
def list_users():
    page     = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    search   = request.args.get("q", "")

    q = User.query
    if search:
        q = q.filter(User.email.ilike(f"%{search}%"))
    paginated = q.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": [u.to_dict(include_private=True) for u in paginated.items],
        "total": paginated.total, "page": paginated.page, "pages": paginated.pages,
    })


@admin_bp.patch("/users/<int:uid>")
@admin_required
def update_user(uid):
    user = User.query.get_or_404(uid)
    data = request.get_json(silent=True) or {}
    if "is_active" in data:
        user.is_active = bool(data["is_active"])
    if "role" in data and data["role"] in ("user", "admin"):
        user.role = data["role"]
    db.session.commit()
    return jsonify(user.to_dict(include_private=True))


@admin_bp.delete("/users/<int:uid>")
@admin_required
def delete_user(uid):
    me = get_jwt_identity()
    if uid == me:
        return jsonify({"error": "Nie możesz usunąć własnego konta"}), 400
    user = User.query.get_or_404(uid)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Użytkownik usunięty"})


# ── Wszystkie wydarzenia ──────────────────────────────────────

@admin_bp.get("/events")
@admin_required
def list_all_events():
    page     = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    paginated = Event.query.order_by(Event.start.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    return jsonify({"items": [e.to_dict() for e in paginated.items],
                    "total": paginated.total})


@admin_bp.delete("/events/<int:eid>")
@admin_required
def delete_event(eid):
    e = Event.query.get_or_404(eid)
    db.session.delete(e)
    db.session.commit()
    return jsonify({"message": "Usunięto"})


# ── Wszystkie transakcje ──────────────────────────────────────

@admin_bp.get("/transactions")
@admin_required
def list_all_transactions():
    page     = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    paginated = Transaction.query.order_by(Transaction.date.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    return jsonify({"items": [t.to_dict() for t in paginated.items],
                    "total": paginated.total})

"""
Transactions blueprint — CRUD dla transakcji użytkownika
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.transaction import Transaction

transactions_bp = Blueprint("transactions", __name__)


@transactions_bp.get("/")
@jwt_required()
def list_transactions():
    user_id = get_jwt_identity()
    # Filtrowanie opcjonalne przez query params: ?type=expense&month=2026-03
    qs = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.date.desc())

    t_type = request.args.get("type")
    if t_type in ("income", "expense"):
        qs = qs.filter_by(type=t_type)

    page     = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    paginated = qs.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": [t.to_dict() for t in paginated.items],
        "total": paginated.total,
        "page":  paginated.page,
        "pages": paginated.pages,
    })


@transactions_bp.post("/")
@jwt_required()
def create_transaction():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    required = ("title", "amount", "type", "date")
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Pole '{field}' jest wymagane"}), 400
    if data["type"] not in ("income", "expense"):
        return jsonify({"error": "type musi być 'income' lub 'expense'"}), 400

    t = Transaction(user_id=user_id, **{k: data[k] for k in (
        "title", "amount", "type", "date", "currency",
        "description", "category_id", "is_recurring", "recurrence_rule"
    ) if k in data})
    db.session.add(t)
    db.session.commit()
    return jsonify(t.to_dict()), 201


@transactions_bp.get("/<int:tid>")
@jwt_required()
def get_transaction(tid):
    user_id = get_jwt_identity()
    t = Transaction.query.filter_by(id=tid, user_id=user_id).first_or_404()
    return jsonify(t.to_dict())


@transactions_bp.put("/<int:tid>")
@jwt_required()
def update_transaction(tid):
    user_id = get_jwt_identity()
    t    = Transaction.query.filter_by(id=tid, user_id=user_id).first_or_404()
    data = request.get_json(silent=True) or {}
    for field in ("title", "amount", "type", "date", "description",
                  "category_id", "currency", "is_recurring", "recurrence_rule"):
        if field in data:
            setattr(t, field, data[field])
    db.session.commit()
    return jsonify(t.to_dict())


@transactions_bp.delete("/<int:tid>")
@jwt_required()
def delete_transaction(tid):
    user_id = get_jwt_identity()
    t = Transaction.query.filter_by(id=tid, user_id=user_id).first_or_404()
    db.session.delete(t)
    db.session.commit()
    return jsonify({"message": "Usunięto"}), 200

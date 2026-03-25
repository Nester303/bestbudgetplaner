"""
/api/categories — kategorie systemowe i własne użytkownika
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_

from ..extensions import db
from ..models.models import Category

categories_bp = Blueprint("categories", __name__)


@categories_bp.get("/")
@jwt_required()
def list_categories():
    """Zwraca kategorie systemowe + własne użytkownika."""
    user_id  = get_jwt_identity()
    tx_type  = request.args.get("type")   # income | expense | None

    q = Category.query.filter(
        or_(Category.user_id == user_id, Category.is_system == True)
    )
    if tx_type:
        q = q.filter(or_(Category.type == tx_type, Category.type == None))
    cats = q.order_by(Category.is_system.desc(), Category.name).all()
    return jsonify([c.to_dict() for c in cats])


@categories_bp.post("/")
@jwt_required()
def create_category():
    user_id = get_jwt_identity()
    data    = request.get_json(silent=True) or {}
    name    = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Nazwa kategorii jest wymagana"}), 400

    cat = Category(
        user_id   = user_id,
        name      = name,
        icon      = data.get("icon", "label"),
        color     = data.get("color", "#888780"),
        type      = data.get("type"),
        is_system = False,
    )
    db.session.add(cat)
    db.session.commit()
    return jsonify(cat.to_dict()), 201


@categories_bp.put("/<int:cid>")
@jwt_required()
def update_category(cid):
    user_id = get_jwt_identity()
    cat = Category.query.filter_by(id=cid, user_id=user_id,
                                    is_system=False).first_or_404()
    data = request.get_json(silent=True) or {}
    for f in ("name", "icon", "color", "type"):
        if f in data:
            setattr(cat, f, data[f])
    db.session.commit()
    return jsonify(cat.to_dict())


@categories_bp.delete("/<int:cid>")
@jwt_required()
def delete_category(cid):
    user_id = get_jwt_identity()
    cat = Category.query.filter_by(id=cid, user_id=user_id,
                                    is_system=False).first_or_404()
    db.session.delete(cat)
    db.session.commit()
    return jsonify({"message": "Usunięto"})

"""Events, Groups, Invoices, Admin — szkielety blueprintów"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

events_bp   = Blueprint("events",   __name__)
groups_bp   = Blueprint("groups",   __name__)
invoices_bp = Blueprint("invoices", __name__)
admin_bp    = Blueprint("admin",    __name__)


# --- EVENTS ---
@events_bp.get("/")
@jwt_required()
def list_events():
    from ..models.models import Event
    user_id = get_jwt_identity()
    evs = Event.query.filter_by(user_id=user_id).all()
    return jsonify([e.to_dict() for e in evs])


@events_bp.post("/")
@jwt_required()
def create_event():
    from flask import request
    from ..extensions import db
    from ..models.models import Event
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    e = Event(user_id=user_id,
              title=data.get("title", ""),
              start=data.get("start"),
              end=data.get("end"),
              color=data.get("color", "#1a73e8"),
              category=data.get("category", "other"),
              description=data.get("description", ""))
    db.session.add(e)
    db.session.commit()
    return jsonify(e.to_dict()), 201


@events_bp.put("/<int:eid>")
@jwt_required()
def update_event(eid):
    from flask import request
    from ..extensions import db
    from ..models.models import Event
    user_id = get_jwt_identity()
    e = Event.query.filter_by(id=eid, user_id=user_id).first_or_404()
    data = request.get_json(silent=True) or {}
    for f in ("title", "start", "end", "color", "category", "description"):
        if f in data:
            setattr(e, f, data[f])
    db.session.commit()
    return jsonify(e.to_dict())


@events_bp.delete("/<int:eid>")
@jwt_required()
def delete_event(eid):
    from ..extensions import db
    from ..models.models import Event
    user_id = get_jwt_identity()
    e = Event.query.filter_by(id=eid, user_id=user_id).first_or_404()
    db.session.delete(e)
    db.session.commit()
    return jsonify({"message": "Usunięto"})


# --- GROUPS (szkielet) ---
@groups_bp.get("/")
@jwt_required()
def list_groups():
    return jsonify([])


# --- INVOICES (szkielet) ---
@invoices_bp.get("/")
@jwt_required()
def list_invoices():
    from ..models.models import Invoice
    user_id = get_jwt_identity()
    invs = Invoice.query.filter_by(user_id=user_id).all()
    return jsonify([i.to_dict() for i in invs])


# --- ADMIN (tylko role=admin) ---
def admin_required():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Brak uprawnień"}), 403
    return None


@admin_bp.get("/users")
@jwt_required()
def admin_list_users():
    err = admin_required()
    if err:
        return err
    from ..models.user import User
    return jsonify([u.to_dict(include_private=True) for u in User.query.all()])


@admin_bp.delete("/users/<int:uid>")
@jwt_required()
def admin_delete_user(uid):
    err = admin_required()
    if err:
        return err
    from ..extension import db
    from ..models.user import User
    u = User.query.get_or_404(uid)
    db.session.delete(u)
    db.session.commit()
    return jsonify({"message": "Usunięto"})


@admin_bp.get("/stats")
@jwt_required()
def admin_stats():
    err = admin_required()
    if err:
        return err
    from ..models.user import User
    from ..models.transaction import Transaction
    from ..models.models import Group, Invoice
    return jsonify({
        "users":        User.query.count(),
        "transactions": Transaction.query.count(),
        "groups":       Group.query.count(),
        "invoices":     Invoice.query.count(),
    })

"""
/api/events — kalendarz wydarzeń (własne + grupowe)
"""
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from sqlalchemy import or_
from ..models.models import Event, Group, group_members

events_bp = Blueprint("events", __name__)


def _ev_dict(e):
    d = e.to_dict()
    if e.group_id:
        g = Group.query.get(e.group_id)
        d["group_name"] = g.name if g else None
    else:
        d["group_name"] = None
    return d


@events_bp.get("/")
@jwt_required()
def list_events():
    user_id  = int(get_jwt_identity())
    group_id = request.args.get("group_id", type=int)

    # Grupy użytkownika
    member_gids = db.session.execute(
        db.select(group_members.c.group_id).where(group_members.c.user_id == user_id)
    ).scalars().all()

    q = Event.query.filter(
        or_(Event.user_id == user_id,
            Event.group_id.in_(member_gids) if member_gids else False)
    )

    if request.args.get("start"):
        q = q.filter(Event.start >= request.args["start"])
    if request.args.get("end"):
        q = q.filter(Event.start <= request.args["end"])
    if group_id:
        q = Event.query.filter_by(group_id=group_id)
        if request.args.get("start"):
            q = q.filter(Event.start >= request.args["start"])

    return jsonify([_ev_dict(e) for e in q.order_by(Event.start).all()])


@events_bp.post("/")
@jwt_required()
def create_event():
    user_id = get_jwt_identity()
    data    = request.get_json(silent=True) or {}

    if not data.get("title") or not data.get("start"):
        return jsonify({"error": "Tytuł i data rozpoczęcia są wymagane"}), 400

    e = Event(
        user_id     = user_id,
        group_id    = data.get("group_id"),
        title       = data["title"],
        description = data.get("description", ""),
        start       = data["start"],
        end         = data.get("end"),
        all_day     = data.get("all_day", False),
        color       = data.get("color", "#1a73e8"),
        category    = data.get("category", "other"),
        is_recurring    = data.get("is_recurring", False),
        recurrence_rule = data.get("recurrence_rule"),
        transaction_id  = data.get("transaction_id"),
    )
    db.session.add(e)
    db.session.commit()
    return jsonify(e.to_dict()), 201


@events_bp.get("/<int:eid>")
@jwt_required()
def get_event(eid):
    user_id = get_jwt_identity()
    e = Event.query.filter_by(id=eid, user_id=user_id).first_or_404()
    return jsonify(e.to_dict())


@events_bp.put("/<int:eid>")
@jwt_required()
def update_event(eid):
    user_id = get_jwt_identity()
    e    = Event.query.filter_by(id=eid, user_id=user_id).first_or_404()
    data = request.get_json(silent=True) or {}
    for f in ("title", "description", "start", "end", "all_day",
              "color", "category", "is_recurring", "recurrence_rule"):
        if f in data:
            setattr(e, f, data[f])
    db.session.commit()
    return jsonify(e.to_dict())


@events_bp.delete("/<int:eid>")
@jwt_required()
def delete_event(eid):
    from sqlalchemy import text as _text
    user_id = int(get_jwt_identity())
    e = Event.query.filter_by(id=eid).first_or_404()

    # Właściciel może zawsze usunąć
    if e.user_id == user_id:
        db.session.delete(e)
        db.session.commit()
        return jsonify({"message": "Usunięto"})

    # Admin lub owner grupy może usunąć wydarzenie grupowe
    if e.group_id:
        role = db.session.execute(
            _text("SELECT role FROM group_members WHERE group_id=:g AND user_id=:u"),
            {"g": e.group_id, "u": user_id}
        ).scalar()
        if role in ("owner", "admin"):
            db.session.delete(e)
            db.session.commit()
            return jsonify({"message": "Usunięto"})

    return jsonify({"error": "Brak uprawnień"}), 403

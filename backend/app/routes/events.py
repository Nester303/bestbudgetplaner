"""
/api/events — kalendarz wydarzeń (własne + grupowe)
"""
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from ..models.models import Event

events_bp = Blueprint("events", __name__)


@events_bp.get("/")
@jwt_required()
def list_events():
    user_id  = get_jwt_identity()
    group_id = request.args.get("group_id", type=int)

    q = Event.query.filter_by(user_id=user_id)

    # Filtr zakresu dat (FullCalendar wysyła ?start=...&end=...)
    if request.args.get("start"):
        q = q.filter(Event.start >= request.args["start"])
    if request.args.get("end"):
        q = q.filter(Event.start <= request.args["end"])
    if group_id:
        q = Event.query.filter_by(group_id=group_id)

    return jsonify([e.to_dict() for e in q.order_by(Event.start).all()])


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
    user_id = get_jwt_identity()
    e = Event.query.filter_by(id=eid, user_id=user_id).first_or_404()
    db.session.delete(e)
    db.session.commit()
    return jsonify({"message": "Usunięto"})

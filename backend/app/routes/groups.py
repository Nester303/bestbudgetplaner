"""
/api/groups — zarządzanie grupami budżetowymi

Endpointy:
  GET    /api/groups/                   – grupy użytkownika
  POST   /api/groups/                   – utwórz grupę
  GET    /api/groups/<id>               – szczegóły grupy
  PUT    /api/groups/<id>               – edytuj (owner/admin)
  DELETE /api/groups/<id>               – usuń (owner)
  GET    /api/groups/<id>/members       – lista członków
  POST   /api/groups/<id>/members       – zaproś przez email
  PUT    /api/groups/<id>/members/<uid> – zmień rolę
  DELETE /api/groups/<id>/members/<uid> – usuń z grupy
  POST   /api/groups/<id>/leave         – opuść grupę
  GET    /api/groups/<id>/transactions  – transakcje grupy
  GET    /api/groups/<id>/summary       – podsumowanie budżetu grupy
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, text

from ..extensions import db
from ..models.models import Group
from ..models.user import User
from ..models.transaction import Transaction

groups_bp = Blueprint("groups", __name__)


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def _get_member_role(group_id: int, user_id: int):
    row = db.session.execute(
        text("SELECT role FROM group_members WHERE group_id=:g AND user_id=:u"),
        {"g": group_id, "u": user_id}
    ).fetchone()
    return row[0] if row else None


def _require_role(group_id: int, user_id: int, min_role: str = "member"):
    role = _get_member_role(group_id, user_id)
    hierarchy = {None: -1, "member": 0, "admin": 1, "owner": 2}
    if hierarchy.get(role, -1) < hierarchy.get(min_role, 0):
        return jsonify({"error": "Niewystarczające uprawnienia"}), 403
    return None


def _members_list(group_id: int) -> list[dict]:
    rows = db.session.execute(
        text("""
            SELECT u.id, u.email, u.first_name, u.last_name, u.avatar_url,
                   gm.role, gm.joined_at
            FROM group_members gm
            JOIN users u ON u.id = gm.user_id
            WHERE gm.group_id = :g
            ORDER BY CASE gm.role WHEN 'owner' THEN 0 WHEN 'admin' THEN 1 ELSE 2 END
        """),
        {"g": group_id}
    ).fetchall()
    return [{
        "id": r.id, "email": r.email, "first_name": r.first_name,
        "last_name": r.last_name, "avatar_url": r.avatar_url,
        "role": r.role,
        "joined_at": r.joined_at.isoformat() if r.joined_at else None,
    } for r in rows]


# ─────────────────────────────────────────────
#  CRUD grupy
# ─────────────────────────────────────────────

@groups_bp.get("/")
@jwt_required()
def list_groups():
    user_id = get_jwt_identity()
    rows = db.session.execute(
        text("""
            SELECT g.id, g.name, g.type, g.description, g.created_by, g.created_at,
                   gm.role,
                   (SELECT COUNT(*) FROM group_members WHERE group_id = g.id) AS member_count
            FROM groups g
            JOIN group_members gm ON gm.group_id = g.id
            WHERE gm.user_id = :uid
            ORDER BY g.created_at DESC
        """),
        {"uid": user_id}
    ).fetchall()
    return jsonify([{
        "id": r.id, "name": r.name, "type": r.type,
        "description": r.description, "created_by": r.created_by,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "my_role": r.role, "member_count": r.member_count,
    } for r in rows])


@groups_bp.post("/")
@jwt_required()
def create_group():
    user_id = get_jwt_identity()
    data    = request.get_json(silent=True) or {}
    name    = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Nazwa grupy jest wymagana"}), 400

    group = Group(name=name, type=data.get("type", "family"),
                  description=data.get("description", ""), created_by=user_id)
    db.session.add(group)
    db.session.flush()

    db.session.execute(
        text("INSERT INTO group_members (user_id, group_id, role) VALUES (:u, :g, 'owner')"),
        {"u": user_id, "g": group.id}
    )
    db.session.commit()
    return jsonify({**group.to_dict(), "my_role": "owner"}), 201


@groups_bp.get("/<int:gid>")
@jwt_required()
def get_group(gid):
    user_id = get_jwt_identity()
    err = _require_role(gid, user_id)
    if err:
        return err
    group = Group.query.get_or_404(gid)
    return jsonify({**group.to_dict(), "my_role": _get_member_role(gid, user_id),
                    "members": _members_list(gid)})


@groups_bp.put("/<int:gid>")
@jwt_required()
def update_group(gid):
    user_id = get_jwt_identity()
    err = _require_role(gid, user_id, "admin")
    if err:
        return err
    group = Group.query.get_or_404(gid)
    data  = request.get_json(silent=True) or {}
    for f in ("name", "type", "description"):
        if f in data:
            setattr(group, f, data[f])
    db.session.commit()
    return jsonify(group.to_dict())


@groups_bp.delete("/<int:gid>")
@jwt_required()
def delete_group(gid):
    user_id = get_jwt_identity()
    err = _require_role(gid, user_id, "owner")
    if err:
        return err
    group = Group.query.get_or_404(gid)
    db.session.delete(group)
    db.session.commit()
    return jsonify({"message": "Grupa usunięta"})


# ─────────────────────────────────────────────
#  Członkowie
# ─────────────────────────────────────────────

@groups_bp.get("/<int:gid>/members")
@jwt_required()
def list_members(gid):
    user_id = get_jwt_identity()
    err = _require_role(gid, user_id)
    if err:
        return err
    return jsonify(_members_list(gid))


@groups_bp.post("/<int:gid>/members")
@jwt_required()
def invite_member(gid):
    user_id = get_jwt_identity()
    err = _require_role(gid, user_id, "admin")
    if err:
        return err

    data    = request.get_json(silent=True) or {}
    email   = (data.get("email") or "").strip().lower()
    role    = data.get("role", "member")

    if role not in ("member", "admin"):
        return jsonify({"error": "Rola musi być 'member' lub 'admin'"}), 400

    invitee = User.query.filter_by(email=email).first()
    if not invitee:
        return jsonify({"error": f"Użytkownik {email} nie istnieje"}), 404
    if _get_member_role(gid, invitee.id):
        return jsonify({"error": "Użytkownik jest już w grupie"}), 409

    db.session.execute(
        text("INSERT INTO group_members (user_id, group_id, role) VALUES (:u, :g, :r)"),
        {"u": invitee.id, "g": gid, "r": role}
    )
    db.session.commit()
    return jsonify({"message": f"Dodano {email} jako {role}"}), 201


@groups_bp.put("/<int:gid>/members/<int:uid>")
@jwt_required()
def update_member_role(gid, uid):
    user_id = get_jwt_identity()
    err = _require_role(gid, user_id, "owner")
    if err:
        return err
    if uid == user_id:
        return jsonify({"error": "Nie możesz zmienić swojej roli"}), 400
    role = (request.get_json(silent=True) or {}).get("role")
    if role not in ("member", "admin"):
        return jsonify({"error": "Nieprawidłowa rola"}), 400
    db.session.execute(
        text("UPDATE group_members SET role=:r WHERE group_id=:g AND user_id=:u"),
        {"r": role, "g": gid, "u": uid}
    )
    db.session.commit()
    return jsonify({"message": "Rola zaktualizowana"})


@groups_bp.delete("/<int:gid>/members/<int:uid>")
@jwt_required()
def remove_member(gid, uid):
    user_id = get_jwt_identity()
    err = _require_role(gid, user_id, "admin")
    if err:
        return err
    if _get_member_role(gid, uid) == "owner":
        return jsonify({"error": "Nie można usunąć właściciela"}), 403
    db.session.execute(
        text("DELETE FROM group_members WHERE group_id=:g AND user_id=:u"),
        {"g": gid, "u": uid}
    )
    db.session.commit()
    return jsonify({"message": "Usunięto z grupy"})


@groups_bp.post("/<int:gid>/leave")
@jwt_required()
def leave_group(gid):
    user_id = get_jwt_identity()
    role = _get_member_role(gid, user_id)
    if not role:
        return jsonify({"error": "Nie jesteś członkiem tej grupy"}), 404
    if role == "owner":
        return jsonify({"error": "Przekaż własność przed opuszczeniem grupy"}), 400
    db.session.execute(
        text("DELETE FROM group_members WHERE group_id=:g AND user_id=:u"),
        {"g": gid, "u": user_id}
    )
    db.session.commit()
    return jsonify({"message": "Opuszczono grupę"})


# ─────────────────────────────────────────────
#  Transakcje i statystyki grupy
# ─────────────────────────────────────────────

@groups_bp.get("/<int:gid>/transactions")
@jwt_required()
def group_transactions(gid):
    user_id = get_jwt_identity()
    err = _require_role(gid, user_id)
    if err:
        return err
    page      = request.args.get("page", 1, type=int)
    per_page  = request.args.get("per_page", 50, type=int)
    paginated = (Transaction.query.filter_by(group_id=gid)
                 .order_by(Transaction.date.desc())
                 .paginate(page=page, per_page=per_page, error_out=False))
    return jsonify({"items": [t.to_dict() for t in paginated.items],
                    "total": paginated.total, "page": paginated.page,
                    "pages": paginated.pages})


@groups_bp.get("/<int:gid>/summary")
@jwt_required()
def group_summary(gid):
    user_id = get_jwt_identity()
    err = _require_role(gid, user_id)
    if err:
        return err
    rows = db.session.query(Transaction.type,
                             func.sum(Transaction.amount).label("total")
                             ).filter_by(group_id=gid).group_by(Transaction.type).all()
    totals  = {r.type: float(r.total) for r in rows}
    income  = totals.get("income",  0.0)
    expense = totals.get("expense", 0.0)
    return jsonify({"group_id": gid, "income_total": round(income, 2),
                    "expense_total": round(expense, 2),
                    "balance": round(income - expense, 2)})

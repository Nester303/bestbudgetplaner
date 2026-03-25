from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from ..extensions import db, limiter
from ..models.user import User

auth_bp = Blueprint("auth", __name__)


# ----------------------------------------------------------
#  POST /api/auth/register
# ----------------------------------------------------------
@auth_bp.post("/register")
@limiter.limit("10 per hour")
def register():
    data = request.get_json(silent=True) or {}
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    first_name = data.get("first_name", "")
    last_name  = data.get("last_name", "")

    if not email or not password:
        return jsonify({"error": "Email i hasło są wymagane"}), 400
    if len(password) < 8:
        return jsonify({"error": "Hasło musi mieć co najmniej 8 znaków"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Konto z tym emailem już istnieje"}), 409

    user = User(email=email, first_name=first_name, last_name=last_name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    access_token  = create_access_token(identity=user.id,
                                         additional_claims={"role": user.role})
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({
        "user":          user.to_dict(),
        "access_token":  access_token,
        "refresh_token": refresh_token,
    }), 201


# ----------------------------------------------------------
#  POST /api/auth/login
# ----------------------------------------------------------
@auth_bp.post("/login")
@limiter.limit("20 per hour")
def login():
    data     = request.get_json(silent=True) or {}
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email, is_active=True).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Nieprawidłowy email lub hasło"}), 401

    access_token  = create_access_token(identity=user.id,
                                         additional_claims={"role": user.role})
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({
        "user":          user.to_dict(),
        "access_token":  access_token,
        "refresh_token": refresh_token,
    })


# ----------------------------------------------------------
#  POST /api/auth/refresh
# ----------------------------------------------------------
@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user    = User.query.get_or_404(user_id)
    token   = create_access_token(identity=user_id,
                                   additional_claims={"role": user.role})
    return jsonify({"access_token": token})


# ----------------------------------------------------------
#  GET /api/auth/me
# ----------------------------------------------------------
@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user    = User.query.get_or_404(user_id)
    return jsonify(user.to_dict(include_private=True))


# ----------------------------------------------------------
#  POST /api/auth/logout  (blacklist tokena w Redis)
# ----------------------------------------------------------
@auth_bp.post("/logout")
@jwt_required()
def logout():
    from ..extensions import redis_client
    jti = get_jwt()["jti"]
    exp = get_jwt()["exp"]
    import time
    ttl = max(0, int(exp - time.time()))
    if redis_client:
        redis_client.setex(f"blacklist:{jti}", ttl, "1")
    return jsonify({"message": "Wylogowano pomyślnie"})

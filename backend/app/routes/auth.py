import random
import time
from datetime import datetime, timezone, timedelta

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)

from ..extensions import db, limiter
from ..models.user import User

auth_bp = Blueprint("auth", __name__)


def _send_verify_email(user):
    import resend
    resend.api_key = current_app.config["RESEND_API_KEY"]

    name = user.first_name or ""
    greeting = f"Witaj {name}!" if name else "Witaj!"

    html_content = (
        "<div style='font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px'>"
        f"<h2 style='color:#0f1117;margin-bottom:8px'>{greeting}</h2>"
        "<p style='color:#6b7280;margin-bottom:24px'>"
        "Dziekujemy za rejestracje w BudzetApp. "
        "Podaj ponizszy kod, aby potwierdzic swoj adres email."
        "</p>"
        "<div style='background:#f1f5f9;border-radius:12px;padding:24px;text-align:center;margin-bottom:24px'>"
        f"<span style='font-size:40px;font-weight:700;letter-spacing:12px;color:#0f1117;font-family:monospace'>{user.verify_code}</span>"
        "</div>"
        "<p style='color:#6b7280;font-size:14px'>"
        "Kod jest wazny przez <strong>15 minut</strong>.<br>"
        "Jesli to nie Ty sie rejestrujesz, zignoruj te wiadomosc."
        "</p>"
        "<hr style='border:none;border-top:1px solid #e5e7eb;margin:24px 0'>"
        "<p style='color:#9ca3af;font-size:12px'>BudzetApp - app.bestbudgetplaner.pl</p>"
        "</div>"
    )

    sender = current_app.config.get("MAIL_DEFAULT_SENDER", "onboarding@resend.dev")
    params = {
        "from":    sender,
        "to":      [user.email],
        "subject": "Twoj kod weryfikacyjny - BudzetApp",
        "html":    html_content,
    }
    resend.Emails.send(params)


def _generate_code(user):
    user.verify_code     = f"{random.randint(0, 9999):04d}"
    user.verify_code_exp = datetime.now(timezone.utc) + timedelta(minutes=15)


@auth_bp.post("/register")
@limiter.limit("10 per hour")
def register():
    data       = request.get_json(silent=True) or {}
    email      = (data.get("email") or "").strip().lower()
    password   = data.get("password") or ""
    first_name = (data.get("first_name") or "").strip()
    last_name  = (data.get("last_name")  or "").strip()

    if not email or not password:
        return jsonify({"error": "Email i haslo sa wymagane"}), 400
    if len(password) < 8:
        return jsonify({"error": "Haslo musi miec co najmniej 8 znakow"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Konto z tym emailem juz istnieje"}), 409

    user = User(email=email, first_name=first_name, last_name=last_name)
    user.set_password(password)
    user.is_verified = False
    _generate_code(user)
    db.session.add(user)
    db.session.commit()

    try:
        _send_verify_email(user)
    except Exception as e:
        current_app.logger.error(f"Blad emaila do {email}: {e}")

    return jsonify({
        "status":  "verify_required",
        "email":   email,
        "message": "Wyslalismy kod weryfikacyjny na Twoj adres email.",
    }), 201


@auth_bp.post("/verify")
@limiter.limit("20 per hour")
def verify():
    data  = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    code  = (data.get("code")  or "").strip()

    if not email or not code:
        return jsonify({"error": "Email i kod sa wymagane"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Nie znaleziono konta"}), 404
    if user.is_verified:
        return jsonify({"error": "Konto juz zostalo zweryfikowane"}), 409
    if not user.verify_code or not user.verify_code_exp:
        return jsonify({"error": "Brak aktywnego kodu - popros o nowy"}), 400
    if datetime.now(timezone.utc) > user.verify_code_exp:
        return jsonify({"error": "Kod wygasl - popros o nowy"}), 400
    if user.verify_code != code:
        return jsonify({"error": "Nieprawidlowy kod weryfikacyjny"}), 400

    user.is_verified     = True
    user.verify_code     = None
    user.verify_code_exp = None
    db.session.commit()

    access_token  = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "user":          user.to_dict(),
        "access_token":  access_token,
        "refresh_token": refresh_token,
    })


@auth_bp.post("/resend-code")
@limiter.limit("5 per hour")
def resend_code():
    data  = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return jsonify({"error": "Email jest wymagany"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "Jesli konto istnieje, kod zostal wyslany"}), 200
    if user.is_verified:
        return jsonify({"error": "Konto juz zostalo zweryfikowane"}), 409

    _generate_code(user)
    db.session.commit()

    try:
        _send_verify_email(user)
    except Exception as e:
        current_app.logger.error(f"Blad emaila do {email}: {e}")
        return jsonify({"error": "Blad wysylania emaila - sprobuj ponownie"}), 500

    return jsonify({"message": "Nowy kod zostal wyslany"})


@auth_bp.post("/login")
@limiter.limit("20 per hour")
def login():
    data     = request.get_json(silent=True) or {}
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email, is_active=True).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Nieprawidlowy email lub haslo"}), 401

    if not user.is_verified:
        return jsonify({
            "error":   "verify_required",
            "email":   email,
            "message": "Potwierdz swoj adres email przed zalogowaniem.",
        }), 403

    access_token  = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "user":          user.to_dict(),
        "access_token":  access_token,
        "refresh_token": refresh_token,
    })


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user    = User.query.get_or_404(user_id)
    token   = create_access_token(identity=str(user_id), additional_claims={"role": user.role})
    return jsonify({"access_token": token})


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user    = User.query.get_or_404(user_id)
    return jsonify(user.to_dict(include_private=True))


@auth_bp.put("/me")
@jwt_required()
def update_me():
    user_id = get_jwt_identity()
    user    = User.query.get_or_404(user_id)
    data    = request.get_json(silent=True) or {}
    if "first_name"       in data: user.first_name       = data["first_name"].strip()
    if "last_name"        in data: user.last_name        = data["last_name"].strip()
    if "default_currency" in data: user.default_currency = data["default_currency"]
    if "timezone"         in data: user.timezone         = data["timezone"]
    db.session.commit()
    return jsonify(user.to_dict(include_private=True))


@auth_bp.post("/change-password")
@jwt_required()
def change_password():
    user_id  = get_jwt_identity()
    user     = User.query.get_or_404(user_id)
    data     = request.get_json(silent=True) or {}
    new_pass = data.get("new_password") or ""
    if len(new_pass) < 8:
        return jsonify({"error": "Haslo musi miec co najmniej 8 znakow"}), 400
    user.set_password(new_pass)
    db.session.commit()
    return jsonify({"message": "Haslo zmienione pomyslnie"})


@auth_bp.post("/logout")
@jwt_required()
def logout():
    from ..extensions import redis_client
    jti = get_jwt()["jti"]
    exp = get_jwt()["exp"]
    ttl = max(0, int(exp - time.time()))
    if redis_client:
        redis_client.setex(f"blacklist:{jti}", ttl, "1")
    return jsonify({"message": "Wylogowano pomyslnie"})

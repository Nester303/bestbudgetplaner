from datetime import datetime, timezone
import bcrypt
from ..extensions import db


class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name    = db.Column(db.String(100))
    last_name     = db.Column(db.String(100))
    avatar_url    = db.Column(db.String(500))
    role          = db.Column(db.String(20), default="user", nullable=False)
    # role: "user" | "admin"
    is_active     = db.Column(db.Boolean, default=True, nullable=False)
    is_verified   = db.Column(db.Boolean, default=False, nullable=False)
    verify_token  = db.Column(db.String(255))

    # Preferencje
    default_currency = db.Column(db.String(3), default="PLN")
    timezone         = db.Column(db.String(50), default="Europe/Warsaw")

    created_at    = db.Column(db.DateTime(timezone=True),
                               default=lambda: datetime.now(timezone.utc))
    updated_at    = db.Column(db.DateTime(timezone=True),
                               default=lambda: datetime.now(timezone.utc),
                               onupdate=lambda: datetime.now(timezone.utc))

    # --- Relacje ---
    transactions  = db.relationship("Transaction", backref="user",
                                     lazy="dynamic", cascade="all, delete-orphan")
    events        = db.relationship("Event", backref="user",
                                     lazy="dynamic", cascade="all, delete-orphan")
    invoices      = db.relationship("Invoice", backref="user",
                                     lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(rounds=12)
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            self.password_hash.encode("utf-8")
        )

    def to_dict(self, include_private: bool = False) -> dict:
        data = {
            "id":               self.id,
            "email":            self.email,
            "first_name":       self.first_name,
            "last_name":        self.last_name,
            "avatar_url":       self.avatar_url,
            "role":             self.role,
            "is_active":        self.is_active,
            "default_currency": self.default_currency,
            "timezone":         self.timezone,
            "created_at":       self.created_at.isoformat() if self.created_at else None,
        }
        if include_private:
            data["is_verified"] = self.is_verified
        return data

    def __repr__(self):
        return f"<User {self.email} [{self.role}]>"

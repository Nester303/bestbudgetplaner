from datetime import datetime, timezone
from ..extensions import db

# ----------------------------------------------------------
#  Category
# ----------------------------------------------------------

class Category(db.Model):
    __tablename__ = "categories"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                             nullable=True)       # NULL = systemowa (dla wszystkich)
    name        = db.Column(db.String(100), nullable=False)
    icon        = db.Column(db.String(50))        # nazwa ikony Material Icons
    color       = db.Column(db.String(7), default="#1a73e8")
    type        = db.Column(db.String(10))        # "income" | "expense" | None = obydwa
    is_system   = db.Column(db.Boolean, default=False)

    transactions = db.relationship("Transaction", backref="category", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id":        self.id,
            "name":      self.name,
            "icon":      self.icon,
            "color":     self.color,
            "type":      self.type,
            "is_system": self.is_system,
        }


# ----------------------------------------------------------
#  Event (kalendarz)
# ----------------------------------------------------------

class Event(db.Model):
    __tablename__ = "events"

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                              nullable=False, index=True)
    group_id     = db.Column(db.Integer, db.ForeignKey("groups.id", ondelete="SET NULL"),
                              nullable=True)

    title        = db.Column(db.String(255), nullable=False)
    description  = db.Column(db.Text)
    start        = db.Column(db.DateTime(timezone=True), nullable=False)
    end          = db.Column(db.DateTime(timezone=True))
    all_day      = db.Column(db.Boolean, default=False)
    color        = db.Column(db.String(7), default="#1a73e8")
    category     = db.Column(db.String(50), default="other")
    # Powiązanie z transakcją (opcjonalne)
    transaction_id = db.Column(db.Integer, db.ForeignKey("transactions.id",
                                                           ondelete="SET NULL"),
                                nullable=True)

    # Cykliczność
    is_recurring     = db.Column(db.Boolean, default=False)
    recurrence_rule  = db.Column(db.String(50))

    created_at   = db.Column(db.DateTime(timezone=True),
                              default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "user_id":     self.user_id,
            "group_id":    self.group_id,
            "title":       self.title,
            "description": self.description,
            "start":       self.start.isoformat() if self.start else None,
            "end":         self.end.isoformat() if self.end else None,
            "all_day":     self.all_day,
            "color":       self.color,
            "category":    self.category,
        }


# ----------------------------------------------------------
#  Group
# ----------------------------------------------------------

group_members = db.Table(
    "group_members",
    db.Column("user_id",  db.Integer, db.ForeignKey("users.id",  ondelete="CASCADE")),
    db.Column("group_id", db.Integer, db.ForeignKey("groups.id", ondelete="CASCADE")),
    db.Column("role",     db.String(20), default="member"),
    # role: "owner" | "admin" | "member"
    db.Column("joined_at", db.DateTime(timezone=True),
              default=lambda: datetime.now(timezone.utc)),
)


class Group(db.Model):
    __tablename__ = "groups"

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    type        = db.Column(db.String(20), default="family")
    # type: "family" | "company" | "other"
    description = db.Column(db.Text)
    created_by  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at  = db.Column(db.DateTime(timezone=True),
                             default=lambda: datetime.now(timezone.utc))

    members     = db.relationship("User", secondary=group_members,
                                   lazy="dynamic", backref="groups")

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "name":        self.name,
            "type":        self.type,
            "description": self.description,
            "created_by":  self.created_by,
            "created_at":  self.created_at.isoformat() if self.created_at else None,
        }


# ----------------------------------------------------------
#  Invoice
# ----------------------------------------------------------

class Invoice(db.Model):
    __tablename__ = "invoices"

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                                  nullable=False, index=True)
    number           = db.Column(db.String(50), nullable=False)
    issue_date       = db.Column(db.Date, nullable=False)
    due_date         = db.Column(db.Date)
    status           = db.Column(db.String(20), default="unpaid")
    # status: "draft" | "unpaid" | "paid" | "cancelled"

    # Dane nabywcy
    buyer_name       = db.Column(db.String(255))
    buyer_nip        = db.Column(db.String(20))
    buyer_address    = db.Column(db.Text)
    buyer_email      = db.Column(db.String(255))

    # Kwoty
    net_total        = db.Column(db.Numeric(12, 2))
    vat_total        = db.Column(db.Numeric(12, 2))
    gross_total      = db.Column(db.Numeric(12, 2))
    currency         = db.Column(db.String(3), default="PLN")

    notes            = db.Column(db.Text)
    pdf_url          = db.Column(db.String(500))

    # Pozycje faktury przechowywane jako JSON
    items            = db.Column(db.JSON, default=list)

    created_at       = db.Column(db.DateTime(timezone=True),
                                  default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "number":      self.number,
            "issue_date":  self.issue_date.isoformat() if self.issue_date else None,
            "due_date":    self.due_date.isoformat() if self.due_date else None,
            "status":      self.status,
            "buyer_name":  self.buyer_name,
            "gross_total": str(self.gross_total) if self.gross_total else None,
            "currency":    self.currency,
            "items":       self.items,
        }

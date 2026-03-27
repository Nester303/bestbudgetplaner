from datetime import datetime, timezone
from ..extensions import db


class Transaction(db.Model):
    __tablename__ = "transactions"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                             nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete="SET NULL"),
                             nullable=True)
    group_id    = db.Column(db.Integer, db.ForeignKey("groups.id", ondelete="SET NULL"),
                             nullable=True)

    title       = db.Column(db.String(255), nullable=False)
    amount      = db.Column(db.Numeric(12, 2), nullable=False)
    currency    = db.Column(db.String(3), default="PLN", nullable=False)
    type        = db.Column(db.String(10), nullable=False)
    # type: "income" | "expense"

    date        = db.Column(db.DateTime(timezone=True), nullable=False,
                             default=lambda: datetime.now(timezone.utc))
    description = db.Column(db.Text)
    attachment_url = db.Column(db.String(500))

    # Cykliczność
    is_recurring     = db.Column(db.Boolean, default=False)
    recurrence_rule  = db.Column(db.String(50))
    # recurrence_rule: "daily" | "weekly" | "monthly" | "yearly"
    recurrence_end   = db.Column(db.DateTime(timezone=True))
    parent_id        = db.Column(db.Integer, db.ForeignKey("transactions.id",
                                                             ondelete="SET NULL"),
                                  nullable=True)

    created_at  = db.Column(db.DateTime(timezone=True),
                             default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.Index("ix_transactions_user_date", "user_id", "date"),
        db.Index("ix_transactions_user_type", "user_id", "type"),
    )

    def to_dict(self) -> dict:
        return {
            "id":              self.id,
            "user_id":         self.user_id,
            "category_id":     self.category_id,
            "group_id":        self.group_id,
            "title":           self.title,
            "amount":          str(self.amount),
            "currency":        self.currency,
            "type":            self.type,
            "date":            self.date.isoformat() if self.date else None,
            "description":     self.description,
            "is_recurring":    self.is_recurring,
            "recurrence_rule": self.recurrence_rule,
            "created_at":      self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Transaction {self.title} {self.amount} {self.currency}>"

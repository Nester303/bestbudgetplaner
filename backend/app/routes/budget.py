"""
/api/budget — statystyki i podsumowania budżetu

Endpointy:
  GET /api/budget/summary          – saldo, przychody, wydatki za okres
  GET /api/budget/chart            – dane do wykresu (słupkowy / liniowy)
  GET /api/budget/by-category      – wydatki wg kategorii (kołowy)
  GET /api/budget/recurring        – lista cyklicznych transakcji
  GET /api/budget/forecast         – prognoza na kolejne miesiące
"""

from __future__ import annotations

from datetime import datetime, date, timezone
from calendar import monthrange
from decimal import Decimal

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, extract, and_

from ..extensions import db
from ..models.transaction import Transaction
from ..models.models import Category

budget_bp = Blueprint("budget", __name__)


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def _parse_period(args: dict) -> tuple[datetime, datetime]:
    """
    Parsuje query params ?year=2026&month=3 lub ?from=2026-01-01&to=2026-03-31.
    Zwraca (start, end) jako datetime z timezone UTC.
    """
    if "from" in args and "to" in args:
        start = datetime.fromisoformat(args["from"]).replace(tzinfo=timezone.utc)
        end   = datetime.fromisoformat(args["to"]).replace(hour=23, minute=59,
                                                            second=59,
                                                            tzinfo=timezone.utc)
        return start, end

    year  = int(args.get("year",  datetime.now().year))
    month = args.get("month")

    if month:
        month = int(month)
        last_day = monthrange(year, month)[1]
        start = datetime(year, month, 1,  tzinfo=timezone.utc)
        end   = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
    else:
        # Cały rok
        start = datetime(year, 1,  1,  tzinfo=timezone.utc)
        end   = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

    return start, end


def _tx_base(user_id: int, start: datetime, end: datetime):
    """Bazowe query transakcji użytkownika za okres."""
    return Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.date >= start,
        Transaction.date <= end,
    )


# ─────────────────────────────────────────────
#  GET /api/budget/summary
# ─────────────────────────────────────────────

@budget_bp.get("/summary")
@jwt_required()
def summary():
    """
    Zwraca:
      - balance        – saldo (przychody - wydatki)
      - income_total   – suma przychodów
      - expense_total  – suma wydatków
      - vs_prev        – % zmiana względem poprzedniego okresu
      - transaction_count
    Query: ?year=2026&month=3  lub  ?from=...&to=...
    """
    user_id = get_jwt_identity()
    start, end = _parse_period(request.args)

    # Sumy za bieżący okres
    rows = db.session.query(
        Transaction.type,
        func.coalesce(func.sum(Transaction.amount), 0).label("total")
    ).filter(
        Transaction.user_id == user_id,
        Transaction.date >= start,
        Transaction.date <= end,
    ).group_by(Transaction.type).all()

    totals = {r.type: float(r.total) for r in rows}
    income  = totals.get("income",  0.0)
    expense = totals.get("expense", 0.0)
    balance = income - expense

    count = _tx_base(user_id, start, end).count()

    # Porównanie z poprzednim miesiącem (tylko gdy month podany)
    vs_prev = None
    if request.args.get("month"):
        period_days = (end - start).days + 1
        from datetime import timedelta
        prev_end   = start - timedelta(seconds=1)
        prev_start = prev_end - timedelta(days=period_days - 1)
        prev_rows = db.session.query(
            Transaction.type,
            func.coalesce(func.sum(Transaction.amount), 0).label("total")
        ).filter(
            Transaction.user_id == user_id,
            Transaction.date >= prev_start,
            Transaction.date <= prev_end,
        ).group_by(Transaction.type).all()
        prev = {r.type: float(r.total) for r in prev_rows}
        prev_expense = prev.get("expense", 0.0)
        if prev_expense > 0:
            vs_prev = round((expense - prev_expense) / prev_expense * 100, 1)

    return jsonify({
        "period":            {"start": start.date().isoformat(),
                              "end":   end.date().isoformat()},
        "income_total":      round(income,  2),
        "expense_total":     round(expense, 2),
        "balance":           round(balance, 2),
        "transaction_count": count,
        "vs_prev_expense_pct": vs_prev,
    })


# ─────────────────────────────────────────────
#  GET /api/budget/chart
# ─────────────────────────────────────────────

@budget_bp.get("/chart")
@jwt_required()
def chart():
    """
    Dane do wykresu słupkowego przychody vs wydatki.
    Query: ?year=2026&granularity=month  (month | week | day)
    Zwraca tablicę { label, income, expense } posortowaną chronologicznie.
    """
    user_id     = get_jwt_identity()
    year        = int(request.args.get("year", datetime.now().year))
    granularity = request.args.get("granularity", "month")

    start = datetime(year, 1,  1,  tzinfo=timezone.utc)
    end   = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

    if granularity == "month":
        group_expr = extract("month", Transaction.date).label("period")
        label_fn   = lambda p: f"{year}-{int(p):02d}"
        periods    = range(1, 13)
    elif granularity == "week":
        group_expr = extract("week", Transaction.date).label("period")
        label_fn   = lambda p: f"W{int(p)}"
        periods    = range(1, 54)
    else:
        group_expr = extract("day", Transaction.date).label("period")
        label_fn   = lambda p: str(int(p))
        periods    = range(1, 32)

    rows = db.session.query(
        group_expr,
        Transaction.type,
        func.coalesce(func.sum(Transaction.amount), 0).label("total")
    ).filter(
        Transaction.user_id == user_id,
        Transaction.date >= start,
        Transaction.date <= end,
    ).group_by("period", Transaction.type).all()

    # Zbierz do słownika {period: {income: x, expense: y}}
    data: dict[int, dict] = {}
    for row in rows:
        p = int(row.period)
        if p not in data:
            data[p] = {"income": 0.0, "expense": 0.0}
        data[p][row.type] = float(row.total)

    result = []
    for p in periods:
        if p in data or granularity == "month":
            d = data.get(p, {})
            result.append({
                "label":   label_fn(p),
                "income":  round(d.get("income",  0.0), 2),
                "expense": round(d.get("expense", 0.0), 2),
            })

    return jsonify(result)


# ─────────────────────────────────────────────
#  GET /api/budget/by-category
# ─────────────────────────────────────────────

@budget_bp.get("/by-category")
@jwt_required()
def by_category():
    """
    Wydatki (lub przychody) pogrupowane wg kategorii.
    Query: ?year=2026&month=3&type=expense
    Zwraca: [{ category_id, name, color, icon, total, pct }]
    """
    user_id = get_jwt_identity()
    start, end = _parse_period(request.args)
    tx_type = request.args.get("type", "expense")

    rows = db.session.query(
        Transaction.category_id,
        func.coalesce(func.sum(Transaction.amount), 0).label("total")
    ).filter(
        Transaction.user_id == user_id,
        Transaction.type    == tx_type,
        Transaction.date    >= start,
        Transaction.date    <= end,
    ).group_by(Transaction.category_id).order_by(
        func.sum(Transaction.amount).desc()
    ).all()

    grand_total = sum(float(r.total) for r in rows) or 1.0

    result = []
    for row in rows:
        cat = Category.query.get(row.category_id) if row.category_id else None
        result.append({
            "category_id": row.category_id,
            "name":        cat.name  if cat else "Bez kategorii",
            "color":       cat.color if cat else "#888780",
            "icon":        cat.icon  if cat else "more_horiz",
            "total":       round(float(row.total), 2),
            "pct":         round(float(row.total) / grand_total * 100, 1),
        })

    return jsonify(result)


# ─────────────────────────────────────────────
#  GET /api/budget/recurring
# ─────────────────────────────────────────────

@budget_bp.get("/recurring")
@jwt_required()
def recurring():
    """Lista cyklicznych transakcji użytkownika."""
    user_id = get_jwt_identity()
    txs = Transaction.query.filter_by(
        user_id=user_id, is_recurring=True
    ).order_by(Transaction.date.desc()).all()
    return jsonify([t.to_dict() for t in txs])


# ─────────────────────────────────────────────
#  GET /api/budget/forecast
# ─────────────────────────────────────────────

@budget_bp.get("/forecast")
@jwt_required()
def forecast():
    """
    Prosta prognoza budżetu na kolejne N miesięcy
    na podstawie średniej z ostatnich 3 miesięcy.
    Query: ?months=3
    """
    user_id   = get_jwt_identity()
    n_months  = min(int(request.args.get("months", 3)), 12)
    now       = datetime.now(timezone.utc)

    # Dane historyczne — ostatnie 3 miesiące
    from datetime import timedelta
    history_start = (now.replace(day=1) -
                     timedelta(days=1)).replace(day=1).replace(day=1)
    # 3 miesiące wstecz
    y, m = now.year, now.month
    months_back = []
    for i in range(1, 4):
        m -= 1
        if m == 0:
            m = 12; y -= 1
        months_back.append((y, m))

    hist_start = datetime(months_back[-1][0], months_back[-1][1], 1,
                          tzinfo=timezone.utc)
    hist_end   = now

    rows = db.session.query(
        extract("year",  Transaction.date).label("y"),
        extract("month", Transaction.date).label("m"),
        Transaction.type,
        func.sum(Transaction.amount).label("total")
    ).filter(
        Transaction.user_id == user_id,
        Transaction.date    >= hist_start,
        Transaction.date    <= hist_end,
    ).group_by("y", "m", Transaction.type).all()

    by_month: dict[tuple, dict] = {}
    for row in rows:
        key = (int(row.y), int(row.m))
        if key not in by_month:
            by_month[key] = {"income": 0.0, "expense": 0.0}
        by_month[key][row.type] = float(row.total)

    avg_income  = (sum(v["income"]  for v in by_month.values()) /
                   max(len(by_month), 1))
    avg_expense = (sum(v["expense"] for v in by_month.values()) /
                   max(len(by_month), 1))

    forecast_months = []
    fy, fm = now.year, now.month
    for _ in range(n_months):
        fm += 1
        if fm > 12:
            fm = 1; fy += 1
        forecast_months.append({
            "label":   f"{fy}-{fm:02d}",
            "income":  round(avg_income,  2),
            "expense": round(avg_expense, 2),
            "balance": round(avg_income - avg_expense, 2),
        })

    return jsonify({
        "based_on_months": len(by_month),
        "avg_income":      round(avg_income,  2),
        "avg_expense":     round(avg_expense, 2),
        "forecast":        forecast_months,
    })

"""
Seed — domyślne kategorie systemowe.
Uruchom: docker compose exec backend flask seed
"""
import click
from flask import current_app
from app.extensions import db
from app.models.models import Category


SYSTEM_CATEGORIES = [
    # Wydatki
    {"name": "Mieszkanie",      "icon": "home",              "color": "#185FA5", "type": "expense"},
    {"name": "Jedzenie",        "icon": "restaurant",        "color": "#1D9E75", "type": "expense"},
    {"name": "Transport",       "icon": "directions_car",    "color": "#BA7517", "type": "expense"},
    {"name": "Zdrowie",         "icon": "health_and_safety", "color": "#E24B4A", "type": "expense"},
    {"name": "Rozrywka",        "icon": "sports_esports",    "color": "#7F77DD", "type": "expense"},
    {"name": "Ubrania",         "icon": "checkroom",         "color": "#D4537E", "type": "expense"},
    {"name": "Edukacja",        "icon": "school",            "color": "#0F6E56", "type": "expense"},
    {"name": "Subskrypcje",     "icon": "subscriptions",     "color": "#534AB7", "type": "expense"},
    {"name": "Oszczędności",    "icon": "savings",           "color": "#639922", "type": "expense"},
    {"name": "Inne wydatki",    "icon": "more_horiz",        "color": "#888780", "type": "expense"},
    # Przychody
    {"name": "Wynagrodzenie",   "icon": "work",              "color": "#1D9E75", "type": "income"},
    {"name": "Freelance",       "icon": "laptop",            "color": "#185FA5", "type": "income"},
    {"name": "Inwestycje",      "icon": "trending_up",       "color": "#BA7517", "type": "income"},
    {"name": "Inne przychody",  "icon": "attach_money",      "color": "#888780", "type": "income"},
]


def seed_categories():
    existing = {c.name for c in Category.query.filter_by(is_system=True).all()}
    added = 0
    for cat_data in SYSTEM_CATEGORIES:
        if cat_data["name"] not in existing:
            cat = Category(is_system=True, **cat_data)
            db.session.add(cat)
            added += 1
    db.session.commit()
    return added


def register_commands(app):
    @app.cli.command("seed")
    def seed_command():
        """Wypełnij bazę domyślnymi kategoriami."""
        n = seed_categories()
        click.echo(f"Dodano {n} kategorii systemowych.")

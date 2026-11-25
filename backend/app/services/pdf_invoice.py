"""
Serwis generowania PDF faktur przy użyciu ReportLab.
Obsługa polskich znaków przez font DejaVu.
"""

from __future__ import annotations

import io
import os
from datetime import date
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Rejestracja fontów z obsługą polskich znaków ─────────────────
_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]

_FONT_REGISTERED = False

def _register_fonts():
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return True
    regular = None
    bold    = None
    for p in _FONT_PATHS:
        if "Bold" not in p and os.path.exists(p):
            regular = p
        if "Bold" in p and os.path.exists(p):
            bold = p
    if regular:
        try:
            pdfmetrics.registerFont(TTFont("DejaVu",     regular))
            pdfmetrics.registerFont(TTFont("DejaVu-Bold", bold or regular))
            _FONT_REGISTERED = True
            return True
        except Exception:
            pass
    return False

def _font(bold=False):
    if _FONT_REGISTERED:
        return "DejaVu-Bold" if bold else "DejaVu"
    return "Helvetica-Bold" if bold else "Helvetica"


COLOR_PRIMARY   = colors.HexColor("#1a1a1a")
COLOR_SECONDARY = colors.HexColor("#555555")
COLOR_MUTED     = colors.HexColor("#888888")
COLOR_ACCENT    = colors.HexColor("#185FA5")
COLOR_ROW_ALT   = colors.HexColor("#f7f7f7")
COLOR_BORDER    = colors.HexColor("#e0e0e0")
COLOR_HEADER_BG = colors.HexColor("#f0f4f9")


def generate_invoice_pdf(invoice_data: dict) -> bytes:
    _register_fonts()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm,  bottomMargin=20*mm,
    )

    story = []

    # ── Style ─────────────────────────────────────────────────────
    h1 = ParagraphStyle("h1", fontSize=22, textColor=COLOR_ACCENT,
                         fontName=_font(True), spaceAfter=2)
    h2 = ParagraphStyle("h2", fontSize=11, textColor=COLOR_PRIMARY,
                         fontName=_font(True), spaceAfter=4)
    body = ParagraphStyle("body", fontSize=9, textColor=COLOR_PRIMARY,
                           fontName=_font(), leading=14)
    muted = ParagraphStyle("muted", fontSize=8, textColor=COLOR_MUTED,
                            fontName=_font())
    right = ParagraphStyle("right", fontSize=9, textColor=COLOR_PRIMARY,
                            fontName=_font(), alignment=TA_RIGHT)
    bold_s = ParagraphStyle("bold", fontSize=9, textColor=COLOR_PRIMARY,
                             fontName=_font(True))

    # ── Nagłówek ──────────────────────────────────────────────────
    header_data = [[
        Paragraph("FAKTURA VAT", h1),
        Paragraph(f"Nr: <b>{invoice_data.get('number', '')}</b>",
                  ParagraphStyle("nr", fontSize=13, fontName=_font(True),
                                 textColor=COLOR_PRIMARY, alignment=TA_RIGHT)),
    ]]
    header_table = Table(header_data, colWidths=[90*mm, 80*mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(header_table)

    # Daty
    issue = invoice_data.get("issue_date", "")
    due   = invoice_data.get("due_date", "")
    cur   = invoice_data.get("currency", "PLN")
    story.append(Paragraph(
        f"<font color='#888888'>Data wystawienia:</font> {issue} &nbsp;&nbsp; "
        f"<font color='#888888'>Termin płatności:</font> {due} &nbsp;&nbsp; "
        f"<font color='#888888'>Waluta:</font> {cur}",
        ParagraphStyle("dates", fontSize=8, fontName=_font(), textColor=COLOR_SECONDARY)
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_BORDER,
                             spaceAfter=8, spaceBefore=6))

    # ── Sprzedawca / Nabywca ──────────────────────────────────────
    seller = invoice_data.get("seller", {})
    buyer  = invoice_data.get("buyer",  {})

    def addr_block(title, data):
        lines = [Paragraph(title, h2)]
        for k, label in [("name",""), ("nip","NIP: "), ("address",""), ("email","Email: ")]:
            v = data.get(k, "")
            if v:
                for line in str(v).split("\n"):
                    lines.append(Paragraph(f"{label}{line}", body))
        return lines

    parties = Table(
        [[addr_block("Sprzedawca", seller), addr_block("Nabywca", buyer)]],
        colWidths=[85*mm, 85*mm]
    )
    parties.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(parties)
    story.append(Spacer(1, 8*mm))

    # ── Tabela pozycji ────────────────────────────────────────────
    items = invoice_data.get("items", [])
    th_style = ParagraphStyle("th", fontSize=8, fontName=_font(True),
                               textColor=COLOR_PRIMARY, alignment=TA_CENTER)
    td_style = ParagraphStyle("td", fontSize=8, fontName=_font(),
                               textColor=COLOR_PRIMARY)
    td_right = ParagraphStyle("tdr", fontSize=8, fontName=_font(),
                               textColor=COLOR_PRIMARY, alignment=TA_RIGHT)

    table_data = [[
        Paragraph("Lp.",          th_style),
        Paragraph("Nazwa",        th_style),
        Paragraph("Jedn.",        th_style),
        Paragraph("Ilość",        th_style),
        Paragraph("Cena netto",   th_style),
        Paragraph("VAT %",        th_style),
        Paragraph("Kwota VAT",    th_style),
        Paragraph("Brutto",       th_style),
    ]]

    total_net   = Decimal("0")
    total_vat   = Decimal("0")
    total_gross = Decimal("0")

    for i, item in enumerate(items, 1):
        qty        = Decimal(str(item.get("qty", 1)))
        unit_net   = Decimal(str(item.get("unit_price_net", 0)))
        vat_rate   = Decimal(str(item.get("vat_rate", 23))) / 100
        net_val    = qty * unit_net
        vat_val    = net_val * vat_rate
        gross_val  = net_val + vat_val

        total_net   += net_val
        total_vat   += vat_val
        total_gross += gross_val

        bg = COLOR_ROW_ALT if i % 2 == 0 else colors.white
        table_data.append([
            Paragraph(str(i),                   td_style),
            Paragraph(item.get("name", ""),     td_style),
            Paragraph(item.get("unit", "szt."), td_style),
            Paragraph(str(qty.normalize()),     td_right),
            Paragraph(f"{unit_net:.2f}",        td_right),
            Paragraph(f"{int(vat_rate*100)}%",  td_right),
            Paragraph(f"{vat_val:.2f}",         td_right),
            Paragraph(f"{gross_val:.2f}",       td_right),
        ])

    # Suma
    table_data.append([
        Paragraph("", td_style),
        Paragraph("RAZEM", ParagraphStyle("sum", fontSize=9, fontName=_font(True),
                                           textColor=COLOR_PRIMARY)),
        "", "", "",
        Paragraph(f"{total_net:.2f}", td_right),
        Paragraph(f"{total_vat:.2f}", td_right),
        Paragraph(f"{total_gross:.2f} {cur}",
                  ParagraphStyle("sumr", fontSize=9, fontName=_font(True),
                                  textColor=COLOR_ACCENT, alignment=TA_RIGHT)),
    ])

    col_w = [8*mm, 65*mm, 12*mm, 14*mm, 22*mm, 12*mm, 18*mm, 24*mm]
    items_table = Table(table_data, colWidths=col_w)
    items_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  COLOR_HEADER_BG),
        ("GRID",          (0,0), (-1,-1), 0.5, COLOR_BORDER),
        ("ROWBACKGROUNDS",(0,1), (-1,-2), [colors.white, COLOR_ROW_ALT]),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LINEABOVE",     (0,-1), (-1,-1), 1, COLOR_ACCENT),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 6*mm))

    # ── Podsumowanie ──────────────────────────────────────────────
    summary_data = [
        [Paragraph("Netto:",        bold_s), Paragraph(f"{total_net:.2f} {cur}",   right)],
        [Paragraph("VAT:",          bold_s), Paragraph(f"{total_vat:.2f} {cur}",   right)],
        [Paragraph("Do zapłaty:",
                   ParagraphStyle("pay", fontSize=12, fontName=_font(True),
                                  textColor=COLOR_ACCENT)),
         Paragraph(f"{total_gross:.2f} {cur}",
                   ParagraphStyle("payr", fontSize=12, fontName=_font(True),
                                  textColor=COLOR_ACCENT, alignment=TA_RIGHT))],
    ]
    summary_table = Table(summary_data, colWidths=[100*mm, 70*mm],
                           hAlign="RIGHT")
    summary_table.setStyle(TableStyle([
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LINEABOVE",     (0,-1), (-1,-1), 1, COLOR_ACCENT),
    ]))
    story.append(summary_table)

    # ── Uwagi ─────────────────────────────────────────────────────
    notes = invoice_data.get("notes", "")
    if notes:
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph("Uwagi:", h2))
        story.append(Paragraph(str(notes), body))

    # ── Bank ──────────────────────────────────────────────────────
    bank = seller.get("bank_account", "")
    if bank:
        story.append(Spacer(1, 4*mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER,
                                 spaceAfter=4))
        story.append(Paragraph(f"Numer konta: {bank}", muted))

    doc.build(story)
    return buf.getvalue()

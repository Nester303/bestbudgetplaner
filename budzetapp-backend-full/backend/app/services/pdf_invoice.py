"""
Serwis generowania PDF faktur przy użyciu ReportLab.
Tworzy profesjonalną fakturę VAT zgodną z polskimi wymogami.
"""

from __future__ import annotations

import io
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


# ─────────────────────────────────────────────
#  Kolory (paleta neutralna, profesjonalna)
# ─────────────────────────────────────────────
COLOR_PRIMARY   = colors.HexColor("#1a1a1a")
COLOR_SECONDARY = colors.HexColor("#555555")
COLOR_MUTED     = colors.HexColor("#888888")
COLOR_ACCENT    = colors.HexColor("#185FA5")
COLOR_ROW_ALT   = colors.HexColor("#f7f7f7")
COLOR_BORDER    = colors.HexColor("#e0e0e0")
COLOR_HEADER_BG = colors.HexColor("#f0f4f9")


def generate_invoice_pdf(invoice_data: dict) -> bytes:
    """
    Generuje PDF faktury i zwraca jako bytes.

    invoice_data: {
        number, issue_date, due_date, currency,
        seller: { name, nip, address, email, phone, bank_account },
        buyer:  { name, nip, address, email },
        items:  [{ name, qty, unit, unit_price_net, vat_rate }],
        notes,
        payment_method   # 'transfer' | 'cash' | 'card'
    }
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm,  bottomMargin=20*mm,
    )

    styles = getSampleStyleSheet()
    story  = []

    # ── Styles ──────────────────────────────────
    h1 = ParagraphStyle("h1", fontSize=22, textColor=COLOR_ACCENT,
                         fontName="Helvetica-Bold", spaceAfter=2)
    h2 = ParagraphStyle("h2", fontSize=11, textColor=COLOR_PRIMARY,
                         fontName="Helvetica-Bold", spaceAfter=4)
    body = ParagraphStyle("body", fontSize=9, textColor=COLOR_PRIMARY,
                           fontName="Helvetica", leading=14)
    muted = ParagraphStyle("muted", fontSize=8, textColor=COLOR_MUTED,
                            fontName="Helvetica")
    right = ParagraphStyle("right", fontSize=9, textColor=COLOR_PRIMARY,
                            fontName="Helvetica", alignment=TA_RIGHT)
    bold  = ParagraphStyle("bold", fontSize=9, textColor=COLOR_PRIMARY,
                            fontName="Helvetica-Bold")

    # ── Nagłówek: FAKTURA + numer ────────────────
    header_data = [[
        Paragraph("FAKTURA VAT", h1),
        Paragraph(f"Nr: <b>{invoice_data.get('number', '')}</b>",
                  ParagraphStyle("nr", fontSize=13, fontName="Helvetica-Bold",
                                 textColor=COLOR_PRIMARY, alignment=TA_RIGHT)),
    ]]
    header_table = Table(header_data, colWidths=[90*mm, 80*mm])
    header_table.setStyle(TableStyle([
        ("VALIGN",      (0,0), (-1,-1), "BOTTOM"),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_ACCENT,
                              spaceAfter=6))

    # ── Daty ────────────────────────────────────
    issue_date = invoice_data.get("issue_date", date.today().isoformat())
    due_date   = invoice_data.get("due_date",   issue_date)
    payment    = invoice_data.get("payment_method", "transfer")
    payment_pl = {"transfer": "Przelew bankowy", "cash": "Gotówka",
                  "card": "Karta płatnicza"}.get(payment, payment)

    dates_data = [[
        Paragraph(f"Data wystawienia: <b>{issue_date}</b>", body),
        Paragraph(f"Termin płatności: <b>{due_date}</b>",   body),
        Paragraph(f"Forma płatności: <b>{payment_pl}</b>",  body),
    ]]
    dates_table = Table(dates_data, colWidths=[57*mm, 57*mm, 56*mm])
    dates_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), COLOR_HEADER_BG),
        ("PADDING",    (0,0), (-1,-1), 6),
        ("ROUNDEDCORNERS", [3]),
    ]))
    story.append(dates_table)
    story.append(Spacer(1, 6*mm))

    # ── Sprzedawca / Nabywca ─────────────────────
    seller = invoice_data.get("seller", {})
    buyer  = invoice_data.get("buyer",  {})

    def _party_block(label: str, party: dict) -> list:
        lines = [Paragraph(f"<b>{label}</b>", muted)]
        if party.get("name"):
            lines.append(Paragraph(f"<b>{party['name']}</b>", bold))
        if party.get("nip"):
            lines.append(Paragraph(f"NIP: {party['nip']}", body))
        if party.get("address"):
            for line in party["address"].splitlines():
                lines.append(Paragraph(line, body))
        if party.get("email"):
            lines.append(Paragraph(party["email"], muted))
        if party.get("phone"):
            lines.append(Paragraph(party["phone"], muted))
        if party.get("bank_account"):
            lines.append(Paragraph(f"Konto: {party['bank_account']}", muted))
        return lines

    parties_data = [[_party_block("SPRZEDAWCA", seller),
                     _party_block("NABYWCA",    buyer)]]
    parties_table = Table(parties_data, colWidths=[85*mm, 85*mm])
    parties_table.setStyle(TableStyle([
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING",   (0,0), (-1,-1), 8),
        ("BOX",          (0,0), (0,-1),  0.5, COLOR_BORDER),
        ("BOX",          (1,0), (1,-1),  0.5, COLOR_BORDER),
    ]))
    story.append(parties_table)
    story.append(Spacer(1, 6*mm))

    # ── Tabela pozycji ───────────────────────────
    currency = invoice_data.get("currency", "PLN")
    items    = invoice_data.get("items", [])

    # Nagłówek tabeli
    col_headers = [
        Paragraph("Lp.", muted),
        Paragraph("Nazwa towaru/usługi", muted),
        Paragraph("Jedn.", muted),
        Paragraph("Ilość", muted),
        Paragraph(f"Cena netto\n({currency})", muted),
        Paragraph("VAT\n%", muted),
        Paragraph(f"Wartość\nnetto", muted),
        Paragraph(f"VAT\n({currency})", muted),
        Paragraph(f"Brutto\n({currency})", muted),
    ]
    col_widths = [8*mm, 54*mm, 10*mm, 12*mm, 18*mm, 10*mm, 18*mm, 16*mm, 18*mm]

    table_data = [col_headers]

    net_sum = Decimal("0")
    vat_sum = Decimal("0")
    gross_sum = Decimal("0")

    for i, item in enumerate(items, 1):
        qty       = Decimal(str(item.get("qty", 1)))
        unit_net  = Decimal(str(item.get("unit_price_net", 0)))
        vat_rate  = Decimal(str(item.get("vat_rate", 23)))
        net_val   = qty * unit_net
        vat_val   = net_val * vat_rate / 100
        gross_val = net_val + vat_val

        net_sum   += net_val
        vat_sum   += vat_val
        gross_sum += gross_val

        bg = COLOR_ROW_ALT if i % 2 == 0 else colors.white
        row = [
            Paragraph(str(i), body),
            Paragraph(item.get("name", ""), body),
            Paragraph(item.get("unit", "szt."), body),
            Paragraph(f"{qty:g}", body),
            Paragraph(f"{unit_net:.2f}", right),
            Paragraph(f"{vat_rate:g}%", body),
            Paragraph(f"{net_val:.2f}", right),
            Paragraph(f"{vat_val:.2f}", right),
            Paragraph(f"{gross_val:.2f}", right),
        ]
        table_data.append(row)

    # Wiersz sumy
    table_data.append([
        "", Paragraph("<b>RAZEM</b>", bold), "", "", "",
        "",
        Paragraph(f"<b>{net_sum:.2f}</b>",   right),
        Paragraph(f"<b>{vat_sum:.2f}</b>",   right),
        Paragraph(f"<b>{gross_sum:.2f}</b>", right),
    ])

    items_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        # Nagłówek
        ("BACKGROUND",   (0,0), (-1,0), COLOR_HEADER_BG),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,0), 8),
        ("TEXTCOLOR",    (0,0), (-1,0), COLOR_SECONDARY),
        ("BOTTOMPADDING",(0,0), (-1,0), 6),
        ("TOPPADDING",   (0,0), (-1,0), 6),
        # Wiersze danych
        ("FONTSIZE",     (0,1), (-1,-1), 9),
        ("TOPPADDING",   (0,1), (-1,-1), 5),
        ("BOTTOMPADDING",(0,1), (-1,-1), 5),
        # Wiersz sumy
        ("BACKGROUND",   (0,-1), (-1,-1), COLOR_HEADER_BG),
        ("LINEABOVE",    (0,-1), (-1,-1), 0.5, COLOR_ACCENT),
        # Obramowanie
        ("BOX",          (0,0), (-1,-1), 0.5, COLOR_BORDER),
        ("LINEBELOW",    (0,0), (-1,0),  0.5, COLOR_BORDER),
        ("INNERGRID",    (0,0), (-1,-1), 0.3, COLOR_BORDER),
        # Wyrównanie
        ("ALIGN",        (0,0), (0,-1), "CENTER"),
        ("ALIGN",        (4,0), (-1,-1), "RIGHT"),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 6*mm))

    # ── Podsumowanie kwot + słownie ──────────────
    def _amount_words(amount: Decimal) -> str:
        """Uproszczone słowne zapisanie kwoty (PLN)."""
        try:
            from num2words import num2words
            whole = int(amount)
            cents = int((amount - whole) * 100)
            words = num2words(whole, lang="pl") + f" zł {cents:02d}/100"
            return words.capitalize()
        except ImportError:
            return f"{amount:.2f} {currency}"

    summary_data = [
        [Paragraph("Wartość netto:",   body), Paragraph(f"{net_sum:.2f} {currency}",   right)],
        [Paragraph("Podatek VAT:",     body), Paragraph(f"{vat_sum:.2f} {currency}",   right)],
        [Paragraph("<b>Do zapłaty:</b>", bold),
         Paragraph(f"<b>{gross_sum:.2f} {currency}</b>",
                   ParagraphStyle("bigright", fontSize=11, fontName="Helvetica-Bold",
                                  alignment=TA_RIGHT, textColor=COLOR_ACCENT))],
        [Paragraph("Słownie:", muted),
         Paragraph(_amount_words(gross_sum), muted)],
    ]
    summary_table = Table(summary_data, colWidths=[120*mm, 50*mm],
                          hAlign="RIGHT")
    summary_table.setStyle(TableStyle([
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("LINEABOVE",    (0,2), (-1,2),  0.5, COLOR_BORDER),
        ("LINEBELOW",    (0,2), (-1,2),  0.5, COLOR_BORDER),
    ]))
    story.append(summary_table)

    # ── Uwagi ────────────────────────────────────
    notes = invoice_data.get("notes")
    if notes:
        story.append(Spacer(1, 5*mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER))
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph("Uwagi:", muted))
        story.append(Paragraph(notes, body))

    # ── Stopka: podpisy ──────────────────────────
    story.append(Spacer(1, 15*mm))
    sig_data = [[
        Paragraph("_________________________<br/>Wystawił(a)", muted),
        Paragraph("_________________________<br/>Odebrał(a)",  muted),
    ]]
    sig_table = Table(sig_data, colWidths=[85*mm, 85*mm])
    sig_table.setStyle(TableStyle([
        ("ALIGN",  (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    story.append(sig_table)

    # ── Generuj PDF ──────────────────────────────
    doc.build(story)
    return buf.getvalue()

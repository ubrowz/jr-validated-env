#!/usr/bin/env python3
"""
tools/generate_invoice_template.py — JR Anchored owner use only

Generates a blank invoice template (invoice_template.docx) in this folder.
Fill in your real details once and save a personal copy outside the repo.

Usage:
    python3 tools/generate_invoice_template.py
"""

import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "invoice_template.docx")

BLUE  = RGBColor(0x2E, 0x5B, 0xBA)
GREY  = RGBColor(0x70, 0x80, 0xA0)
BLACK = RGBColor(0x1A, 0x1A, 0x2E)


def set_cell_bg(cell, hex_color):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  hex_color)
    tcPr.append(shd)


def no_space(para):
    para.paragraph_format.space_before = Pt(0)
    para.paragraph_format.space_after  = Pt(0)


def add_run(para, text, bold=False, size=10, color=BLACK, italic=False):
    run = para.add_run(text)
    run.bold   = bold
    run.italic = italic
    run.font.size  = Pt(size)
    run.font.color.rgb = color
    return run


doc = Document()

# ── Page margins ──────────────────────────────────────────────────────────────
for section in doc.sections:
    section.top_margin    = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin   = Cm(2.5)
    section.right_margin  = Cm(2.5)

# ── Header table: brand left, invoice meta right ───────────────────────────
tbl = doc.add_table(rows=1, cols=2)
tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
tbl.columns[0].width = Cm(10)
tbl.columns[1].width = Cm(6)

# Left: sender
left = tbl.cell(0, 0)
left.width = Cm(10)
for text, bold, size, color in [
    ("JR Anchored",        True,  14, BLUE),
    ("[YOUR TRADING NAME]", False, 9,  GREY),
    ("[ADDRESS LINE 1]",    False, 9,  GREY),
    ("[POSTCODE  CITY]",    False, 9,  GREY),
    ("[EMAIL ADDRESS]",     False, 9,  GREY),
    ("KvK: [KVK NUMBER]",  False, 9,  GREY),
]:
    p = left.add_paragraph()
    no_space(p)
    add_run(p, text, bold=bold, size=size, color=color)

# Remove auto-added empty first paragraph
left.paragraphs[0]._element.getparent().remove(left.paragraphs[0]._element)

# Right: invoice label
right = tbl.cell(0, 1)
right.width = Cm(6)
p = right.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
no_space(p)
add_run(p, "INVOICE", bold=True, size=20, color=BLUE)

# ── Divider ───────────────────────────────────────────────────────────────────
doc.add_paragraph()
p = doc.add_paragraph()
no_space(p)
p.paragraph_format.space_after = Pt(12)
run = p.add_run("─" * 80)
run.font.color.rgb = RGBColor(0xCC, 0xD4, 0xEE)
run.font.size = Pt(7)

# ── Invoice meta + Bill To ────────────────────────────────────────────────────
meta = doc.add_table(rows=1, cols=2)
meta.alignment = WD_TABLE_ALIGNMENT.LEFT
meta.columns[0].width = Cm(8)
meta.columns[1].width = Cm(8)

ml = meta.cell(0, 0)
mr = meta.cell(0, 1)

for label, value in [
    ("Invoice number", "[INVOICE NUMBER]"),
    ("Date",           "[DD MONTH YYYY]"),
    ("Due date",       "[DD MONTH YYYY]  (14 days)"),
]:
    p = ml.add_paragraph()
    no_space(p)
    p.paragraph_format.space_after = Pt(2)
    add_run(p, f"{label}: ", bold=True, size=9, color=BLACK)
    add_run(p, value, bold=False, size=9, color=GREY)

ml.paragraphs[0]._element.getparent().remove(ml.paragraphs[0]._element)

p = mr.add_paragraph()
no_space(p)
add_run(p, "Bill to", bold=True, size=9, color=BLACK)
mr.paragraphs[0]._element.getparent().remove(mr.paragraphs[0]._element)

for line in ["[BUYER NAME / COMPANY]", "[ADDRESS]", "[CITY, COUNTRY]", "[EMAIL]"]:
    p = mr.add_paragraph()
    no_space(p)
    p.paragraph_format.space_after = Pt(2)
    add_run(p, line, size=9, color=GREY)

# ── Line items table ──────────────────────────────────────────────────────────
doc.add_paragraph()
items = doc.add_table(rows=2, cols=3)
items.alignment = WD_TABLE_ALIGNMENT.LEFT

widths = [Cm(11), Cm(2), Cm(3)]
headers = ["Description", "Qty", "Amount"]

for i, (hdr, w) in enumerate(zip(headers, widths)):
    cell = items.cell(0, i)
    cell.width = w
    set_cell_bg(cell, "2E5BBA")
    p = cell.paragraphs[0]
    no_space(p)
    p.paragraph_format.space_after = Pt(4)
    if i > 0:
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    add_run(p, hdr, bold=True, size=9, color=RGBColor(0xFF, 0xFF, 0xFF))

row = items.rows[1]
contents = [
    "JR Anchored Validation Pack v[VERSION] — perpetual licence, one organisation",
    "1",
    "$ 100.00",
]
for i, (text, w) in enumerate(zip(contents, widths)):
    cell = row.cells[i]
    cell.width = w
    p = cell.paragraphs[0]
    no_space(p)
    p.paragraph_format.space_after  = Pt(4)
    p.paragraph_format.space_before = Pt(4)
    if i > 0:
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    add_run(p, text, size=9, color=BLACK)

# ── Total ─────────────────────────────────────────────────────────────────────
doc.add_paragraph()
totals = doc.add_table(rows=2, cols=2)
totals.alignment = WD_TABLE_ALIGNMENT.LEFT
for r, (label, value) in enumerate([
    ("VAT", "Exempt (KOR)"),
    ("Total due", "$ 100.00"),
]):
    lc = totals.cell(r, 0)
    vc = totals.cell(r, 1)
    lc.width = Cm(13)
    vc.width = Cm(3)
    pl = lc.paragraphs[0]
    pv = vc.paragraphs[0]
    no_space(pl); no_space(pv)
    pv.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    bold = (r == 1)
    add_run(pl, label, bold=bold, size=9, color=BLACK if bold else GREY)
    add_run(pv, value, bold=bold, size=9, color=BLACK if bold else GREY)

# ── Payment details ───────────────────────────────────────────────────────────
doc.add_paragraph()
p = doc.add_paragraph()
no_space(p)
p.paragraph_format.space_before = Pt(10)
add_run(p, "Payment", bold=True, size=9, color=BLUE)

for label, value in [
    ("IBAN",      "[IBAN]"),
    ("BIC",       "[BIC]"),
    ("Reference", "Invoice [INVOICE NUMBER]"),
]:
    p = doc.add_paragraph()
    no_space(p)
    p.paragraph_format.space_after = Pt(2)
    add_run(p, f"{label}: ", bold=True, size=9, color=BLACK)
    add_run(p, value, size=9, color=GREY)

# ── Footer note ───────────────────────────────────────────────────────────────
doc.add_paragraph()
p = doc.add_paragraph()
no_space(p)
p.paragraph_format.space_before = Pt(16)
add_run(p, "BTW vrijgesteld op grond van de kleineondernemersregeling (KOR).",
        size=8, color=GREY, italic=True)

doc.save(OUT)
print(f"✅  Invoice template written to: {OUT}")

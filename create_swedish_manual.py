#!/usr/bin/env python3
# create_swedish_manual.py
# Kräver: pip install pymupdf reportlab

import sys
import os
import textwrap
from io import BytesIO
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

def main(in_pdf, out_pdf, text_file):
    if not os.path.exists(in_pdf):
        print("Fel: Original-PDF hittades inte:", in_pdf)
        return
    if not os.path.exists(text_file):
        print("Fel: Textfil med översättning hittades inte:", text_file)
        return

    # Läs in text från fil
    with open(text_file, "r", encoding="utf-8") as f:
        swedish_text = f.read()

    doc = fitz.open(in_pdf)
    num_pages = doc.page_count

    wrapped = textwrap.wrap(swedish_text, width=90)
    lines_per_page = 48
    pages_lines = [wrapped[i:i+lines_per_page] for i in range(0, len(wrapped), lines_per_page)]

    width, height = A4
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)

    for i in range(num_pages):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=fitz.Matrix(2,2))
        img_bytes = pix.tobytes("png")
        img_io = BytesIO(img_bytes)
        c.drawImage(ImageReader(img_io), 0, 0, width=width, height=height)

        if i < len(pages_lines):
            lines = pages_lines[i]
        else:
            lines = []

        c.setFillColorRGB(1,1,1)
        c.rect(40, 60, width-80, height-120, fill=1, stroke=0)
        c.setFillColorRGB(0,0,0)
        c.setFont("Helvetica", 9)
        y = height - 80
        for line in lines:
            c.drawString(50, y, line)
            y -= 12
            if y < 70:
                break
        c.showPage()

    for j in range(len(pages_lines) - num_pages):
        idx = num_pages + j
        c.setFillColorRGB(1,1,1)
        c.rect(0,0,width,height,fill=1,stroke=0)
        c.setFillColorRGB(0,0,0)
        c.setFont("Helvetica", 9)
        y = height - 60
        for line in pages_lines[idx]:
            c.drawString(40, y, line)
            y -= 12
            if y < 40:
                c.showPage()
                y = height - 60
        c.showPage()

    c.save()
    packet.seek(0)
    with open(out_pdf, "wb") as f:
        f.write(packet.getvalue())
    print("Klar! Skapad:", out_pdf)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python create_swedish_manual.py input.pdf output.pdf text.txt")
    else:
        main(sys.argv[1], sys.argv[2], sys.argv[3])

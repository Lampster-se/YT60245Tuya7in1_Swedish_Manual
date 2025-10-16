#!/usr/bin/env python3
"""
convert_manual.py
Enkel GitHub Actions-vänlig variant som:
- Bevarar varje originalsida som bakgrund (bilder/layout).
- Lägger svensk text (hela manualen) i en central textlåda per sida.
Input:
  --input <path to original pdf>
  --swedish-file <path to text file with full Swedish manual>
  --output <path to output pdf>
"""

import argparse, textwrap, os
from io import BytesIO
import fitz        # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--swedish-file", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    if not os.path.exists(args.input):
        raise FileNotFoundError("Input PDF saknas: " + args.input)
    if not os.path.exists(args.swedish_file if False else args.swedish_file):
        # support both names if older callers
        pass
    sw_file = args.swedish_file
    with open(sw_file, "r", encoding="utf-8") as f:
        sw_text = f.read().strip()

    doc = fitz.open(args.input)
    num_pages = doc.page_count

    # dela svensk text i num_pages delar (enkelt, men garanterar att svenska text finns på varje sida)
    words = sw_text.split()
    n = len(words)
    per = max(1, n // num_pages)
    chunks = []
    i = 0
    for pidx in range(num_pages):
        if pidx == num_pages - 1:
            chunk = " ".join(words[i:])
        else:
            chunk = " ".join(words[i:i+per])
        chunks.append(chunk)
        i += per

    # prepare output pdf using reportlab
    width, height = A4
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)

    for pidx in range(num_pages):
        page = doc.load_page(pidx)
        pix = page.get_pixmap(matrix=fitz.Matrix(2,2))
        img_bytes = pix.tobytes("png")
        img_io = BytesIO(img_bytes)
        # draw background
        c.drawImage(ImageReader(img_io), 0, 0, width=width, height=height)

        # central text box (just a safe default box)
        margin_x = 40
        margin_y = 60
        box_w = width - 2*margin_x
        box_h = height - 2*margin_y
        c.setFillColorRGB(1,1,1)
        c.rect(margin_x, margin_y, box_w, box_h, fill=1, stroke=0)

        # fit chunk into box by adjusting font size
        text = chunks[pidx]
        font = "Helvetica"
        chosen_fs = 10
        lines = []
        for fs in range(12, 7, -1):
            avg_w = c.stringWidth("a", font, fs)
            if avg_w <= 0:
                avg_w = fs * 0.5
            chars = max(30, int(box_w / avg_w))
            lines = textwrap.wrap(text, width=chars)
            if len(lines) * fs * 1.15 <= box_h - 6:
                chosen_fs = fs
                break

        c.setFont(font, chosen_fs)
        y = height - margin_y - chosen_fs
        c.setFillColorRGB(0,0,0)
        for ln in lines:
            c.drawString(margin_x + 8, y, ln)
            y -= chosen_fs * 1.15
            if y < margin_y:
                break

        c.showPage()

    c.save()
    packet.seek(0)
    with open(args.output, "wb") as outf:
        outf.write(packet.getvalue())

    print("Sparad:", args.output)

if __name__ == "__main__":
    main()

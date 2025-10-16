#!/usr/bin/env python3
"""
convert_manual.py  (uppdaterad blockvis version)

Ersätter text i original-PDF block-för-block med svensk text.
Bevarar layout, bilder, logotyper och sidnummer.
"""

import argparse, os, re, textwrap
from io import BytesIO
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth

def split_into_paragraphs(text):
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    parts = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()!='']
    paras = []
    for p in parts:
        lines = [ln.rstrip() for ln in p.split('\n') if ln.strip()!='']
        if all(ln.lstrip().startswith('-') or re.match(r'^\d+\.', ln.lstrip()) for ln in lines) and len(lines) > 1:
            paras.extend(lines)
        else:
            paras.append(" ".join(lines))
    return paras

def get_blocks_for_page(page):
    blocks = page.get_text("blocks")
    meaningful = [b for b in blocks if b[4].strip()!='']
    meaningful.sort(key=lambda b: (b[1], b[0]))
    return meaningful

def fit_text_to_box(text, box_w, box_h, font_name="Helvetica", max_fs=12, min_fs=6):
    for fs in range(max_fs, min_fs-1, -1):
        avg_w = stringWidth("a", font_name, fs)
        chars_per_line = max(6, int(box_w / max(avg_w, 1)))
        wrapped = textwrap.wrap(text, width=chars_per_line)
        needed_h = len(wrapped) * fs * 1.15
        if needed_h <= box_h - 2:
            return fs, wrapped
    fs = min_fs
    avg_w = stringWidth("a", font_name, fs)
    chars_per_line = max(6, int(box_w / max(avg_w, 1)))
    wrapped = textwrap.wrap(text, width=chars_per_line)
    return fs, wrapped

def fitz_bbox_to_reportlab(bbox, page_rect, a4_width, a4_height):
    x0, y0, x1, y1 = bbox
    rel_x0 = x0 / page_rect.width
    rel_x1 = x1 / page_rect.width
    rel_y0 = y0 / page_rect.height
    rel_y1 = y1 / page_rect.height
    bx = rel_x0 * a4_width
    by = a4_height - (rel_y1 * a4_height)
    bx1 = rel_x1 * a4_width
    by1 = a4_height - (rel_y0 * a4_height)
    return bx, by, bx1, by1

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--swedish-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if not os.path.exists(args.input):
        raise FileNotFoundError("Input PDF saknas: " + args.input)
    if not os.path.exists(args.swedish_file):
        raise FileNotFoundError("Svensk textfil saknas: " + args.swedish_file)

    with open(args.swedish_file, "r", encoding="utf-8") as f:
        sw_text = f.read().strip()

    paras = split_into_paragraphs(sw_text)
    doc = fitz.open(args.input)
    num_pages = doc.page_count

    all_blocks = []
    for p in range(num_pages):
        page = doc.load_page(p)
        blocks = get_blocks_for_page(page)
        if not blocks:
            r = page.rect
            fallback = (r.width*0.08, r.height*0.12, r.width*0.92, r.height*0.88, "fallback")
            blocks = [fallback]
        for b in blocks:
            all_blocks.append((p, b))

    mapped = []
    p_idx = 0
    for i, (page_index, block) in enumerate(all_blocks):
        text = paras[p_idx] if p_idx < len(paras) else ""
        mapped.append((page_index, block, text))
        p_idx += 1
    if p_idx < len(paras):
        rest = " ".join(paras[p_idx:])
        last = mapped[-1]
        mapped[-1] = (last[0], last[1], (last[2] + " " + rest).strip())

    a4_w, a4_h = A4
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    mapped_by_page = {}
    for page_index, block, text in mapped:
        mapped_by_page.setdefault(page_index, []).append((block, text))

    for p in range(num_pages):
        page = doc.load_page(p)
        pix = page.get_pixmap(matrix=fitz.Matrix(2,2))
        img_io = BytesIO(pix.tobytes("png"))
        c.drawImage(ImageReader(img_io), 0, 0, width=a4_w, height=a4_h)

        blocks_here = mapped_by_page.get(p, [])
        for block, text in blocks_here:
            if not text.strip():
                continue
            bx, by, bx1, by1 = fitz_bbox_to_reportlab(block[:4], page.rect, a4_w, a4_h)
            box_w, box_h = max(10, bx1 - bx), max(10, by1 - by)
            c.setFillColorRGB(1,1,1)
            c.rect(bx, by, box_w, box_h, fill=1, stroke=0)
            is_heading = (text.strip().upper() == text.strip() and len(text.strip()) < 60)
            if is_heading:
                fs = 16
                c.setFont("Helvetica-Bold", fs)
                tw = c.stringWidth(text.strip(), "Helvetica-Bold", fs)
                tx = bx + (box_w - tw)/2
                ty = by + box_h - fs - 2
                c.setFillColorRGB(0,0,0)
                c.drawString(tx, ty, text.strip())
                continue
            fs, wrapped = fit_text_to_box(text, box_w, box_h)
            c.setFont("Helvetica", fs)
            y = by + box_h - fs - 2
            c.setFillColorRGB(0,0,0)
            for ln in wrapped:
                if ln.startswith("-"):
                    bullet = u"\u2022"
                    ln_text = ln.lstrip("-").strip()
                    c.drawString(bx + 6, y, bullet + " " + ln_text)
                else:
                    c.drawString(bx + 2, y, ln)
                y -= fs * 1.15
                if y < by + 2:
                    break
        c.showPage()

    c.save()
    packet.seek(0)
    with open(args.output, "wb") as f:
        f.write(packet.getvalue())

    print(f"✅ Sparad: {args.output}")

if __name__ == "__main__":
    main()

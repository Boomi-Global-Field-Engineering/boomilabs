#!/usr/bin/env python3
"""Parse a Boomi Labs Word document into typed blocks + extracted images.

Usage:  python3 -I parse_docx.py <lab.docx> <labs/lab-id>

Writes <labs/lab-id>/blocks.json and <labs/lab-id>/images/exN/imageNN.<ext>.
Standard library only. Deterministic: the same docx always yields the same output.
"""
import json, os, re, shutil, sys, zipfile, html
import xml.etree.ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
V = "urn:schemas-microsoft-com:vml"


def q(ns, local): return f"{{{ns}}}{local}"


STYLE_MAP = {
    "heading1": "h1", "heading2": "h2", "heading3": "h3", "title": "h1",
    "labstep": "step_title", "labcode": "code_block",
    "labinfo": "callout_info", "labtip": "callout_tip", "labwarning": "callout_warning", "labimportant": "callout_important",
    "listbullet": "ul", "listnumber": "ol", "listparagraph": "li",
}
CALLOUT_PREFIX = re.compile(r"^\s*(ℹ️|💡|⚠️|🚨|ℹ|⚠)\s*")


def norm_style(name): return re.sub(r"[^a-z0-9]", "", (name or "normal").lower())


def main(docx, out):
    z = zipfile.ZipFile(docx)
    doc = ET.fromstring(z.read("word/document.xml"))
    rels = ET.fromstring(z.read("word/_rels/document.xml.rels"))
    styles_xml = ET.fromstring(z.read("word/styles.xml")) if "word/styles.xml" in z.namelist() else None
    # styleId -> display name (template styles are referenced by id, e.g. "LabStep")
    style_names = {}
    if styles_xml is not None:
        for st in styles_xml.findall(q(W, "style")):
            nm = st.find(q(W, "name"))
            if nm is not None: style_names[st.get(q(W, "styleId"))] = nm.get(q(W, "val"))
    img_rel = {r.get("Id"): r.get("Target") for r in rels if "image" in (r.get("Type") or "")}

    def pstyle(p):
        ppr = p.find(q(W, "pPr"))
        if ppr is None: return "Normal"
        ps = ppr.find(q(W, "pStyle"))
        if ps is None:
            return "ListParagraph" if ppr.find(q(W, "numPr")) is not None else "Normal"
        sid = ps.get(q(W, "val")); return style_names.get(sid, sid)

    def is_numbered(p):
        ppr = p.find(q(W, "pPr"))
        if ppr is None: return None
        numpr = ppr.find(q(W, "numPr"))
        if numpr is None: return None
        return "ol"  # numbering definitions are not inspected; bullets come through List Bullet style

    def runs_html(p):
        parts = []
        for r in p.iter(q(W, "r")):
            rpr = r.find(q(W, "rPr"))
            text = "".join((t.text or "") for t in r.findall(q(W, "t")))
            if r.find(q(W, "br")) is not None: text += "\n"
            if not text: continue
            text = html.escape(text, quote=False)
            bold = rpr is not None and rpr.find(q(W, "b")) is not None and (rpr.find(q(W, "b")).get(q(W, "val")) not in ("0", "false"))
            ital = rpr is not None and rpr.find(q(W, "i")) is not None and (rpr.find(q(W, "i")).get(q(W, "val")) not in ("0", "false"))
            fonts = rpr.find(q(W, "rFonts")) if rpr is not None else None
            mono = fonts is not None and any("mono" in (fonts.get(q(W, k)) or "").lower() or "consolas" in (fonts.get(q(W, k)) or "").lower() or "courier" in (fonts.get(q(W, k)) or "").lower() for k in ("ascii", "hAnsi"))
            rstyle = rpr.find(q(W, "rStyle")) if rpr is not None else None
            if rstyle is not None and "code" in (style_names.get(rstyle.get(q(W, "val")), rstyle.get(q(W, "val"))) or "").lower(): mono = True
            if mono: text = f"<code>{text}</code>"
            if bold: text = f"<strong>{text}</strong>"
            if ital: text = f"<em>{text}</em>"
            parts.append(text)
        s = "".join(parts)
        # merge adjacent identical tags produced by split runs
        for t in ("strong", "em", "code"): s = s.replace(f"</{t}><{t}>", "")
        return s.strip()

    def images_in(p):
        out = []
        for blip in p.iter(q(A, "blip")):
            rid = blip.get(q(R, "embed"))
            if rid in img_rel: out.append(img_rel[rid])
        for im in p.iter(q(V, "imagedata")):
            rid = im.get(q(R, "id"))
            if rid in img_rel: out.append(img_rel[rid])
        return out

    blocks, meta_done, exercise_no, img_no = [], False, 0, 0
    os.makedirs(out, exist_ok=True)

    def add_image(target, alt):
        nonlocal img_no
        img_no += 1
        ext = os.path.splitext(target)[1].lower() or ".png"
        exn = max(exercise_no, 1)
        folder = os.path.join(out, "images", f"ex{exn}"); os.makedirs(folder, exist_ok=True)
        dst = os.path.join(folder, f"image{img_no:02d}{ext}")
        try:
            with z.open("word/" + target.lstrip("/")) as src, open(dst, "wb") as f: shutil.copyfileobj(src, f)
            blocks.append({"type": "image", "src": os.path.relpath(dst, out).replace(os.sep, "/"), "alt": alt})
        except KeyError:
            blocks.append({"type": "comment", "text": f"image missing: {target}"})

    body = doc.find(q(W, "body"))
    last_text = ""
    for el in body:
        if el.tag == q(W, "tbl"):
            rows = []
            for tr in el.findall(q(W, "tr")):
                rows.append([" ".join(runs_html(p) for p in tc.findall(q(W, "p"))).strip() for tc in tr.findall(q(W, "tc"))])
            first = re.sub(r"<[^>]+>", "", rows[0][0]).strip().lower() if rows and rows[0] else ""
            if not meta_done and any(b["type"] == "h1" for b in blocks) and first in ("field", "key", "metadata"):
                blocks.append({"type": "meta", "rows": rows[1:]}); meta_done = True
            else:
                blocks.append({"type": "table", "rows": rows})
            continue
        if el.tag != q(W, "p"): continue
        style = norm_style(pstyle(el)); kind = STYLE_MAP.get(style)
        text = runs_html(el)
        imgs = images_in(el)
        if text:
            if kind == "h1": blocks.append({"type": "h1", "text": text})
            elif kind == "h2":
                plain = re.sub(r"<[^>]+>", "", text).strip().lower()
                if not re.match(r"(prerequisites|before you begin|what you.ll learn|introduction|about|overview|lab metadata|document structure|special content)", plain):
                    exercise_no += 1
                blocks.append({"type": "h2", "text": text})
            elif kind in ("h3", "step_title"): blocks.append({"type": "h3", "text": text})
            elif kind == "code_block":
                if blocks and blocks[-1]["type"] == "code_block": blocks[-1]["text"] += "\n" + text
                else: blocks.append({"type": "code_block", "text": text})
            elif kind and kind.startswith("callout_"): blocks.append({"type": kind, "text": CALLOUT_PREFIX.sub("", text)})
            elif kind in ("ul", "ol", "li") or is_numbered(el):
                lst = "ol" if (kind == "ol" or (kind == "li" and is_numbered(el))) else "ul"
                blocks.append({"type": "body", "text": re.sub(r"^\s*[•\-\*]\s*", "", text), "list": lst})
            else:
                m = re.match(r"^\s*(\d+)[.)]\s+(.*)", text)
                if m: blocks.append({"type": "step", "text": m.group(2)})
                elif re.match(r"^\s*[•\-\*]\s+", text): blocks.append({"type": "body", "text": re.sub(r"^\s*[•\-\*]\s+", "", text), "list": "ul"})
                else: blocks.append({"type": "body", "text": text})
            last_text = re.sub(r"<[^>]+>", "", text)
        for target in imgs:
            alt = last_text[:120] if last_text and len(last_text) < 120 else ""
            add_image(target, alt)

    with open(os.path.join(out, "blocks.json"), "w", encoding="utf-8") as f: json.dump(blocks, f, ensure_ascii=False, indent=1)
    meta = next((b for b in blocks if b["type"] == "meta"), None)
    print(f"blocks: {len(blocks)}  exercises: {exercise_no}  images: {img_no}")
    print("metadata:", json.dumps(dict((r[0], r[1]) for r in meta["rows"] if len(r) >= 2), ensure_ascii=False) if meta else "NOT FOUND — add the Field/Value table under the title")


if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])

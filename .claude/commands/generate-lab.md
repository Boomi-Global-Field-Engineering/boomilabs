# Generate Lab Guide

Convert a Word document (authored with the Boomi Labs template) into a complete HTML lab guide and publish it to this site.

## Usage

```
/generate-lab <path-to-docx>  [--lab-id <slug>]
```

- `<path-to-docx>` — required. Absolute or relative path to the `.docx` file.
- `--lab-id <slug>` — optional. Directory slug under `labs/`. Defaults to the docx filename (spaces → hyphens, lowercase).

## What this skill does

1. Parses the Word document for lab metadata, exercises, steps, and images
2. Creates `labs/<lab-id>/` with `index.html` + `exercise-N.html` for every exercise
3. Extracts embedded images to `labs/<lab-id>/images/exN/`
4. Adds a card to the root `index.html` catalog (if not already present)
5. Commits all new files to git

---

## Step-by-step instructions

### 1 — Parse the DOCX

Write a Python script (inline via `python3 -c` or a temp file) using only stdlib (`zipfile`, `xml.etree.ElementTree`):

```python
import zipfile, xml.etree.ElementTree as ET, re, os, shutil, json

DOCX = "<path-to-docx>"          # fill in at runtime
OUT  = "labs/<lab-id>"           # fill in at runtime

W  = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R  = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
RP = "http://schemas.openxmlformats.org/package/2006/relationships"

def tag(ns, local): return f"{{{ns}}}{local}"

with zipfile.ZipFile(DOCX) as z:
    doc_xml  = ET.fromstring(z.read("word/document.xml"))
    rels_xml = ET.fromstring(z.read("word/_rels/document.xml.rels"))
    # build rId → target map for images
    img_map = {}
    for rel in rels_xml:
        if "image" in rel.get("Type",""):
            img_map[rel.get("Id")] = rel.get("Target")

    # extract all images from word/media/
    os.makedirs(f"{OUT}/images", exist_ok=True)
    for name in z.namelist():
        if name.startswith("word/media/"):
            fname = os.path.basename(name)
            with z.open(name) as src, open(f"{OUT}/images/{fname}", "wb") as dst:
                shutil.copyfileobj(src, dst)

    body = doc_xml.find(f".//{tag(W,'body')}")
    paragraphs = list(body)
```

Walk the paragraphs and collect structured data. Each paragraph has a style name (read from `w:pPr/w:pStyle/@w:val`) and text runs. Build a list of "blocks":

```python
def para_style(p):
    pPr = p.find(tag(W,"pPr"))
    if pPr is None: return "Normal"
    ps  = pPr.find(tag(W,"pStyle"))
    return ps.get(tag(W,"val")) if ps is not None else "Normal"

def para_text(p, bold_wrap=True):
    parts = []
    for r in p.findall(f".//{tag(W,'r')}"):
        rpr  = r.find(tag(W,"rPr"))
        text = "".join(t.text or "" for t in r.findall(tag(W,"t")))
        if not text: continue
        is_bold   = rpr is not None and rpr.find(tag(W,"b")) is not None
        is_italic = rpr is not None and rpr.find(tag(W,"i")) is not None
        is_code   = rpr is not None and (
            rpr.find(tag(W,"rFonts")) is not None and
            "Mono" in (rpr.find(tag(W,"rFonts")).get(tag(W,"ascii"),"") or "")
        )
        if is_code:   text = f"<code>{text}</code>"
        elif is_bold: text = f"<strong>{text}</strong>"
        elif is_italic: text = f"<em>{text}</em>"
        parts.append(text)
    return "".join(parts)

def inline_images(p):
    rids = []
    for blip in p.findall(f".//{tag('http://schemas.openxmlformats.org/drawingml/2006/main','blip')}"):
        rid = blip.get(tag(R,"embed"))
        if rid and rid in img_map:
            rids.append(img_map[rid])
    return rids
```

**Style → block type mapping** (these are the styles defined in the Word template):

| Word Style Name | Block type |
|---|---|
| `Heading1` | `h1` — Lab title (appears once) |
| `Heading2` | `h2` — Exercise title |
| `Heading3` | `h3` — Step title (within an exercise) |
| `LabStep`  | `step` — Numbered instruction paragraph |
| `LabCode`  | `code_block` — Monospace code/value block |
| `LabInfo`  | `callout_info` |
| `LabTip`   | `callout_tip` |
| `LabWarning` | `callout_warning` |
| `LabImportant` | `callout_important` |
| `Normal` / `ListParagraph` | `body` — Regular paragraph or list item |
| Table | `table` — Metadata, credentials, mapping, or defaults table |

Also look for inline images attached to any paragraph and emit them as `image` blocks immediately after the paragraph.

Build a flat list like:
```python
blocks = [
    {"type": "h1",    "text": "..."},
    {"type": "meta",  "table": [["Key","Value"],...]},   # first table after h1
    {"type": "h2",    "text": "Exercise 1 — ..."},
    {"type": "h3",    "text": "Step 1 — ..."},
    {"type": "step",  "text": "..."},
    {"type": "body",  "text": "..."},
    {"type": "image", "src":  "images/exN/imageNN.png", "alt": ""},
    {"type": "callout_info", "text": "..."},
    ...
]
```

### 2 — Extract metadata

The metadata table (first table in the document, immediately after the `Heading1`) has rows of `[Key, Value]`. Extract:

- `Title` → lab title
- `Description` → lab description  
- `Duration` → e.g. "~2 hours"
- `Level` → e.g. "Intermediate"
- `Tags` → comma-separated tags
- `Product` → e.g. "Boomi for SAP"

### 3 — Segment into exercises and steps

Walk the block list and partition on `h2` boundaries (each `h2` = one exercise). Within each exercise, partition on `h3` boundaries (each `h3` = one step). The first group before the first `h3` becomes the **Overview** page for that exercise.

```
Exercise 1 (h2)
  Overview  ← blocks before first h3
  Step 1    ← blocks between h3[0] and h3[1]
  Step 2    ← ...
Exercise 2 (h2)
  ...
```

### 4 — Assign images per exercise

Rename extracted images into per-exercise folders:

```
labs/<lab-id>/images/ex1/image01.png
labs/<lab-id>/images/ex2/image01.png
...
```

Track which images belong to which exercise by counting them in document order as you encounter `image` blocks during segmentation. The first image encountered in Exercise 1 = `ex1/image01.png`, etc.

### 5 — Generate exercise HTML files

For each exercise, generate `labs/<lab-id>/exercise-N.html` following **exactly** this structure (adapt from the existing exercises):

```html
<!DOCTYPE html>
<html lang="en" data-lab-id="exercise-N">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{step_title} — {lab_title} — Boomi Labs</title>
<link rel="stylesheet" href="../../assets/css/lab.css">
</head>
<body>

<header class="lab-header">
  <a href="../../index.html" class="lab-header-logo">
    <img src="../../assets/img/boomi-logo-reversed.svg" alt="Boomi" height="22" style="vertical-align:middle">
    <span style="font-weight:700;letter-spacing:-.2px">Labs</span>
  </a>
  <div class="lab-header-sep"></div>
  <span class="lab-header-title">{lab_title} — Exercise N</span>
  <div class="lab-header-actions">
    <button class="btn-icon" id="menuBtn" title="Toggle menu" aria-label="Toggle menu">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
    </button>
  </div>
</header>

<div class="lab-layout">

  <nav class="lab-sidebar">
    <div class="sidebar-progress">
      <div class="progress-label">
        <span>Progress</span>
        <span class="progress-pct">0%</span>
      </div>
      <div class="progress-bar"><div class="progress-fill" style="width:0%"></div></div>
    </div>
    <div class="sidebar-divider"></div>
    <div class="sidebar-section-label">Steps</div>
    <ul class="sidebar-nav">
      <!-- one <li> per page (Overview + each step) -->
      <li>
        <a href="#step-0" data-step="0">
          <span class="step-num">
            <span class="step-num-inner">1</span>
            <svg class="step-check" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
          </span>
          Overview
        </a>
      </li>
      <!-- repeat for each step: label = "Step K of N" -->
    </ul>
    <div class="sidebar-divider"></div>
    <div class="sidebar-meta">
      <div class="meta-item">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        Duration: {exercise_duration}
      </div>
      <div class="meta-item">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
        Level: {level}
      </div>
    </div>
  </nav>

  <main class="lab-main">
  <!-- one <section class="step-page" id="page-K"> per page -->
  <section class="step-page" id="page-0">
    <div class="step-content">
      <header class="step-header">
        <div class="step-label">Overview</div>
        <h1 class="step-title">{exercise_title}</h1>
      </header>
      <!-- overview body blocks -->
      <nav class="step-nav">
        <button class="step-nav-btn" id="prevBtn">← Back</button>
        <button class="mark-done-btn" id="markDoneBtn">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 8 12 12 14.5 14.5"/></svg>
          Mark complete
        </button>
        <button class="step-nav-btn primary" id="nextBtn">Next →</button>
      </nav>
    </div>
  </section>
  <!-- ... more step sections ... -->
  </main>

</div>

<script src="../../assets/js/lab.js"></script>
</body>
</html>
```

**Important rules for exercise HTML:**

- `data-lab-id` on `<html>` must be `exercise-N` (e.g., `exercise-1`)
- Every `.step-page` must have `id="page-K"` (0-indexed)
- Every nav button set must use exactly `id="prevBtn"`, `id="markDoneBtn"`, `id="nextBtn"` — one set per page (JS queries within the active page, so duplicate IDs are fine)
- The `<script>` tag must be at the very end of `<body>`, pointing to `../../assets/js/lab.js`
- Step label for page-0 is `"Overview"`, for page-K (K≥1) is `"Step K of N"` where N = total step count

**Block → HTML rendering rules:**

| Block type | HTML output |
|---|---|
| `body` (plain paragraph) | `<p>…</p>` |
| `body` (list item — detected by leading `•`, `-`, or `*`) | wrap in `<ul><li>…</li></ul>`, merge consecutive list items |
| `body` (numbered list — leading `1.`, `2.`, etc.) | `<ol><li>…</li></ol>`, merge consecutive |
| `step` | `<div class="instruction-list"><div class="instruction-num">K</div><div class="instruction-body"><p>…</p></div></div>` — auto-number within each step page |
| `code_block` | `<pre class="code-block"><code>…</code></pre>` |
| `image` | `<figure><img src="{src}" alt="{alt}" class="step-img" style="max-width:100%;border-radius:6px;border:1px solid var(--border);margin:16px 0"></figure>` |
| `callout_info` | `<div class="callout info"><span class="callout-icon">ℹ️ SVG</span><div>…</div></div>` |
| `callout_tip` | `<div class="callout success">…</div>` |
| `callout_warning` | `<div class="callout warning">…</div>` |
| `callout_important` | `<div class="callout danger">…</div>` |
| `table` (credentials) | `<div class="credentials-box">…</div>` — detect by first column header = "Field" or "Credential" |
| `table` (mapping) | `<table class="mapping-table">…</table>` — detect by first column header = "Source" or "From" |
| `table` (defaults) | `<table class="mapping-table">…</table>` — any other table |

**Callout SVG icons** (copy these exactly):

- info: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`
- tip/success: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>`
- warning: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`
- important/danger: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`

### 6 — Generate the lab index page

Create `labs/<lab-id>/index.html` following the pattern of `labs/boomi-for-sap/index.html`:

- Workshop hero with title, description, badges (duration, level, N exercises)
- Exercise list — one item per exercise (number, title, description, duration, step count)
- Prerequisites section — include any prerequisite block from the document (look for `h2` with text "Prerequisites" or "Before you begin")
- Lab Details aside — products covered (from metadata `Product`), integration patterns (from metadata `Tags`), total duration, level

Asset paths use `../../assets/...`.

### 7 — Update the catalog `index.html`

Open `index.html` at the repo root. Find the `<div class="catalog-grid">` block. Before the closing `</div>`, append a new lab card:

```html
<a href="labs/<lab-id>/exercise-1.html" class="lab-card">
  <div class="lab-card-banner"></div>
  <div class="lab-card-body">
    <span class="lab-card-tag">{first_tag}</span>
    <h3>{exercise_1_title}</h3>
    <p>{exercise_1_description}</p>
  </div>
  <div class="lab-card-footer">
    <span class="lab-meta-tag">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
      {exercise_1_duration}
    </span>
    <span class="lab-meta-tag">{step_count} steps</span>
  </div>
</a>
```

Also update the "All Labs" section heading count if it displays a number.

If the lab has more than one exercise, add a card for each exercise following the same pattern.

Check first: if a card with `href="labs/<lab-id>/..."` already exists, skip adding it (idempotent).

### 8 — HTML escaping

Always escape these characters in any text inserted into HTML attributes or element content:

- `&` → `&amp;`
- `<` → `&lt;`
- `>` → `&gt;`
- `"` → `&quot;` (in attributes only)
- `'` → `&#x27;` (in attributes only)

### 9 — Commit

After all files are written:

```bash
git add labs/<lab-id>/ index.html
git status
git commit -m "Add <lab-title> lab guide

Auto-generated from <docx-filename> using /generate-lab skill.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Quality checklist

Before reporting done, verify:

- [ ] Every exercise file has a `<script src="../../assets/js/lab.js"></script>` at end of body
- [ ] `data-lab-id` attribute on `<html>` matches `exercise-N`
- [ ] Each `.step-page` has a unique `id="page-K"`
- [ ] Nav buttons exist on every page (`id="prevBtn"`, `id="markDoneBtn"`, `id="nextBtn"`)
- [ ] Image `src` paths are relative to the exercise HTML file
- [ ] No broken image references (cross-check extracted image filenames)
- [ ] Sidebar step count matches actual number of `.step-page` sections minus 1 (Overview doesn't count as a numbered step)
- [ ] `labs/<lab-id>/index.html` links back to `../../index.html`
- [ ] Root `index.html` catalog has been updated with new cards
- [ ] All files committed to git

## Error handling

- If the docx cannot be opened: report the error with the exact Python traceback, then stop.
- If metadata table is missing required fields: warn the user which fields are missing and use sensible defaults (`"Unknown"`, `"~N/A"`, etc.), then continue.
- If no `Heading3` styles are found in an exercise: treat the entire exercise body as a single step (no step partitioning).
- If image extraction fails for an individual image: emit a warning comment in the HTML (`<!-- image extraction failed: <rId> -->`) and continue.

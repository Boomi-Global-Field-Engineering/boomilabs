---
name: generate-lab
description: Convert a Word document written with the Boomi Labs template into a complete HTML lab guide (lab index + one page per exercise + extracted screenshots), add it to the site catalog, and commit it. Use for new labs, new versions of existing labs, and re-generating a lab after its source docx changes.
---

# Generate Lab Guide (v3 — November 2026)

Turn a `.docx` authored with `templates/boomi-labs-template.docx` into a published lab on the Boomi Labs site
(`https://boomi-global-field-engineering.github.io/boomilabs/`).

## Usage

```
/generate-lab <path-to-docx> [--lab-id <slug>] [--category <slug>] [--status published|draft|unlisted]
```

| Argument | Meaning |
|---|---|
| `<path-to-docx>` | Required. The Word file. |
| `--lab-id` | Folder name under `labs/`. Default: docx filename, lower-case, spaces → hyphens. Must be unique on the site. For a new version of an existing lab use `<id>-v2`, never overwrite the old folder. |
| `--category` | One of `sap`, `mft`, `flow`, `integration`, `datamgmt`, `agentic`, `tech`. Overrides the `Category` row of the metadata table. |
| `--status` | `published` (default) adds a normal catalog card. `draft` adds a greyed "Coming Soon" card plus DRAFT banners on every page. `unlisted` publishes the pages but adds no card (use for review previews). |

## What you produce

```
labs/<lab-id>/
  index.html            lab overview: hero, exercise list, prerequisites, details aside
  exercise-1.html …     one file per exercise, one .step-page per step (+ overview page 0)
  images/exN/…          screenshots extracted from the docx, per exercise
index.html              root catalog: one card per lab inside .catalog-grid, with data-category
catalog.txt             plain-text index: Lab Name / Description / Guide Link / Version block
```

One lab = one catalog card (not one per exercise). Both `index.html` and `catalog.txt` must be updated together.

## Procedure

### 1. Parse the docx

Run the bundled parser — it needs only the Python standard library:

```bash
python3 -I .claude/skills/generate-lab/scripts/parse_docx.py "<path-to-docx>" labs/<lab-id>
```

It writes `labs/<lab-id>/blocks.json` (an ordered list of typed blocks, see below), extracts every image to
`labs/<lab-id>/images/exN/imageNN.png` numbered per exercise, and prints the metadata table it found.
Delete `blocks.json` before committing.

Block types: `h1` (lab title), `meta` (key/value rows), `h2` (exercise), `h3` (step), `step` (numbered
instruction), `body` (paragraph; list items carry `"list": "ul"|"ol"`), `code_block`, `callout_info`,
`callout_tip`, `callout_warning`, `callout_important`, `table` (rows), `image` (`src`, `alt`).
Inline formatting arrives as `<strong>`, `<em>`, `<code>` already escaped.

Style mapping used by the parser (styles defined in the Word template):

| Word style | Block |
|---|---|
| Heading 1 | `h1` — lab title, once |
| Heading 2 | `h2` — exercise title (`Exercise N: …`) |
| Heading 3 / **Lab Step** | `h3` — step title (`Step K: … (N min)`) |
| Normal / List Bullet / List Number | `body` |
| Lab Code | `code_block` |
| Lab Info / Lab Tip / Lab Warning / Lab Important | `callout_*` |
| any table | `table`; the first table after the title is `meta` |

Metadata rows: `Title`, `Description`, `Duration`, `Level`, `Tags`, `Product`, `Category`, `Status`,
optional `Lab ID`. Missing rows → warn and fall back (`Level: Intermediate`, `Category` from `--category`
or ask, `Status: published`).

### 2. Segment

Partition on `h2` → exercises; within each, on `h3`/`step` titles → steps. Blocks before the first step
form that exercise's **Overview** (page 0). An `h2` titled "Prerequisites", "Before you begin" or
"What you'll learn" before Exercise 1 belongs to the lab index, not an exercise.

### 3. Write each `exercise-N.html`

Copy `reference/exercise-page.html` and fill the placeholders. Non-negotiable rules (the JavaScript depends
on them):

- `<html lang="en" data-lab-id="<lab-id>-exN" data-next-exercise-href="exercise-N+1.html">`. The lab id
  must be unique across the whole site (it keys saved progress in the browser). **Omit**
  `data-next-exercise-href` on the last exercise so the final button reads "Finish ✓".
- `<script src="../../assets/js/analytics.js"></script>` in `<head>`, `<script src="../../assets/js/lab.js"></script>`
  as the last thing in `<body>`. Pages in a deeper folder use one more `../`.
- One `<section class="step-page" id="page-K">` per page, K from 0; only page 0 also has class `active`.
- Sidebar: one `<li><a href="#step-K" data-step="K">` per page. The bubble number `.step-num-inner` is **K**
  (Overview shows 0), so bubbles match the "Step K of N" labels inside the pages.
- Every page ends with the `step-nav` block (`prevBtn`, `markDoneBtn`, `nextBtn`). Duplicate ids across
  pages are expected.
- Step label text: page 0 `Overview`; page K `Step K of N` (prefix `Section S · ` if the docx groups steps
  under sections).

Rendering rules:

| Block | HTML |
|---|---|
| `body` | `<p>…</p>`; consecutive list items → `<ul>`/`<ol>` |
| `step` | `<li><div class="instruction-num">K</div><div class="instruction-body">…</div></li>` inside one `<ol class="instruction-list">` per page; images, callouts and tables that follow a step go inside its `instruction-body` |
| `code_block` | `<pre><code>…</code></pre>` (lab.js adds the Copy button) |
| `image` | `<figure class="screenshot"><img src="images/exN/…" alt="…" loading="lazy"><figcaption>…</figcaption></figure>` — caption from the paragraph that precedes the image if it is short and ends without a period, else the alt text |
| `callout_info` / `tip` / `warning` / `important` | `<div class="callout info|tip|warning|important"><span class="callout-icon">SVG</span><div><strong>Title</strong> text</div></div>` — if the first sentence ends with `—` or `:` treat it as the title. SVGs are in `reference/exercise-page.html`. |
| table with first header `Field`/`Credential`/`URL` | `<div class="credentials-box"><h4>Credentials</h4><div class="cred-row"><span class="cred-label">…</span><span class="cred-value">…</span></div>…</div>` |
| any other table | `<table class="mapping-table"><thead>…</thead><tbody>…</tbody></table>` |

Optional components for richer labs (copy the inline `<style>` from `labs/boomi-for-sap-v2/exercise-1.html`):
`.flow-strip` (where-am-I strip above a step), `.why-box` (the reasoning behind a step), `.trainer-box`
(a "Facilitator moment" the facilitator demonstrates live). Use them only when the docx asks for them.

### 4. Write `labs/<lab-id>/index.html`

Copy `reference/lab-index.html`. Hero = title, description, badges (duration, level, N exercises); one
`exercise-item` per exercise with its description, duration and step count; Prerequisites; Lab Details aside
(products, patterns from `Tags`, total duration, level, reference links).

### 5. Update the catalog

Follow `reference/catalog.md`: add one `lab-card` with the right `data-category` and tag colour, placed in
the correct position inside `.catalog-grid` (DOM order is display order within a category; the MFT order is
fixed and listed there), and append a block to `catalog.txt`. Category tile counts update themselves.
Status `draft` → card class `lab-card coming-soon` + `<span class="lab-card-tag coming-soon-tag">Coming Soon</span>`,
and every lab page gets the DRAFT pill in the header and a `.draft-banner` at the top of its content.
Status `unlisted` → skip the card and `catalog.txt`; report the direct URL instead.

### 6. Content rules (public, customer-facing site)

- **No credentials.** Passwords, API keys and shared account secrets are never written into a page. Use
  `Provided by your lab facilitator`. User names that identify a real shared account are also left out.
- **No customer branding.** Strip customer names, logos, screenshots that show a customer's tenant, and
  internal project names before publishing. Replace with neutral names (Contoso-style) or the Boomi demo org.
- **No internal asides.** Facilitator-only notes ("if anyone asks…", review history, who built what) go in
  the internal facilitator guide, not the lab.
- Say **facilitator**, not trainer. Say **runtime**, not Atom, except where the product UI still shows Atom.
- Product names as the product team spells them today (e.g. *Boomi for SAP Solutions*, *Solutions Core*,
  *Solutions Connector*); keep on-screen labels exactly as the UI shows them.
- Where a runtime, environment or connection name appears in a screenshot but will differ per delivery, say
  so in the step: "the runtime name will differ from the screenshot — pick the one your facilitator names".

### 7. Verify, then commit

Run the checklist below, open the lab locally (`open labs/<lab-id>/index.html` or `python3 -m http.server`)
and click through every step. Then:

```bash
git add labs/<lab-id> index.html catalog.txt
git commit -m "Add <lab title> lab guide

Generated from <docx filename> with /generate-lab v3."
```

Contributors who are not the site owner push a branch and open a pull request (see `CONTRIBUTING.md`);
the owner merges to `main`, which deploys GitHub Pages within a few minutes.

## Quality checklist

- [ ] Every page has `analytics.js` in `<head>` at the correct relative depth, and exercises end with `lab.js`
- [ ] `data-lab-id` values are unique on the site (`grep -r 'data-lab-id="<lab-id>-' labs | wc -l` equals the number of exercises)
- [ ] `data-next-exercise-href` present on all exercises except the last
- [ ] Sidebar bubbles run 0…N and match the step labels; `.step-page` ids run `page-0`…`page-N`; every page has the three nav buttons
- [ ] Every `img src` resolves to a file; no image from another lab's folder
- [ ] No `Welcome…`-style passwords, no customer names, no "trainer"
- [ ] Catalog card has `data-category`, sits in the right position, links to `labs/<lab-id>/index.html`; `catalog.txt` block added
- [ ] HTML parses: `python3 -c "import html.parser,sys; ..."` or open in a browser with the console clean
- [ ] `blocks.json` removed; only `labs/<lab-id>`, `index.html`, `catalog.txt` staged

## Regenerating an existing lab

Re-run the parser into the same folder only if the lab was never hand-edited after generation. Many live
labs have been refined directly in HTML (SAP, MFT). For those, apply the docx changes to the HTML by hand
and keep the existing ids, screenshots and catalog entry. When in doubt, generate into `<id>-v2` and compare.

## Error handling

- Docx fails to open → report the traceback and stop.
- Metadata rows missing → warn, use defaults, continue; always ask for `Category` if it cannot be inferred.
- No step headings in an exercise → the whole exercise is one step.
- An image cannot be extracted → leave `<!-- image missing: rIdN -->` and continue.

## Version history

- **v3 — 18 Nov 2026.** Skill format (`SKILL.md` + reference files + parser script). Category-based catalog
  with `data-category` and ordering rules, `catalog.txt` sync, one card per lab linking to the lab index,
  draft / coming-soon / unlisted states, 0-based sidebar bubbles, site-unique `data-lab-id`, `.screenshot`
  figures, correct callout classes, credentials/branding/internal-note rules, facilitator wording, PR flow.
- **v2 — 21 Jul 2026.** Google Analytics loader on every page; `data-next-exercise-href` navigation.
- **v1 — 29 Apr 2026.** Initial docx → HTML generator and Word template.

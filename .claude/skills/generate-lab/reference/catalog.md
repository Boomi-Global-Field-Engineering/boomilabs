# Catalog rules (root `index.html` + `catalog.txt`)

The root page shows seven category tiles; clicking one filters the single `.catalog-grid` of lab cards by
`data-category`. The count on each tile is computed by the page script from the cards, so adding a card is
all that is needed to update the count.

## Categories

| `data-category` | Tile label | Tag text / colours used on cards |
|---|---|---|
| `sap` | SAP | `SAP Integration` (default tag colours) |
| `mft` | Managed File Transfer | `Boomi MFT` — `style="background:#ecfdf5;color:#065f46;"`; banner `linear-gradient(90deg,#1a9e5c,#0a5a7a)` |
| `flow` | Boomi Flow | `Boomi Flow` — `style="background:#fff1ec;color:#c94000;"`; banner `linear-gradient(90deg,#f97c67,#c94000)` |
| `integration` | Integration & APIM | `Integration` — `style="background:#ecfdf5;color:#065f46;"`; APIM cards `Cloud API Management` — `style="background:#e6f0f5;color:#063d58;"` |
| `datamgmt` | Data Management | `Data Hub` / `Data Integration` — `style="background:#eef2ff;color:#3730a3;"`; banner `linear-gradient(90deg,#4f46e5,#0a5a7a)` |
| `agentic` | Agentic | `Agentic` — `style="background:#fdf2f8;color:#9d174d;"`; banner `linear-gradient(90deg,#ec4899,#8b5cf6)` |
| `tech` | Technical Workshop | `Technical Workshop` — `style="background:#eef2ff;color:#3730a3;"`; banner `linear-gradient(90deg,#063d58,#4f46e5)` |

Copy the tag and banner styles from an existing card in the same category rather than inventing new ones.

## Card markup

```html
      <a href="labs/<lab-id>/index.html" class="lab-card" data-category="<category>">
        <div class="lab-card-banner" style="background: linear-gradient(90deg, #1a9e5c, #0a5a7a);"></div>
        <div class="lab-card-body">
          <span class="lab-card-tag" style="background: #ecfdf5; color: #065f46;">Boomi MFT</span>
          <h3>{Lab title}</h3>
          <p>{One or two sentences — what they build and learn.}</p>
        </div>
        <div class="lab-card-footer">
          <span class="lab-meta-tag">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            ~90 min
          </span>
          <span class="lab-meta-tag">3 exercises</span>
        </div>
      </a>
```

- One card per lab, linking to the lab's `index.html` (never to `exercise-1.html`).
- Draft lab: `class="lab-card coming-soon"` and add `<span class="lab-card-tag coming-soon-tag">Coming Soon</span>`
  right after the category tag. The card stays clickable so reviewers can open the draft.
- New version of an existing lab: add a second card with " — Version 2" in the title and keep the old one
  (" — Version 1") unless the owner says to retire it. Give the old lab's index a short notice pointing
  to the new version.
- Idempotent: if a card with the same `href` exists, update it instead of adding another.

## Ordering

DOM order inside `.catalog-grid` is the display order within a category. Append new cards at the end of
their category's run unless told otherwise. The MFT order is fixed:

1. Modernizing the Back Office (CRM → Partner) — Version 2, then Version 1
2. Many to One (Partners → Headquarters)
3. Install & Test the MFT Runtime (Thru Node)
4. Trading Partner SFTP & EDI Processing
5. MFT POC Framework
6. MFT Guided Demos
7. Certified File Transfer Professional (CFTP)

## Featured lab

The "Featured Lab" block above the tiles is maintained by hand by the site owner. Do not change it when
adding a lab.

## `catalog.txt`

Plain-text index consumed outside the site. Append one block per lab, separated by `---`. Description is
plain text with no punctuation other than spaces (the file is used for keyword search); write it as a
single line.

```
Lab Name: <Lab title>
Description: <plain text description>
Guide Link: https://boomi-global-field-engineering.github.io/boomilabs/labs/<lab-id>/index.html
Version: <YYYY-MM-DD>

---
```

Drafts are listed with ` (DRAFT - coming soon, under review)` appended to the name. Unlisted labs are not
added.

## Unlisted labs

Some folders under `labs/` are deliberately not in the catalog (review previews such as a lab's `-v2`
before approval, or customer-specific workshops). Never add a card for a folder just because it exists;
ask the owner.

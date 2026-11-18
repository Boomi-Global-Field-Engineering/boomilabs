# Contributing a lab to Boomi Labs

Boomi Labs is a static GitHub Pages site. Every lab is a folder under `labs/` with an `index.html`, one
`exercise-N.html` per exercise, and an `images/` folder. The root `index.html` is the catalog and
`catalog.txt` is its plain-text twin. There is no build step: what is committed to `main` is what is live
a few minutes later at https://boomi-global-field-engineering.github.io/boomilabs/.

## The short version

1. Write the lab in Word using `templates/boomi-labs-template.docx`. Keep the heading and "Lab …" styles;
   fill in the metadata table (including `Category` and `Status`); paste screenshots inline.
2. Clone this repo, open it in Claude Code, and run
   `/generate-lab path/to/your-lab.docx --lab-id your-lab-id`.
   The skill in `.claude/skills/generate-lab/` builds the pages, extracts the screenshots, adds the catalog
   card and `catalog.txt` entry, and runs its own checklist.
3. Open `labs/your-lab-id/index.html` in a browser and click through every step.
4. Push a branch and open a pull request. The site owner reviews and merges to `main`.

If you don't use Claude Code, follow `.claude/skills/generate-lab/SKILL.md` by hand: it is written as a
procedure, and `reference/` holds the exact page skeletons to copy.

## Rules every lab must follow

- **No credentials.** Never put a password, key or shared account secret in a page. Write
  `Provided by your lab facilitator`.
- **No customer branding.** No customer names, logos or tenant screenshots. Use neutral names or the Boomi
  demo org.
- **Customer-facing voice.** No internal notes, review history or "if anyone asks" asides. Those belong in
  the internal facilitator guide for the lab.
- **One card per lab** in the catalog, with the correct `data-category`, linking to the lab's `index.html`.
  Update `catalog.txt` at the same time.
- **Analytics on every page**: `<script src="../../assets/js/analytics.js"></script>` in `<head>`
  (adjust `../` to the page's depth). Don't add your own tracking snippets.
- **Unique `data-lab-id`** on every exercise page (`<lab-id>-exN`). It keys saved progress in the browser.
- **Don't edit `assets/`** (shared CSS and JS) without agreeing it with the site owner; it affects every lab.
- **Don't overwrite a live lab in place** when you make a new version. Create `<lab-id>-v2`, mark the old one
  "Version 1", and let the owner decide whether both stay in the catalog.

## Drafts and reviews

A lab that is not ready for participants can still be published for review:

- `--status draft` lists it with a greyed "Coming Soon" card and DRAFT banners on every page.
- `--status unlisted` publishes the pages with no card at all; share the direct URL with reviewers.

## Updating an existing lab

Most live labs have been refined directly in HTML after generation. Edit the HTML for small changes
(text, a screenshot swap, a corrected URL) rather than regenerating from the docx, and keep the lab's ids,
image names and catalog entry. Put replacement screenshots in the lab's `images/exN/` folder with a
descriptive name.

## Getting access

Ask the site owner (Field Engineering) for write access to the `Boomi-Global-Field-Engineering/boomilabs`
repository, or fork it and open pull requests from your fork.

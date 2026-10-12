# Design guide

The rules that keep every change to this site looking like the same site. `assets/css/site.css` is the implementation; this file is the intent. If you change one, change the other. `tools/check_site.py` enforces what can be enforced.

The site is the HTML5 UP "Dopetrope/Helios" template (`assets/css/main.css`, jQuery, no build step) with a custom layer on top (`site.css`, `site.js`). The look: light page, white cards, plum headings, coral accent, Source Sans Pro, soft shadows.

## Where things live

| What | Where | Rules |
|---|---|---|
| Template styles | `assets/css/main.css` | Treat as vendor code. The header/hero edits stay; **don't add new components here.** `assets/sass/` is the untouched template source and is **not** rebuilt: main.css is edited directly and is the truth. |
| Custom styles | `assets/css/site.css` | All new CSS. Tokens first, then components. No `<style>` blocks in HTML, no `style=""` attributes. |
| Custom behavior | `assets/js/site.js` | All new JS. No inline `<script>` blocks, no `javascript:` URLs, no `onclick=""`. |
| Project cards | `index.html`, between `projects:*:start/end` markers | **Generated** from the registry by `tools/render_projects.py`. Don't hand-edit between the markers. |
| Images | `images/` | Web-sized only (see Images). Full-size originals live outside the repo. |

## Tokens

All values come from `:root` in `site.css`. Use the token; never type the value.

**Color**

| Token | Value | Use | Contrast |
|---|---|---|---|
| `--color-ink` | `#483949` | Headings, tag text | 10.7:1 on white |
| `--color-text` | `#555555` | Body copy in cards | 7.5:1 on white |
| `--color-meta` | `#6b5f6c` | Small secondary text | 6.0:1 on white |
| `--color-accent` | `#ef8376` | Fills, borders, bullets. **Never as text** | 2.6:1: fails as text |
| `--color-accent-strong` | `#b94a3a` | Accent used **as text**, or as a fill under white text | 5.1:1 on white, 4.6:1 on page |
| `--color-accent-hover` | `#df7366` | Hover on accent fills | n/a |
| `--color-surface` / `--color-page` | `#fff` / `#f0f4f4` | Card / page background | n/a |
| `--color-tint` | `#f0eef0` | Tag background | 9.3:1 with ink |

Rules: one accent. No new hues (the old rainbow of tag colors failed contrast at 1.6–2.1:1, so tags are one neutral style). Anything that carries meaning must also carry it without color.

**Spacing** (`--space-1` … `--space-10` = 0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4 rem). Every padding, margin, and gap in a component uses one of these. Card padding is `--space-5`; gap between cards is `--space-6` (`--space-5` on mobile); section padding is `--space-8`/`--space-10`.

**Type** (`--text-xs` 0.78, `--text-sm` 0.95, `--text-base` 1, `--text-lg` 1.2, `--text-xl` 1.8 rem). Card titles `--text-lg` 600; card copy `--text-sm` weight **400** (the template's 300 is too thin at card size); meta line `--text-xs` uppercase 600. Body text is left-aligned: the template justifies every `<p>`, which opens uneven gaps, so components override it.

**Shape**: card radius `--radius-card`, chips `--radius-pill`, shadow `--shadow-card` (hover `--shadow-card-hover`). Tap targets are at least `--tap-target` (44px).

## Components

### Project card

```
article.project-card [--featured]
├─ div.project-card__media > img          13.75rem tall, object-fit: cover, 1000×666 source
└─ div.project-card__body
   ├─ p.project-card__meta                "Org · Period" (under ~38 chars: one line at every width)
   ├─ h4.project-card__title
   ├─ p.project-card__role                optional, italic; team size goes here
   ├─ p.project-card__summary             1–3 sentences
   ├─ ul.project-card__highlights         1–3 bullets, one fact each, coral dot
   ├─ ul.project-card__tags               stack and methods; pinned to the bottom
   └─ div.project-card__links | p.project-card__note
```

- Every card has every part it has data for, in this order. Don't reorder, skip a level, or add a one-off element. If a card needs something new, extend the component and update this section.
- Featured cards (`--featured`) get the coral border and the badge, and sit in the first grid. Standard cards go in "More Projects".
- Cards in a row are equal height (flex column; tags and links pin to the bottom).
- Link labels are short ("GitHub", "Report") and each carries an `aria-label` that names the project.
- No repo link means a `project-card__note` (for example "Employer project · source not public"). Never link to a repo that isn't public.
- Titles are `h4`, under an `h3` group heading, under the `h2` "Selected Works". Don't skip heading levels.

### Page sections

| Section | Pattern |
|---|---|
| Work bands | `section.work` (`--featured` white band, `--more` page-grey band) → `.project-grid` |
| About | `.about` flex row (photo 40%, text), stacks under 840px |
| Services | Template `.row` / `article.col-4`; each opens the dialog via `data-service` |
| Dialog | `.modal` + `.modal__content`; opened by `site.js` only |

### Dialog

`role="dialog"`, `aria-modal`, labelled by its title. Opens with focus on the first field, traps Tab, closes on Escape, the × button, or the backdrop, and returns focus to the trigger. Status messages go in `#formStatus` (`role="status"`), never `alert()`. Inputs are 16px minimum so iOS doesn't zoom.

## Responsive

Breakpoints in use: **840px** (grids and About stack), **600px** (dialog tightens). Check **375, 768, 1280** before calling anything done. No horizontal scroll at any width. The card grid is `auto-fit` from 300px to 420px, plus one explicit two-column rule for 600–900px (auto-fit counts columns using the 420px maximum, so a tablet would otherwise get one).

## Images

- Card, service, and about images: **1000px wide max, JPEG quality ~72, under 400KB.** The hero background: **1920px, quality ~60, under 1MB.**
- Always `width`, `height`, and `loading="lazy"` (not on anything above the fold).
- `alt` describes what the photo shows, written after **looking** at it. Decorative images use `alt=""` and sit inside an `aria-hidden` link. Never reuse one photo for two cards.
- Resize with: `sips -Z 1000 -s format jpeg -s formatOptions 72 "in.jpg" --out "images/out.jpg"`. Keep the full-size original in `../_originals/`, not in this repo.

## Accessibility baseline

Zoom is never disabled. One `h1`; heading levels don't skip. Every field has a `<label for>`. Every link has a name. Text meets 4.5:1. Focus is visible (`:focus-visible` outline in `site.css`). Motion respects `prefers-reduced-motion`. New tabs use `rel="noopener noreferrer"`.

## Content

Content rules are not in this file: this repo is public. Page content comes from `../PROJECTS.md` and `../PROFILE.md` and follows `../CLAUDE.md`. `check_site.py` reads them and fails the build of a page that publishes a held project or a never-say phrase.

## Review

Run `/portfolio-ux-review` for a full UX review (screens at three widths, keyboard pass, hierarchy and spacing, accessibility, performance). Run `python3 tools/check_site.py` for the automatic part at any time; it must report 0 fail before any change is handed back.

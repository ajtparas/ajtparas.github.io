---
name: portfolio-ux-review
description: Review the portfolio website's UX, visual consistency, accessibility, performance, and content integrity, and write a prioritized report. Use when the user asks for a UX review, design review, accessibility audit, or "how does the site look/feel", or before publishing portfolio changes.
---

# Portfolio UX review

A review finds problems and ranks them. It doesn't fix anything unless the user asks. It's built so two reviews on different days measure the same things, and so every finding points at a rule in `portfolio/DESIGN.md` or a measurement, never at taste alone. Run from `career/`.

## 1. Set up

- Serve the site: `cd portfolio && python3 -m http.server 8765` in the background (the preview launcher can't read `~/Desktop`). Open it in the browser pane.
- **Bypass the browser cache** after any edit (cache-bust the stylesheet and image URLs, or navigate with a fresh `?v=` query and reload images). A stale cache once made 1000px images read as 4032px.
- Read `portfolio/DESIGN.md` so you review against the site's own rules.

## 2. Automatic checks

```bash
python3 portfolio/tools/check_site.py            # structure, a11y basics, image weight, tokens, content rules
python3 portfolio/tools/check_site.py --online   # external links alive
```

Record every FAIL and WARN. These are facts; don't re-derive them.

## 3. Measure the rendered page

At each of **1280, 768, and 375px** (`resize_window`, then reload): run the audit in the browser's JavaScript executor. The local server serves the script, so load it with:

```js
eval(await (await fetch('/.claude/skills/portfolio-ux-review/audit.js')).text())
```

It returns JSON. It measures text contrast against the real background, tap-target sizes, the text sizes in use, horizontal overflow, image sizing against display size, and card row gaps. Text over the hero photo is listed under `overImage`: check it by eye.

Reset the viewport to the `desktop` preset when done.

## 4. Look at it (screenshots; wait a second after each scroll, since screenshots lag)

At all three widths, top to bottom: hero, work section, About, Services, footer. Then judge:

- **Hierarchy.** Is it obvious what to read first on each screen? Does the eye land on the featured work and on the contact path?
- **Consistency.** One card style, one accent, one spacing rhythm, one voice. Anything that looks like it came from a different site is a finding.
- **Spacing.** Gaps match the token scale; sections breathe equally; nothing is cramped on mobile or lost on desktop.
- **Text.** Readable size and weight, sensible line length, no justified paragraphs with uneven gaps, no orphaned words in headings.
- **Imagery.** Each photo says something true about its card; no repeats; crops don't cut subjects; no distortion.
- **Interaction.** Hover and focus states exist; the dialog opens, traps focus, closes on Escape and returns focus; buttons look like buttons.
- **Mobile.** Single column, no horizontal scroll, nav panel works, tap targets are comfortable.

## 5. Keyboard pass

Press Tab from the top of the page with screenshots at several stops. Every interactive element must be reachable in a sensible order, with a **visible** focus indicator; the skip into the dialog and back must work; nothing should trap focus outside the dialog. Note anything that isn't reachable or isn't visible.

## 6. Content integrity

Does the page match `PROJECTS.md` (live cards present, held absent) and `PROFILE.md` (titles, tagline, links)? Do the numbers on cards read exactly as sourced? `check_site.py` covers the mechanical part; you cover whether the **story** is coherent: does the hero, About, and the cards tell one consistent account of who this person is and what they've done?

## 7. Write the report

Save to `reviews/portfolio-YYYY-MM-DD.md` (create `reviews/` in `career/`, outside the public repo). If an earlier report exists, read it and mark each old finding **fixed**, **still open**, or **won't fix**.

```markdown
# Portfolio UX review: YYYY-MM-DD

**Scope:** what was reviewed, widths, how
**Verdict:** two sentences. Would you be comfortable sending this link to a hiring manager today? Why.

## Fix before publishing (P0/P1)
| # | Finding | Evidence | Rule | Suggested fix |
|---|---|---|---|---|

## Should fix (P2)
## Polish (P3)
## Needs your call
(design choices only the owner can make, with a recommendation)

## What's working
(specific things to keep; calibration runs both ways)

## Since last review
(fixed / still open / won't fix)
```

Severity: **P0** breaks the page, publishes something false or withdrawn, or locks users out. **P1** fails an accessibility minimum or damages first impressions. **P2** friction or inconsistency a visitor would notice. **P3** polish. Every finding cites evidence (measurement, check ID, or screenshot description) and the `DESIGN.md` rule it breaks; if no rule covers it, say so and propose one.

## 8. Report back

Give the verdict, the P0/P1 list, the "needs your call" items, and the report path. Don't fix anything unprompted. Offer to.

---
name: portfolio-update
description: Add, edit, or remove a project card, or change copy and sections on the portfolio site, while keeping its design system, spacing, and content rules. Use when the user wants to add or change a portfolio project, update About or Services copy, swap images, publish a held project, or sync the site with the career files.
---

# Portfolio update

Every change to this site goes through the same path so it stays consistent: **facts → registry → generated cards → checks → look at it.** Read `portfolio/CLAUDE.md` and `portfolio/DESIGN.md` first, and `../CLAUDE.md` for the evidence rules. Run from `career/`.

## Add or edit a project card

1. **Get the facts from the source, not from memory.** If the project is in `PROJECTS.md` as `held`, read its **unlock** questions and get answers from Aldrich. If it's new, ask what's needed: what it is, dates, who did what (authorship!), stack, a public link if any, and the outcome. Look up what you can yourself (public repo README via `curl -s -H "Accept: application/vnd.github.raw" https://api.github.com/repos/ajtparas/<repo>/readme`, the repo's file tree, `CAREER_MASTER.md`). Only decisions and recollections go to the user.
2. **Check the claims against `CAREER_MASTER.md`** (Verified projects, the role sections, Open Inconsistencies, Resolved). Numbers appear only as sourced; authorship is scoped to the user's own commits; coursework is never described as adopted by a client. Anything that isn't in CAREER_MASTER gets recorded there first, through `/grill-resume`.
3. **Write the entry in `PROJECTS.md`** in the existing format: `status`, `tier`, `title`, `meta`, `role`, `summary` (1–3 sentences), `highlights` (1–3 bullets, one fact each), `tags`, `links` (public URLs only, or `none` with a `note`), `image`, `image alt`, `source`, `do not claim`. Mirror the voice of the existing cards. Set `status: live`. A held project keeps `status: held` plus `why held` and `unlock`.
4. **Image.** Pick or add a photo that isn't used by another card. **Look at it** (Read the file) before writing `image alt` so the description matches what it shows. Resize per `DESIGN.md` into `portfolio/images/` and keep the original in `_originals/`.
5. **Render**: `python3 portfolio/tools/render_projects.py`. Don't hand-edit between the `projects:*:start/end` markers.
6. **Check**: `python3 portfolio/tools/check_site.py`. It must show **0 fail**. Fix warnings or say why one stays.
7. **Look**: serve the site (`cd portfolio && python3 -m http.server 8765`, in the background) and screenshot the cards at **375, 768, and 1280px**. Confirm: equal heights in a row, no clipped text, tags and links pinned to the card bottom, no horizontal scroll.
8. **Log the decision** in `CAREER_MASTER.md` if a claim was reframed or withdrawn along the way, and keep `PROFILE.md` in sync if a title or bio fact changed.

## Remove or hold a project

Set `status: held` in `PROJECTS.md`, fill `why held` and `unlock`, rerun the renderer. The card disappears from the page, and the registry keeps the reason and what would bring it back. Never delete a project from the registry.

## Change page copy (hero, About, Services, footer)

Copy that states a career fact comes from `PROFILE.md` (approved bio, titles of record, tagline). Change it there first, then edit `index.html` to match. Pure voice changes (the Bears story, hobbies, service descriptions) are Aldrich's to word; fix typos, don't rewrite. Run `check_site.py`; its never-say list scans the page text.

## Change styling

Use tokens and existing components (`DESIGN.md`). A new value is a new token in `:root`; a new pattern is a new component documented in `DESIGN.md`, in the same change. No new CSS in `main.css` or in HTML. Re-check at three widths.

## Replace the public resume PDF

Only with a PDF from `resume/tailored/`, copied to `portfolio/images/Paras_Resume.pdf`, and only after `check_site.py` passes (it scans the PDF's text). Also run `python3 .claude/skills/tailor-resume/check_pdf.py` on it.

## Sync after the career files change

When `CAREER_MASTER.md` withdraws, reframes, or rescopes a claim, search `PROJECTS.md`, `PROFILE.md`, and `portfolio/index.html` for it and fix all three. Add the phrase to PROFILE's never-say list if it must never return.

## Finish

Report what changed, the `check_site.py` result, and anything you left for the user to decide. **Do not commit or push**: the site is public, and its GitHub repo is archived until the user unarchives it.

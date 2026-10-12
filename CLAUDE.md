# Portfolio — working rules

Static site, served by GitHub Pages from this folder (`ajtparas/ajtparas.github.io`). **This folder is a public git repo: anything saved here can end up on the internet.** Shared career rules are in `../CLAUDE.md`; read them first. Design rules are in `DESIGN.md`. Run sessions from `career/`, not from this folder.

## Before you change anything

1. Read `DESIGN.md`. Reuse existing tokens and components. If you need something new, add it to `assets/css/site.css` (tokens at the top) and document it in `DESIGN.md` in the same change.
2. Content comes from `../PROJECTS.md` and `../PROFILE.md`, never from your own wording. If a fact isn't there, ask, then add it there with its source in `../CAREER_MASTER.md`, then use it. `../CAREER_MASTER.md` itself must never be copied into this folder, quoted at length, or referenced by claim detail in any file here.
3. Don't write career claims into HTML by hand. Project cards are generated: edit `../PROJECTS.md`, run `python3 tools/render_projects.py`.

## Commands

```bash
python3 tools/render_projects.py        # regenerate the cards from ../PROJECTS.md
python3 tools/sync_resume.py            # republish images/Paras_Resume.pdf from ../resume/tailored/
python3 tools/sync_resume.py --list     # show which tailored resume is currently published
python3 tools/check_site.py             # structure, a11y, performance, tokens, content rules. Must show 0 fail
python3 tools/check_site.py --online    # also checks external links are alive
cd portfolio && python3 -m http.server 8765    # preview at http://localhost:8765
```

The desktop app's preview launcher can't read `~/Desktop`, so start the server from the shell as above. Look at the result at **375, 768, and 1280px** before reporting a change done.

## Skills

- `portfolio-update`: add or change a project card or a page section, the right way.
- `portfolio-ux-review`: full UX, accessibility, and performance review with a written report.

## Hard rules

- **No `git commit`, `git push`, or GitHub settings changes** unless asked. Edit files only.
- The repo `ajtparas.github.io` is **archived** on GitHub: it can't be pushed to until it's unarchived (repo Settings → Archive this repository). Say so if asked to publish.
- No custom CSS in `main.css` or in HTML. No inline `style=""`, `<style>`, `<script>` blocks, or `javascript:` links. See `DESIGN.md` for where each thing goes.
- `images/Paras_Resume.pdf` is the public resume, and it is a **copy** — it goes stale whenever a new resume is built. Never hand-replace it: run `python3 tools/sync_resume.py`, which copies from `../resume/tailored/` and refuses to publish a PDF containing a never-say phrase. Re-run it after every resume build, then `check_site.py`.
- Don't link to a repo that isn't public. Held projects (`../PROJECTS.md`) never render.
- Full-size source images belong in `../_originals/`, not here. Web images follow the sizes in `DESIGN.md`.

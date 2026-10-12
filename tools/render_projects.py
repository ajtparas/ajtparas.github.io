#!/usr/bin/env python3
"""Render project cards into index.html from the registry (../PROJECTS.md).

Usage:  python3 tools/render_projects.py [--check]

Replaces the content between these marker pairs in index.html:
    <!-- projects:featured:start --> ... <!-- projects:featured:end -->
    <!-- projects:standard:start --> ... <!-- projects:standard:end -->
Only projects with status `live` are rendered. Never edit between the markers by hand: change
PROJECTS.md and rerun. With --check, exits 1 if index.html is out of date instead of writing.
"""
import html
import re
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import projects_md  # noqa: E402

INDEX = Path(__file__).resolve().parents[1] / "index.html"
T = "\t"


def esc(s):
    """Escape &, < and > and double quotes. Apostrophes stay literal: valid in text and in double-quoted attributes."""
    return html.escape(s, quote=False).replace('"', "&quot;")


def card(p, indent):
    featured = p.get("tier") == "featured"
    ind = T * indent
    out = [f'{ind}<article class="project-card{" project-card--featured" if featured else ""}">']
    out.append(f'{ind}{T}<div class="project-card__media">')
    out.append(
        f'{ind}{T}{T}<img src="{esc(quote(p["image"], safe="/"))}" alt="{esc(p.get("image_alt", ""))}" '
        f'width="1000" height="666" loading="lazy">'
    )
    out.append(f"{ind}{T}</div>")
    out.append(f'{ind}{T}<div class="project-card__body">')
    out.append(f'{ind}{T}{T}<p class="project-card__meta">{esc(p["meta"])}</p>')
    out.append(f'{ind}{T}{T}<h4 class="project-card__title">{esc(p["title"])}</h4>')
    if p.get("role"):
        out.append(f'{ind}{T}{T}<p class="project-card__role">{esc(p["role"])}</p>')
    out.append(f'{ind}{T}{T}<p class="project-card__summary">{esc(p["summary"])}</p>')
    if p["highlights"]:
        out.append(f'{ind}{T}{T}<ul class="project-card__highlights">')
        for h in p["highlights"]:
            out.append(f"{ind}{T}{T}{T}<li>{esc(h)}</li>")
        out.append(f"{ind}{T}{T}</ul>")
    tags = projects_md.tags(p)
    if tags:
        out.append(f'{ind}{T}{T}<ul class="project-card__tags" aria-label="Tools and methods">')
        for t in tags:
            out.append(f"{ind}{T}{T}{T}<li>{esc(t)}</li>")
        out.append(f"{ind}{T}{T}</ul>")
    links = projects_md.links(p)
    if links:
        out.append(f'{ind}{T}{T}<div class="project-card__links">')
        for label, url in links:
            out.append(
                f'{ind}{T}{T}{T}<a class="project-card__link" href="{esc(url)}" target="_blank" '
                f'rel="noopener noreferrer" aria-label="{esc(label)} for {esc(p["title"])}">{esc(label)}</a>'
            )
        out.append(f"{ind}{T}{T}</div>")
    elif p.get("note"):
        out.append(f'{ind}{T}{T}<p class="project-card__note">{esc(p["note"])}</p>')
    out.append(f"{ind}{T}</div>")
    out.append(f"{ind}</article>")
    return "\n".join(out)


def region(projects, tier, indent):
    cards = [card(p, indent) for p in projects if p.get("status") == "live" and p.get("tier") == tier]
    return "\n\n".join(cards)


def splice(text, name, body, indent):
    start, end = f"<!-- projects:{name}:start -->", f"<!-- projects:{name}:end -->"
    pat = re.compile(rf"{re.escape(start)}.*?{re.escape(end)}", re.S)
    if not pat.search(text):
        raise SystemExit(f"Markers for '{name}' not found in index.html")
    pad = T * indent
    replacement = f"{start}\n{body}\n{pad}{end}" if body else f"{start}\n{pad}{end}"
    return pat.sub(lambda m: replacement, text)


def render(text, projects):
    """Return index.html text with both card regions regenerated from the registry."""
    for tier in ("featured", "standard"):
        text = splice(text, tier, region(projects, tier, 5), 5)
    return text


def main():
    projects = projects_md.load()
    text = INDEX.read_text(encoding="utf-8")
    new = render(text, projects)
    if "--check" in sys.argv:
        if new != text:
            print("index.html is out of date with PROJECTS.md. Run: python3 tools/render_projects.py")
            return 1
        print("index.html matches PROJECTS.md")
        return 0
    INDEX.write_text(new, encoding="utf-8")
    live = [p for p in projects if p.get("status") == "live"]
    print(f"Rendered {len(live)} live project(s); {len(projects) - len(live)} held, not rendered.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

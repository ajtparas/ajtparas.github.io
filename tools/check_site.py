#!/usr/bin/env python3
"""Static checks for the portfolio: structure, accessibility basics, performance, design tokens,
and content consistency with the career registry.

Usage:  python3 tools/check_site.py [--online]
          --online   also HEAD every external link and report dead ones (needs network)

Exit code 1 if any FAIL. WARN means "fix or justify". INFO is context.

Content checks read ../PROJECTS.md and ../PROFILE.md (private, one folder up). If they are not
there, those checks are skipped and the script says so. Rules: see DESIGN.md.
"""
import re
import subprocess
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import projects_md  # noqa: E402
import render_projects  # noqa: E402

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
ALLOW_HASH_TEXT = {"Extras"}          # template dropdown opener; href="#" is intentional
IMG_WARN_KB, IMG_FAIL_KB = 400, 1024  # per image used on the page
IMG_MAX_WIDTH = 2400
SPACING_PROPS = re.compile(r"^\s*(padding|margin|gap|row-gap|column-gap)(-(top|right|bottom|left))?\s*:\s*([^;]+);", re.M)

findings = []  # (severity, id, message)


def add(sev, cid, msg):
    findings.append((sev, cid, msg))


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.headings, self.ids, self.anchors, self.imgs = [], [], [], [], []
        self.labels_for, self.fields, self.inline_styles, self.style_blocks = [], [], 0, 0
        self.text, self.attr_text, self.meta, self.html_attrs = [], [], {}, {}
        self._skip = 0
        self._a = None
        self._h = None
        self._label_for = None
        self.mismatch = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.html_attrs = a
        if tag == "meta" and a.get("name"):
            self.meta[a["name"]] = a.get("content", "")
        if a.get("id"):
            self.ids.append(a["id"])
        if "style" in a:
            self.inline_styles += 1
        if tag == "style":
            self.style_blocks += 1
        for k in ("alt", "title", "aria-label"):
            if a.get(k):
                self.attr_text.append(a[k])
        if tag in ("script", "style"):
            self._skip += 1
        if re.fullmatch(r"h[1-6]", tag):
            self._h = [int(tag[1]), ""]
        if tag == "a":
            self._a = {"href": a.get("href"), "target": a.get("target"), "rel": a.get("rel", ""),
                       "aria-label": a.get("aria-label"), "aria-hidden": a.get("aria-hidden"), "text": "", "img_alt": None}
        if tag == "img":
            self.imgs.append(a)
            if self._a is not None:
                self._a["img_alt"] = a.get("alt")
        if tag == "label" and a.get("for"):
            self.labels_for.append(a["for"])
        if tag in ("input", "select", "textarea") and a.get("type") != "hidden":
            self.fields.append(a.get("id"))
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip -= 1
        if re.fullmatch(r"h[1-6]", tag) and self._h:
            self.headings.append((self._h[0], self._h[1].strip()))
            self._h = None
        if tag == "a" and self._a is not None:
            self.anchors.append(self._a)
            self._a = None
        if tag in VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.mismatch.append(f"</{tag}> at line {self.getpos()[0]} (open: {self.stack[-1] if self.stack else 'none'})")
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag:
                    pass

    def handle_data(self, data):
        if self._skip:
            return
        self.text.append(data)
        if self._h is not None:
            self._h[1] += data
        if self._a is not None:
            self._a["text"] += data


def jpeg_size(path):
    try:
        data = path.read_bytes()
        i = 2
        while i < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in range(0xC0, 0xCF) and marker not in (0xC4, 0xC8, 0xCC):
                return int.from_bytes(data[i + 7:i + 9], "big"), int.from_bytes(data[i + 5:i + 7], "big")
            i += 2 + int.from_bytes(data[i + 2:i + 4], "big")
    except Exception:
        pass
    return None


def luminance(hex_):
    h = hex_.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def check_html(page, html):
    h1 = [h for h in page.headings if h[0] == 1]
    if len(h1) != 1:
        add("FAIL", "H1", f"expected exactly one h1, found {len(h1)}")
    prev = 0
    for level, text in page.headings:
        if prev and level > prev + 1:
            add("FAIL", "HEADING-ORDER", f"h{prev} jumps to h{level} at '{text[:40]}'")
        prev = level
    if not page.html_attrs.get("lang"):
        add("FAIL", "LANG", "<html> has no lang attribute")
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    if not title or not 10 <= len(title.group(1).strip()) <= 70:
        add("WARN", "TITLE", "missing, or not 10-70 characters")
    desc = page.meta.get("description", "")
    if not 50 <= len(desc) <= 170:
        add("WARN", "META-DESCRIPTION", f"{len(desc)} characters (want 50-170)")
    vp = page.meta.get("viewport", "")
    if "user-scalable=no" in vp.replace(" ", "") or re.search(r"maximum-scale=1(\.0)?(,|$)", vp.replace(" ", "")):
        add("FAIL", "VIEWPORT", "zoom is disabled; remove user-scalable=no / maximum-scale=1")
    if page.mismatch:
        add("FAIL", "HTML-BALANCE", "; ".join(page.mismatch[:5]))
    if page.stack:
        add("FAIL", "HTML-BALANCE", f"unclosed tags at end: {page.stack[-5:]}")
    dup = sorted({i for i in page.ids if page.ids.count(i) > 1})
    if dup:
        add("FAIL", "DUPLICATE-ID", ", ".join(dup))
    if page.inline_styles:
        add("WARN", "INLINE-STYLE", f"{page.inline_styles} style= attribute(s); use classes from site.css")
    if page.style_blocks:
        add("WARN", "STYLE-BLOCK", f"{page.style_blocks} <style> block(s) in HTML; move CSS to site.css")
    for f in page.fields:
        if f and f not in page.labels_for:
            add("FAIL", "FORM-LABEL", f"field #{f} has no <label for>")
    for target in page.labels_for:
        if target not in page.ids:
            add("FAIL", "FORM-LABEL", f"<label for='{target}'> points at nothing")


def check_links(page):
    ids = set(page.ids)
    for a in page.anchors:
        href = (a["href"] or "").strip()
        name = (a["text"].strip() or (a["aria-label"] or "") or (a["img_alt"] or "")).strip()
        label = name or href
        if not name and a["aria-hidden"] != "true":
            add("FAIL", "LINK-NAME", f"link to '{href}' has no accessible name")
        if href in ("", "#") and name not in ALLOW_HASH_TEXT:
            add("FAIL", "DEAD-LINK", f"'{label}' has href='{href}'")
        elif href.lower().startswith("javascript:"):
            add("FAIL", "JS-LINK", f"'{label}' uses a javascript: URL; use a real href plus a script handler")
        elif href.startswith("#") and len(href) > 1 and href[1:] not in ids:
            add("FAIL", "ANCHOR", f"'{label}' links to {href}, which does not exist")
        if a["target"] == "_blank" and "noopener" not in a["rel"]:
            add("WARN", "REL-NOOPENER", f"'{label}' opens a new tab without rel=noopener")
        parsed = urlparse(href)
        if href and not parsed.scheme and not href.startswith(("#", "mailto:")):
            if not (ROOT / unquote(parsed.path)).exists():
                add("FAIL", "MISSING-FILE", f"'{label}' -> {href} does not exist")


def check_images(page):
    seen = set()
    for im in page.imgs:
        src = im.get("src", "")
        if "alt" not in im:
            add("FAIL", "IMG-ALT", f"{src}: no alt attribute (use alt=\"\" only for decorative images)")
        if not (im.get("width") and im.get("height")):
            add("WARN", "IMG-SIZE", f"{src}: no width/height attributes (causes layout shift)")
        path = ROOT / unquote(src)
        if src in seen or not src or urlparse(src).scheme:
            continue
        seen.add(src)
        if not path.exists():
            add("FAIL", "MISSING-FILE", f"image {src} does not exist")
            continue
        kb = path.stat().st_size // 1024
        if kb > IMG_FAIL_KB:
            add("FAIL", "IMG-WEIGHT", f"{src} is {kb} KB (limit {IMG_FAIL_KB}); resize, see DESIGN.md")
        elif kb > IMG_WARN_KB:
            add("WARN", "IMG-WEIGHT", f"{src} is {kb} KB (target under {IMG_WARN_KB})")
        size = jpeg_size(path)
        if size and size[0] > IMG_MAX_WIDTH:
            add("WARN", "IMG-DIMENSIONS", f"{src} is {size[0]}px wide (max {IMG_MAX_WIDTH})")
    # CSS background images
    for css in ROOT.glob("assets/css/*.css"):
        for m in re.finditer(r"url\(['\"]?\.\./\.\./(images/[^'\")]+)['\"]?\)", css.read_text(encoding="utf-8")):
            p = ROOT / unquote(m.group(1))
            if p.exists() and p.stat().st_size // 1024 > 1024:
                add("WARN", "IMG-WEIGHT", f"{m.group(1)} (CSS background) is {p.stat().st_size // 1024} KB; target under 1024")


def tokens(css):
    root = re.search(r":root\s*\{(.*?)\n\}", css, re.S)
    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", root.group(1))) if root else {}


def check_css():
    path = ROOT / "assets/css/site.css"
    if not path.exists():
        add("FAIL", "SITE-CSS", "assets/css/site.css is missing")
        return
    css = path.read_text(encoding="utf-8")
    t = tokens(css)
    hexval = lambda name: re.search(r"#[0-9a-fA-F]{3,6}", t.get(name, "")).group(0) if re.search(r"#[0-9a-fA-F]{3,6}", t.get(name, "")) else None
    pairs = [("--color-text", "--color-surface", 4.5), ("--color-meta", "--color-surface", 4.5),
             ("--color-ink", "--color-surface", 4.5), ("--color-accent-strong", "--color-surface", 4.5),
             ("--color-accent-strong", "--color-page", 4.5), ("--color-ink", "--color-tint", 4.5)]
    for fg, bg, want in pairs:
        a, b = hexval(fg), hexval(bg)
        if a and b:
            r = contrast(a, b)
            if r < want:
                add("FAIL", "CONTRAST", f"{fg} on {bg} is {r:.2f}:1 (need {want}:1)")
        else:
            add("WARN", "CONTRAST", f"could not read {fg} / {bg} from :root")
    white_on = hexval("--color-accent-strong")
    if white_on and contrast("#ffffff", white_on) < 4.5:
        add("FAIL", "CONTRAST", f"white on --color-accent-strong is {contrast('#ffffff', white_on):.2f}:1")
    outside = re.sub(r":root\s*\{.*?\n\}", "", css, flags=re.S)
    outside = re.sub(r"/\*.*?\*/", "", outside, flags=re.S)
    for hx in sorted(set(re.findall(r"#[0-9a-fA-F]{3,8}\b", outside))):
        if hx.lower() not in ("#fff", "#ffffff"):
            add("WARN", "TOKEN-COLOR", f"hard-coded color {hx} in site.css; add a token to :root")
    for m in SPACING_PROPS.finditer(outside):
        for val in m.group(4).split():
            if val in ("0", "auto") or val.startswith(("var(", "calc(")) or val in ("-1px",):
                continue
            if re.fullmatch(r"-?[\d.]+(rem|px|em)", val):
                add("WARN", "TOKEN-SPACING", f"{m.group(1)}{m.group(2) or ''}: {val}; use a --space-* token")
    for name, val in t.items():
        if name.startswith("--tap-target"):
            continue


def visible_text(page):
    return " ".join(page.text + page.attr_text)


def never_say(profile_md):
    section = re.search(r"## Never say.*?\n(.*?)(?=\n## |\Z)", profile_md, re.S)
    out = []
    if section:
        for line in section.group(1).splitlines():
            if line.startswith("- "):
                pats = re.findall(r"`([^`]+)`", line.split("—")[0])
                out += [(p.strip(), line.split("—", 1)[-1].strip()) for p in pats if p.strip() not in ("/",)]
    return out


def check_content(page, page_html):
    registry = ROOT.parent / "PROJECTS.md"
    profile = ROOT.parent / "PROFILE.md"
    if not registry.exists():
        add("INFO", "CONTENT", "../PROJECTS.md not found: skipped registry checks")
    else:
        text = visible_text(page)
        for p in projects_md.load(registry):
            title = p.get("title", "")
            present = title in text
            if p.get("status") == "live" and not present:
                add("FAIL", "LIVE-MISSING", f"live project '{title}' is not on the page; run tools/render_projects.py")
            if p.get("status") == "held" and (title in text or any(part.strip() in text for part in title.split(";") if len(part.strip()) > 12)):
                add("FAIL", "HELD-PUBLISHED", f"held project '{title}' appears on the page")
            if p.get("status") == "live":
                if len(p.get("meta", "")) > 38:
                    add("WARN", "CARD-META", f"'{p['meta']}' is {len(p['meta'])} chars (keep under 38 so it fits one line at every card width)")
                for h in p["highlights"]:
                    if h not in text:
                        add("WARN", "HIGHLIGHT-DRIFT", f"'{h[:50]}...' differs from PROJECTS.md; rerun render_projects.py")
        try:
            current = render_projects.render(page_html, projects_md.load(registry)) == page_html
        except SystemExit:
            add("FAIL", "CARDS-STALE", "index.html has no <!-- projects:...:start/end --> markers; cards are not generated from PROJECTS.md")
        else:
            if not current:
                add("FAIL", "CARDS-STALE", "index.html cards are out of date with PROJECTS.md; run tools/render_projects.py")
    if not profile.exists():
        add("INFO", "CONTENT", "../PROFILE.md not found: skipped never-say checks")
        return
    rules = never_say(profile.read_text(encoding="utf-8"))
    corpora = {"page": visible_text(page).lower()}
    pdf = ROOT / "images/Paras_Resume.pdf"
    if pdf.exists():
        try:
            corpora["images/Paras_Resume.pdf"] = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True).stdout.lower()
        except FileNotFoundError:
            add("INFO", "CONTENT", "pdftotext not installed: skipped the resume PDF text check")
    for where, body in corpora.items():
        for pat, why in rules:
            if pat.lower() in body:
                add("FAIL", "NEVER-SAY", f"'{pat}' found in {where}. {why}")
    add("INFO", "CONTENT", f"checked {len(rules)} never-say pattern(s) against {', '.join(corpora)}")


def check_online(page):
    seen = set()
    for a in page.anchors:
        href = a["href"] or ""
        if urlparse(href).scheme in ("http", "https") and href not in seen:
            seen.add(href)
            try:
                req = urllib.request.Request(href, method="HEAD", headers={"User-Agent": "Mozilla/5.0 (site-check)"})
                code = urllib.request.urlopen(req, timeout=8).status
            except urllib.error.HTTPError as e:
                code = e.code
            except Exception as e:
                add("WARN", "LINK-CHECK", f"{href}: {type(e).__name__}")
                continue
            if code >= 400 and code not in (401, 403, 405, 429, 999):
                add("FAIL", "DEAD-LINK", f"{href} returned {code}")
    add("INFO", "LINK-CHECK", f"checked {len(seen)} external link(s); social sites that block bots may be skipped")


def main():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    page = Page()
    page.feed(html)
    check_html(page, html)
    check_links(page)
    check_images(page)
    check_css()
    check_content(page, html)
    if "--online" in sys.argv:
        check_online(page)
    order = {"FAIL": 0, "WARN": 1, "INFO": 2}
    for sev, cid, msg in sorted(findings, key=lambda f: (order[f[0]], f[1])):
        print(f"{sev:4}  {cid:16} {msg}")
    fails = sum(1 for f in findings if f[0] == "FAIL")
    warns = sum(1 for f in findings if f[0] == "WARN")
    print(f"\n{fails} fail, {warns} warn")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

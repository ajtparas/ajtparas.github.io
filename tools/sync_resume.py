#!/usr/bin/env python3
"""Publish the current tailored resume as the site's public resume PDF.

The site links to images/Paras_Resume.pdf. That file is a copy, so it goes
stale the moment a new resume is built. This script re-copies it from
../resume/tailored/ and refuses to publish one that fails the never-say scan.

    python3 tools/sync_resume.py              # newest PDF under ../resume/tailored/
    python3 tools/sync_resume.py --list       # show candidates, change nothing
    python3 tools/sync_resume.py --from <p>   # publish a specific PDF

Run check_site.py afterwards. Pushing is still manual and deliberate.
"""
import argparse, filecmp, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # portfolio/
TAILORED = ROOT.parent / "resume" / "tailored"
DEST = ROOT / "images" / "Paras_Resume.pdf"


def candidates():
    if not TAILORED.exists():
        return []
    return sorted(TAILORED.rglob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)


def never_say_patterns():
    """Reuse check_site.py's rules so the two can't disagree."""
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import check_site
        profile = ROOT.parent / "PROFILE.md"
        if not profile.exists():
            return None
        return check_site.never_say(profile.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  ! could not load never-say rules from check_site.py ({e})")
        return None


def scan(pdf):
    rules = never_say_patterns()
    if rules is None:
        print("  ! never-say rules unavailable; run check_site.py before you push")
        return True
    try:
        text = subprocess.run(["pdftotext", str(pdf), "-"],
                              capture_output=True, text=True).stdout.lower()
    except FileNotFoundError:
        print("  ! pdftotext not installed; could not scan the PDF text")
        return True
    hits = [(pat, why) for pat, why in rules if pat in text]
    for pat, why in hits:
        print(f"  FAIL  '{pat}' found in the PDF. {why}")
    if not hits:
        print(f"  ok    scanned {len(rules)} never-say pattern(s), none found")
    return not hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", help="path to the PDF to publish")
    ap.add_argument("--list", action="store_true", help="show candidates and exit")
    args = ap.parse_args()

    found = candidates()

    if args.list:
        if not found:
            print(f"no PDFs under {TAILORED}")
            return 0
        print(f"candidates under {TAILORED}, newest first:\n")
        for p in found:
            same = DEST.exists() and filecmp.cmp(p, DEST, shallow=False)
            print(f"  {'* published  ' if same else '             '}{p.relative_to(TAILORED)}")
        return 0

    if args.src:
        src = Path(args.src).resolve()
    elif found:
        src = found[0]
    else:
        print(f"No resume PDF found under {TAILORED}. Build one first, or pass --from.")
        return 1

    if not src.exists():
        print(f"Not found: {src}")
        return 1

    print(f"source      {src}")
    print(f"destination {DEST}")

    if DEST.exists() and filecmp.cmp(src, DEST, shallow=False):
        print("\nAlready identical, nothing to do.")
        return 0

    if not scan(src):
        print("\nRefusing to publish: the PDF contains a withdrawn claim.")
        return 1

    DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, DEST)
    print("\nPublished. Now run: python3 tools/check_site.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())

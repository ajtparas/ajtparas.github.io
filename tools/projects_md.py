"""Parse the project registry (../PROJECTS.md) into dicts. Shared by render_projects.py and check_site.py.

The registry lives one folder above this repo and is private; the site only ever receives the
fields of projects whose status is `live`.
"""
import re
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[2] / "PROJECTS.md"


def load(path=REGISTRY):
    if not Path(path).exists():
        raise FileNotFoundError(f"Project registry not found: {path}")
    text = Path(path).read_text(encoding="utf-8")
    projects = []
    for chunk in re.split(r"^### ", text, flags=re.M)[1:]:
        pid, _, body = chunk.partition("\n")
        pid = pid.strip()
        if not re.search(r"^- \*\*status:\*\*", body, flags=re.M):
            continue  # a heading that isn't a project entry
        project = {"id": pid, "highlights": []}
        lines = body.splitlines()
        i = 0
        while i < len(lines):
            m = re.match(r"- \*\*([^*]+):\*\*\s*(.*)", lines[i])
            if m:
                key, val = m.group(1).strip().lower().replace(" ", "_"), m.group(2).strip()
                if key == "highlights":
                    i += 1
                    while i < len(lines) and re.match(r"\s+- ", lines[i]):
                        project["highlights"].append(re.sub(r"^\s+- ", "", lines[i]).strip())
                        i += 1
                    continue
                project[key] = val
            i += 1
        projects.append(project)
    return projects


def links(project):
    """'GitHub | https://... ; Report | https://...' -> [(label, url)]. 'none ...' -> []"""
    raw = project.get("links", "none")
    if raw.lower().startswith("none"):
        return []
    out = []
    for part in raw.split(";"):
        label, _, url = part.partition("|")
        if url.strip():
            out.append((label.strip(), url.strip()))
    return out


def tags(project):
    return [t.strip() for t in project.get("tags", "").split(",") if t.strip()]

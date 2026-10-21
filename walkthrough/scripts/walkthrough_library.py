"""Store walkthroughs and rebuild a local gallery shared by independent skills."""

from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import quote, urlparse


ENTRY_NAME = ".walkthrough-entry.json"
COLORS = {"blue": "#70a5ff", "green": "#6cddb3", "amber": "#f4c876", "pink": "#ef88ca", "purple": "#ae98ef", "red": "#ed8b89", "slate": "#91a1b7"}


def library_root(root: Path | None = None) -> Path:
    return (root if root is not None else Path.home() / ".agents" / "walkthroughs").expanduser().resolve()


def slug(value: object, limit: int = 48) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")[:limit].rstrip("-") or "untitled"


def repository_name(meta: dict) -> str:
    address = str(meta.get("repository_url") or meta.get("pr_url") or "")
    parts = [part for part in urlparse(address).path.split("/") if part]
    if parts:
        if "pull" in parts:
            parts = parts[:parts.index("pull")]
        return "/".join(parts[-2:]).removesuffix(".git")
    return "Standalone" if meta.get("snapshot", {}).get("kind") == "snippet" else "Local source"


def default_output(data: dict, kind: str, root: Path | None = None) -> Path:
    meta = data.get("meta", {})
    snapshot = meta.get("snapshot", {})
    identity = snapshot.get("sha") or meta.get("head_sha") or "files"
    # The data digest distinguishes repositories, local snapshots and regenerated stories.
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
    directory = f"{kind}-{slug(repository_name(meta), 36)}-{slug(meta.get('title', 'walkthrough'))}-{slug(identity, 12)}-{digest}"
    return library_root(root) / directory / "index.html"


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix=".walkthrough-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def preview_svg(data: dict) -> str:
    visual = next(iter(data.get("visuals", [])), {})
    nodes = visual.get("nodes", [])
    if not nodes:
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 180"><text x="20" y="90">Walkthrough</text></svg>'
    def number(value: object) -> float:
        value = float(value)
        if not math.isfinite(value):
            raise ValueError("Preview coordinates must be finite")
        return value
    positions = {n["id"]: (number(n["x"]), number(n["y"])) for n in nodes}
    xs, ys = zip(*positions.values())
    bounds = (min(xs)-85, min(ys)-45, max(200, max(xs)-min(xs)+170), max(100, max(ys)-min(ys)+90))
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="{" ".join(map(str, bounds))}">', '<title>Diagram preview (2D)</title>']
    for edge in visual.get("edges", []):
        if edge["source"] not in positions or edge["target"] not in positions:
            continue
        x1, y1 = positions[edge["source"]]; x2, y2 = positions[edge["target"]]
        parts.append(f'<path d="M{x1} {y1} L{x2} {y2}" stroke="#71809b" stroke-width="2"/>')
    for node in nodes:
        x, y = positions[node["id"]]
        color = COLORS.get(node.get("color"), COLORS["slate"])
        label = str(node.get("label", ""))
        short = label if len(label) <= 22 else label[:21] + "…"
        parts.append(f'<g><title>{html.escape(label)}</title><rect x="{x-75}" y="{y-25}" width="150" height="50" rx="8" fill="#172235" stroke="{color}"/><text x="{x}" y="{y+4}" fill="#e8edf5" text-anchor="middle" font-family="system-ui,sans-serif" font-size="11">{html.escape(short)}</text></g>')
    return "".join(parts) + "</svg>"


@contextmanager
def gallery_lock(root: Path):
    # Serialize read/rebuild/replace so simultaneous code and PR renders retain both entries.
    with (root / ".gallery.lock").open("a") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def rebuild_gallery(root: Path) -> Path:
    entries = []
    for manifest in sorted(root.rglob(ENTRY_NAME)):
        if not manifest.resolve().is_relative_to(root):
            continue
        entry = json.loads(manifest.read_text(encoding="utf-8"))
        page = (manifest.parent / entry["page"]).resolve()
        preview = (manifest.parent / entry["preview"]).resolve()
        if not page.is_relative_to(root) or not preview.is_relative_to(root) or not page.is_file():
            continue
        entries.append(entry | {"url": quote(page.relative_to(root).as_posix()), "image": quote(preview.relative_to(root).as_posix())})
    entries.sort(key=lambda item: (item["generated_at"], item["url"]), reverse=True)
    cards = []
    for entry in entries:
        escape = html.escape
        search = " ".join(str(entry.get(key, "")) for key in ("title", "repository", "target", "snapshot", "kind")).casefold()
        cards.append(f'<article class="card" data-search="{escape(search, quote=True)}" data-kind="{escape(entry["kind"], quote=True)}" data-repo="{escape(entry["repository"], quote=True)}"><a href="{escape(entry["url"], quote=True)}"><img loading="lazy" src="{escape(entry["image"], quote=True)}" alt="Diagram preview (2D)"><div class="body"><p class="meta">{escape(entry["repository"])} · {escape(entry["kind"].upper())}</p><h2>{escape(entry["title"])}</h2><p>{escape(entry["intent"])}</p><p class="meta">{escape(entry["generated_at"])} · {escape(entry["snapshot"])}</p><p class="meta">{entry["steps"]} chapters · {entry["diagrams"]} diagrams</p></div></a></article>')
    repositories = sorted({entry["repository"] for entry in entries})
    options = "".join(f'<option value="{html.escape(repo, quote=True)}">{html.escape(repo)}</option>' for repo in repositories)
    document = GALLERY_TEMPLATE.replace("__CARDS__", "\n".join(cards)).replace("__REPOSITORIES__", options).replace("__COUNT__", str(len(entries)))
    atomic_write(root / "index.html", document)
    return root / "index.html"


def register(data: dict, output: Path, kind: str, root: Path | None = None) -> Path | None:
    root = library_root(root)
    output = output.expanduser().resolve()
    if not output.is_relative_to(root):
        return None  # Respect explicitly requested outputs outside the library.
    if output.parent == root:
        raise ValueError("Store the walkthrough in its own folder; the library index is reserved for the gallery")
    meta = data.get("meta", {})
    snapshot = meta.get("snapshot", {})
    entry = dict(kind=kind, title=str(meta.get("title", "Walkthrough")), intent=str(meta.get("intent", "")), target=str(meta.get("target", "")), repository=repository_name(meta), generated_at=str(meta.get("generated_at", "")), snapshot=str(snapshot.get("label") or meta.get("head_sha", "")[:12]), steps=len(data.get("steps", [])), diagrams=len(data.get("visuals", [])), page=output.name, preview="preview.svg")
    atomic_write(output.parent / "walkthrough-data.json", json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    atomic_write(output.parent / "preview.svg", preview_svg(data))
    with gallery_lock(root):
        atomic_write(output.parent / ENTRY_NAME, json.dumps(entry, indent=2) + "\n")
        return rebuild_gallery(root)


GALLERY_TEMPLATE = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Walkthrough library</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#0c1018;color:#e8edf5;font:15px/1.55 system-ui,sans-serif}main{max-width:1400px;margin:auto;padding:36px 24px}h1{font-size:34px;margin:0}header p{color:#a6b4ca;max-width:800px}a{color:inherit;text-decoration:none}.controls{display:flex;gap:12px;flex-wrap:wrap;margin:26px 0}input,select{background:#172030;color:inherit;border:1px solid #40506a;border-radius:8px;padding:12px;font:inherit;max-width:100%}input{flex:1;min-width:180px}#grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:20px}.card{border:1px solid #344259;border-radius:12px;overflow:hidden;background:#131b29;max-width:600px}.card a{display:block;height:100%}.card:hover,.card:focus-within{border-color:#70a5ff}.card img{display:block;width:100%;height:200px;padding:22px;background:#0c1422}.body{padding:20px}.body h2{font-size:20px;line-height:1.3;margin:8px 0}.body p{overflow-wrap:anywhere}.meta{color:#a6b4ca;font-size:12px}.card[hidden]{display:none}:focus-visible{outline:3px solid #70a5ff;outline-offset:3px}#empty{color:#a6b4ca}@media(max-width:600px){main{padding:24px 16px}h1{font-size:28px}select{width:100%}}
</style></head><body><main><header><h1>Walkthrough library</h1><p>Code and PR walkthroughs from your agents. Browse recent explanations or search by title, repository, target, or snapshot.</p></header>
<div class="controls" role="search"><input id="search" type="search" aria-label="Search walkthroughs" placeholder="Search walkthroughs…"><select id="repository" aria-label="Filter by repository"><option value="">All repositories</option>__REPOSITORIES__</select><select id="kind" aria-label="Filter by walkthrough type"><option value="">Code and PR</option><option value="code">Code</option><option value="pr">PR</option></select></div>
<p id="count" class="meta" aria-live="polite">__COUNT__ walkthroughs</p><section id="grid" aria-label="Walkthroughs">__CARDS__</section><p id="empty" hidden>No matching walkthroughs.</p>
</main><script>
const cards=[...document.querySelectorAll('.card')];
function filter(){const query=document.getElementById('search').value.toLocaleLowerCase();const repo=document.getElementById('repository').value;const kind=document.getElementById('kind').value;let count=0;for(const card of cards){card.hidden=!(card.dataset.search.includes(query)&&(!repo||card.dataset.repo===repo)&&(!kind||card.dataset.kind===kind));if(!card.hidden)count++;}document.getElementById('count').textContent=count+' walkthrough'+(count===1?'':'s');document.getElementById('empty').hidden=count>0;}
for(const id of ['search','repository','kind'])document.getElementById(id).addEventListener('input',filter);
filter();
</script></body></html>'''

# Code walkthrough artifact contract

The bundled renderer accepts one JSON document and injects it into a local, self-contained HTML template.

## Top-level shape

```json
{
  "meta": {},
  "files": [],
  "code": [],
  "visuals": [],
  "steps": [],
  "findings": [],
  "coverage": {}
}
```

## `meta`

```json
{
  "title": "Request handling walkthrough",
  "intent": "Explain how requests become durable jobs.",
  "target": "src/server.py and its service calls",
  "repository_url": "https://github.com/owner/repo",
  "snapshot": {
    "kind": "git",
    "label": "main at the captured commit",
    "ref": "main",
    "sha": "40- or 64-character Git commit ID"
  },
  "generated_at": "ISO-8601 timestamp",
  "code_involved": true
}
```

`repository_url` is optional; omit it or use an empty string when no remote is available. `target` describes the selected scope. `snapshot` is required and has a non-empty human-readable `label` plus one of these forms:

- `kind: "git"`: `ref` and an immutable `sha` (40 or 64 hexadecimal characters). All excerpts come from that revision; Git is used only for committed source.
- `kind: "files"` or `kind: "snippet"`: a non-empty `sources` array with unique `path` identifiers and a 64-character hexadecimal `sha256` for each captured source. Hash original file bytes or exact UTF-8 snippet/cell text. Every catalogued source must be covered; use the enclosing notebook path for a cell identifier.

For example, a standalone function can use:

```json
{"kind":"snippet","label":"Supplied function, captured text","sources":[{"path":"snippet-1","sha256":"64-character SHA-256 digest"}]}
```

A working-tree target uses `files` and content digests even when `HEAD` is known. A commit SHA alone cannot identify uncommitted code. Never invent a commit or require Git for standalone code.

## `files`

Each evidence-bearing file record requires:

```json
{
  "path": "src/server.py",
  "role": "story-critical",
  "purpose": "HTTP entry point and application wiring",
  "source_url": "https://github.com/owner/repo/blob/<sha>/src/server.py"
}
```

`role` is `story-critical`, `supporting`, `deemphasized`, or `unresolved`. This is a representative evidence inventory within the selected scope. `path` may be a supplied snippet identifier or `analysis.ipynb#cell-<id>`. Use an empty `source_url` when there is no remote source.

## `code`

```json
{
  "id": "request-entry",
  "label": "Route requests into the service layer",
  "path": "src/server.py",
  "language": "python",
  "side": "context",
  "start_line": 41,
  "end_line": 52,
  "content": "exact source text",
  "emphasis": [43, 44, 49],
  "source_url": "https://github.com/owner/repo/blob/<sha>/src/server.py#L41-L52"
}
```

The line range must match the exact content. For a snippet or notebook cell, use lines within that source and the same identifier as its file record. Use an empty `source_url` when no remote exists. Do not synthesize code or use screenshots of code.

## `visuals`

```json
{
  "id": "request-flow",
  "title": "Request to durable state",
  "mode": "2d",
  "caption": "The API validates input before the service writes state and emits an event.",
  "nodes": [
    {"id":"api","label":"API","detail":"Validates requests","x":80,"y":160,"z":0,"color":"blue"}
  ],
  "edges": [
    {"source":"api","target":"service","label":"validated command","style":"solid"}
  ]
}
```

`mode` is `2d` or `3d`; coordinates are required. In 3D at least one node has non-zero `z`. Supported colors are `blue`, `green`, `amber`, `pink`, `purple`, `red`, and `slate`. Edge style is `solid` or `dashed`.

## `steps`

```json
{
  "id": "primary-flow",
  "kind": "behavior",
  "kicker": "Primary journey",
  "title": "A request becomes a durable job",
  "takeaway": "The API owns validation; the service owns persistence and dispatch.",
  "narrative": ["One or two short factual paragraphs."],
  "visual_id": "request-flow",
  "focus_node_ids": ["api", "service"],
  "code_ids": ["request-entry"],
  "evidence": [{"label":"Pinned source","url":"https://github.com/..."}]
}
```

`kind` is `intent`, `architecture`, `mechanism`, `behavior`, `proof`, `risk`, or `coverage`. Every step needs a valid visual. Attach code to relevant architecture, mechanism, behavior, proof, and risk steps.

For a codebase or broad subsystem, order steps for progressive disclosure:

- Open with the useful outcome, intended user, and motivation in plain language.
- Follow with a compact input → transformation → output flow that avoids internal names.
- Summarize the small set of design ideas needed to understand the approach.
- Put owners, process details, code, state, tests, operations, and risks in later optional deep dives. Label their `kicker` clearly, for example `Deep dive / runtime flow`.

The overview must stand on its own. Keep each overview narrative to one to three short paragraphs and avoid exhaustive lists of roles, phases, files, exceptions, or evidence. A function or small snippet can use a shorter contract → behavior → edge-cases arc instead.

## `findings`

Each finding requires `severity`, `confidence`, `title`, `trigger`, `impact`, `evidence`, `resolution`, and `url`. Severity is `blocking`, `important`, or `optional`; confidence is `high`, `medium`, or `low`. Use an empty array when no actionable finding relevant to the selected code was verified.

## `coverage`

```json
{
  "represented": ["src/server.py"],
  "deemphasized": [{"path":"vendor/lock.json","reason":"generated dependency resolution"}],
  "unresolved": [],
  "evidence_gaps": ["Deployment manifests are maintained in another repository"]
}
```

Every `files[].path` appears exactly once across `represented`, `deemphasized[].path`, and `unresolved`. State broader excluded areas and inaccessible external systems in `evidence_gaps`.

## Output and validation

Render and validate:

```bash
python3 scripts/render_walkthrough.py --data data.json --output .walkthrough/code-<target>-<snapshot-id>/index.html
python3 scripts/validate_walkthrough.py --html .walkthrough/code-<target>-<snapshot-id>/index.html
```

The renderer embeds all data and runtime code in one file without network dependencies. The validator checks schema references, line ranges, coverage accounting, required UI contracts, snapshot metadata shape, and external runtime dependencies. It does not read source files or Git: compare excerpts to captured source and recheck the selected ref or content digests separately before handoff. Browser QA remains required for layout and interaction confidence.

# Artifact contract

The bundled renderer accepts one JSON document and injects it into a local HTML template. Use snake_case keys exactly as shown.

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

Required fields:

```json
{
  "title": "Add bounded retry scheduling",
  "intent": "Prevent transient worker failures from dropping jobs.",
  "target": "PR #123",
  "pr_url": "https://github.com/owner/repo/pull/123",
  "base_ref": "main",
  "head_ref": "bounded-retries",
  "base_sha": "40-character SHA",
  "head_sha": "40-character SHA",
  "generated_at": "ISO-8601 timestamp",
  "code_involved": true
}
```

Use an empty `pr_url` for local-only changes. Immutable SHAs remain required; for an uncommitted target, use the current HEAD for `head_sha` and describe staged/working-tree scope in `target` and `coverage.evidence_gaps`.

## `files`

Each changed file record requires `path`, `status`, `additions`, `deletions`, `role`, and `diff_url`. `role` is one of `story-critical`, `supporting`, `mechanical`, or `unresolved`.

## `code`

```json
{
  "id": "retry-loop",
  "label": "Bound retries at the queue boundary",
  "path": "src/worker/retry.py",
  "language": "python",
  "side": "new",
  "start_line": 41,
  "end_line": 52,
  "content": "exact source text",
  "emphasis": [43, 44, 49],
  "diff_url": "https://github.com/owner/repo/pull/123/files#...R43"
}
```

`side` is `old`, `new`, `diff`, or `context`. The line range must match the excerpt for old/new/context sides. `emphasis` contains source line numbers; for a diff excerpt it may be empty.

## `visuals`

```json
{
  "id": "retry-flow",
  "title": "Failure to retry path",
  "mode": "2d",
  "caption": "Retries return through the scheduler; terminal failures go to the dead-letter queue.",
  "nodes": [
    {"id": "worker", "label": "Worker", "detail": "Runs the job", "x": 80, "y": 160, "z": 0, "color": "blue"}
  ],
  "edges": [
    {"source": "worker", "target": "scheduler", "label": "retryable failure", "style": "solid"}
  ]
}
```

`mode` is `2d` or `3d`. Coordinates are required. In 2D, `z` may be zero. In 3D, depth must be meaningful and at least one node must have a non-zero `z`. Supported colors are `blue`, `green`, `amber`, `pink`, `purple`, `red`, and `slate`. Edge `style` is `solid` or `dashed`.

## `steps`

```json
{
  "id": "mechanism",
  "kind": "mechanism",
  "kicker": "Key mechanism",
  "title": "Retry policy now lives at the queue boundary",
  "takeaway": "Workers report failure; the scheduler owns whether another attempt exists.",
  "narrative": ["One or two short factual paragraphs."],
  "visual_id": "retry-flow",
  "focus_node_ids": ["worker", "scheduler"],
  "code_ids": ["retry-loop"],
  "evidence": [{"label": "Changed retry loop", "url": "https://github.com/..."}],
  "camera": {"rotation_x": -0.15, "rotation_y": 0.35, "zoom": 1.15}
}
```

`kind` is `intent`, `architecture`, `mechanism`, `behavior`, `proof`, `risk`, or `coverage`. Every step needs a valid visual. Code-bearing changes need code attached to the relevant architecture/mechanism/behavior/proof/risk steps. `camera` is optional and primarily useful for 3D scenes.

## `findings`

Each finding requires `severity`, `confidence`, `title`, `trigger`, `impact`, `evidence`, `resolution`, and `url`. Severity is `blocking`, `important`, or `optional`; confidence is `high`, `medium`, or `low`. Use an empty array when no actionable findings were verified.

## `coverage`

Required arrays:

```json
{
  "represented": ["src/worker/retry.py"],
  "deemphasized": [{"path": "lockfile", "reason": "generated dependency resolution"}],
  "unresolved": [],
  "evidence_gaps": ["No linked rollout dashboard"]
}
```

Every `files[].path` must appear exactly once across `represented`, `deemphasized[].path`, and `unresolved`.

## Output and validation

Escape external text as data; do not inject it as HTML. The renderer embeds all structured data and runtime code in one file and has no runtime network dependency.

Render and validate:

```bash
python3 scripts/render_walkthrough.py --data data.json --output .walkthrough/change/index.html
python3 scripts/validate_walkthrough.py --html .walkthrough/change/index.html
```

The validator checks schema references, line ranges, coverage accounting, required UI contracts, inline data, and unpinned/external runtime dependencies. Browser QA remains required for layout and interaction confidence.

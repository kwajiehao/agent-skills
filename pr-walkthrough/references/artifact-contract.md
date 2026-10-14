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

Use an empty `pr_url` for local-only changes. Immutable SHAs remain required; for an uncommitted target, use the current HEAD for `head_sha` and collect staged/working fingerprints as described below. Keep `base_ref` and `head_ref` from collection so validation can detect moved refs. For intentionally immutable historical targets, pass the full SHAs as refs.

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

`side` is `old`, `new`, `diff`, or `context`. The line range must match the excerpt. Diff ranges index the collector's per-file unified diff, including `---`/`+++` headers and newline markers. `context` also requires `revision` equal to the full base or head SHA. `emphasis` contains source line numbers; for a diff excerpt it may be empty. Content is exact selected text with line separators normalized to `\n` and no terminal separator.

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
  "claim_status": "demonstrated",
  "evidence": [{"label": "Changed retry loop", "code_id": "retry-loop"}],
  "camera": {"rotation_x": -0.15, "rotation_y": 0.35, "zoom": 1.15}
}
```

`kind` is `intent`, `architecture`, `mechanism`, `behavior`, `proof`, `risk`, or `coverage`. Every step needs a valid visual. Code-bearing changes need code attached to the relevant architecture/mechanism/behavior/proof/risk steps. `camera` is optional and primarily useful for 3D scenes.

Source-bound validation requires `claim_status`: `stated`, `demonstrated`, `inferred`, `disputed`, or `unknown`. Stated/demonstrated/disputed claims need nonempty typed evidence. Inferred/unknown claims without evidence require a nonempty `evidence_gap`, rendered beside the claim. Each evidence record has a `label` and exactly one of `code_id` (an existing source-verified excerpt) or `url` (absolute HTTP(S)). URL records require `source_kind`: `spec`, `issue`, `pr`, `comment`, `check`, `benchmark`, or `manual`. URL contents and semantic entailment remain manual checks; a source link is not execution proof.

## `findings`

Each finding requires `severity`, `confidence`, `title`, `trigger`, `impact`, `evidence`, `resolution`, and `url`. Source-bound findings use the same `claim_status`, typed evidence records, and gap policy as steps. Severity is `blocking`, `important`, or `optional`; confidence is `high`, `medium`, or `low`. Use an empty array when no actionable findings were verified. Legacy string evidence can still render but does not pass source-bound validation.

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
python3 scripts/render_walkthrough.py --data data.json
python3 scripts/validate_walkthrough.py --html <rendered-path> --repo <repo-root>
```

By default the renderer writes an artifact folder under `~/.agents/walkthroughs/` and reports its path. Each library artifact contains the HTML, `walkthrough-data.json`, `preview.svg`, and `.walkthrough-entry.json`; source captures and supporting assets belong beside them. The root `index.html` is the shared searchable gallery and is reserved for that purpose. An explicit `--output` outside the library is respected without registering it. `--library-root` overrides the default library for isolated tests or a user-selected destination. Metadata labels retain the captured snapshot; the gallery does not validate live source freshness.

Without `--repo`, validation checks structure only: schema references, line ranges, coverage accounting, required UI contracts, inline data, and unpinned/external runtime dependencies. It prints an explicit warning and does not verify source text or freshness. Browser QA remains required for layout and interaction confidence. The bundled example is synthetic renderer data and is not a source-verified review.

## Source-bound verification

Run `scripts/source_evidence.py --repo <repo-root> --base <ref> --head <ref> --mode committed` and preserve returned `meta.source_snapshot` unchanged. `--mode staged` compares base to the index; `--mode working` compares base to tracked working contents and untracked source, and independently fingerprints the index. Collection is read-only and fails on Git errors, merge conflicts, changed files during collection, and dirty submodules rather than presenting incomplete evidence as verified.

The manifest contains version, mode, base/head SHAs, base/target tree digests, local index digest when relevant, explicit untracked output exclusions, and a SHA-256 digest of those fields. Fingerprints cover file content and modes. They establish freshness relative to collection, not authenticity against someone intentionally rewriting both evidence and digests.

Default untracked exclusion: `.walkthrough`. Override with repeatable `--exclude-untracked <relative-path>` when an explicitly selected output directory should not be reviewed. Tracked files are never excluded. Preserve this list in the snapshot and disclose any additional exclusion in coverage. Avoid excluding product sources to make validation pass.

The collector derives inventory from complete Git endpoint entries and reports renames as added/deleted paths. Text counts and diff excerpts use Git's Myers diff over observed bytes in an isolated temporary directory, without repository textconv/clean filters. Binary changes receive zero text counts and `binary: true`; account for their effect separately. Text line endings are normalized in excerpts; blob fingerprints still detect byte differences. SHA-1 Git repositories and UTF-8 paths/text are supported; source blobs larger than 16 MiB fail explicitly rather than silently truncating evidence. Symlinks are inventoried by link text and cannot be used as source excerpts. Context reads are limited to immutable endpoint SHAs; paths cannot escape the repository.

`--repo` validation checks source snapshots, current target refs, exact source/diff excerpts, full inventory and counts, and evidence-link targets. It does not claim to judge whether prose follows logically from code, whether linked external records exist, whether tests executed, or whether a visual accurately models behavior. Inspect those separately and label execution gaps.

To collect an excerpt, add `--path src/file.py --side new --start 10 --end 18` with the same collection arguments. Add its returned fields to a code record plus editorial id/label/language/emphasis/link. Use `--side old` for base, `--side diff` for the collector's unified diff, or `--side context --revision <full-base-or-head-sha>` for unchanged context.

# Code discovery and evidence method

Build the walkthrough from runtime ownership and evidence, not from file counts.

## Reader-first model

Before choosing architecture chapters for a broad target, write a plain-language model that answers:

1. What useful outcome does this code produce?
2. Who or what supplies its input?
3. What problem or less desirable approach does it replace?
4. What is the simplest accurate input → transformation → output flow?
5. Which two to four design ideas make that flow possible?

Ground this model in docs, examples, entry points, and tests, then verify it against implementation. Keep intended value (`stated`) distinct from current behavior (`demonstrated`). Explain discrepancies later; do not front-load the overview with every caveat, role, branch, or source path.

## Scope and source capture

Start with the supplied target and the reader's question. Read surrounding context only where it explains the target's behavior or contracts.

| Target | Useful discovery and story |
|---|---|
| Snippet or function | Inputs, outputs, decisions, transformations, side effects, and edge cases |
| Script or file | Execution order, entry points, responsibilities, imports, and observable outcomes |
| Notebook | Cell identities, data dependencies, state, and evidence of execution order |
| Query, style, schema, or infrastructure definition | Evaluation rules, dependencies, constraints, and resulting structures |
| Module or library | Public contracts, internal owners, callers, and representative flows |
| Codebase | Purpose, subsystem boundaries, entry points, journeys, state, tests, and operations |

For committed Git source, resolve the selected ref to an immutable commit and extract from that revision. A file requested in its local state uses its current bytes even if it lives in a repository. Capture all local evidence-bearing files and their SHA-256 digests, including supporting files read outside the selected target. A pasted snippet can use `snippet-1` as its source identifier; hash its exact UTF-8 text. Notebook excerpts use `analysis.ipynb#cell-<id>` and cell-local lines; fingerprint the notebook bytes, or each supplied cell text when the complete notebook is unavailable. Do not invent filesystem paths or remote URLs for supplied code.

Keep the captured source available while composing. For multiple files, verify their digests again after capture and before handoff so the story does not silently mix revisions. Digests establish source identity, not execution proof. If context is unavailable, explain the visible code and label external behavior as unknown.

## Subsystem ledger

Record each important subsystem with:

| Field | Meaning |
|---|---|
| Responsibility | The durable job this subsystem owns |
| Owner paths | Primary source/config/schema locations |
| Entry/callers | How execution reaches it |
| Dependencies | Important upstream and downstream boundaries |
| State | Data read, written, cached, or transmitted |
| Proof | Tests, commands, fixtures, or operational signals |
| Confidence | `high`, `medium`, or `low` |

Prefer a small number of coherent subsystems over mirroring every directory. A package is not automatically an architectural boundary; confirm ownership from imports, registration, configuration, and runtime calls.

## Evidence ledger

Central claims use these statuses:

- `stated`: maintained docs or configuration explicitly says it.
- `demonstrated`: executable code or a test shows it.
- `inferred`: code shape supports it, but intent or runtime proof is absent.
- `disputed`: sources disagree.
- `unknown`: the available source and context cannot answer it.

For each claim, retain an exact source, confidence, and intended story step. Tests demonstrate only the cases they execute. A README may state a design goal without proving the current implementation meets it.

## Discovery order for a codebase

Use an order that minimizes false architecture:

1. Repository instructions and declared purpose.
2. Build/package manifests and executable entry points.
3. Registration, routing, dependency injection, or plugin discovery.
4. Primary request/job/data paths.
5. Persistence, schemas, filesystem layout, and external interfaces.
6. Tests that exercise those paths.
7. Deployment, observability, recovery, and administrative tooling.
8. Remaining top-level areas, generated/vendor/data boundaries, and gaps.

Do not let alphabetical traversal determine the story.

## Representative journeys

Choose journeys by explanatory value, not completeness theater. Prefer flows that cross important boundaries and reveal who owns decisions. For each journey, answer:

- What initiates it?
- Which entry point receives control?
- Which stable boundaries does it cross?
- Where is state read or written?
- What is synchronous, asynchronous, or external?
- How do success and failure become observable?
- Which tests or operational artifacts support the explanation?

When multiple flows share most of their path, teach the common trunk once and branch only where behavior or ownership changes.

For a codebase or subsystem, first compress the representative journey into conceptual stages. Expand the same journey later with owners, state, retries, and code evidence so the overview and deep dive remain one coherent story.

## Coverage model

Catalog evidence-bearing paths as:

- **story-critical**: required to understand purpose, architecture, or a representative journey;
- **supporting**: tests, docs, schemas, config, tooling, or secondary owners that substantiate the story;
- **deemphasized**: generated output, vendor code, fixtures, data, or repetitive implementations intentionally collapsed;
- **unresolved**: relevant purpose or behavior remains unexplained.

The inventory is representative, not a claim that every project file was read. Coverage is relative to the selected scope. For a snippet, catalog its source identifier and note missing callers or dependencies. For a codebase, disclose excluded areas such as vendored trees, build artifacts, large model weights, generated code, or hardware-only paths.

## Architecture review lenses

Use the relevant lenses only after the explanation is coherent. A small target does not require all of them:

1. **Ownership:** split responsibility, circular dependency, task-specific logic in shared layers.
2. **Contracts:** public APIs, schemas, config compatibility, migrations, versioning.
3. **State and lifecycle:** persistence, concurrency, cleanup, retries, crash recovery.
4. **Trust boundaries:** authentication, authorization, secrets, subprocesses, filesystem and network inputs.
5. **Operations:** observability, rollout, rollback, resource isolation, failure diagnosis.
6. **Proof:** integration coverage, negative cases, platform-specific gaps, stale docs.

A displayed finding needs severity, confidence, concrete trigger, observable impact, exact evidence, and an actionable resolution direction. If evidence is incomplete, pose a reviewer question rather than a verdict.

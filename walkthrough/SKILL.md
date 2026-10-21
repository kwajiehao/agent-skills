---
name: walkthrough
description: Build an evidence-linked visual walkthrough of software, systems, architecture, and technical workflows, using synchronized narrative, diagrams, source excerpts, and concrete examples. Use for a general overview or a visual explanation of how a system works. Use code-walkthrough for tracing source block by block from an entrypoint, and pr-walkthrough for a change comparison; do not use for a findings-only review.
---

# Walkthrough

Use this skill for a general visual explanation of a system or technical workflow. The existing code discovery method and interactive artifact tooling below remain available in full. For non-code boundaries, ground the explanation in relevant documentation, configuration, or operational evidence, and distinguish observed behavior from intended design. For a developer reading code in execution order with step-ins and returns, use `code-walkthrough`.

Help the reader form a reliable mental model of the code they selected. Start at the reader's altitude: explain the purpose, useful outcome, and simplest end-to-end behavior before introducing internal names. Match the later detail to scope: a function may need a branch-by-branch trace, a notebook a cell/data journey, and a codebase an ownership map with representative runtime paths.

The default deliverable is a local interactive site under `~/.agents/walkthroughs/` with synchronized narrative, semantic diagrams, and exact source excerpts. Respect a requested explanation format; a small snippet may be clearer as an inline walkthrough. Remain read-only with respect to source code and external systems unless the user separately asks for changes or publishing.

## Core contract

- **Lead with purpose and outcome.** For a codebase or subsystem, the opening must plainly answer what it produces or enables, who it serves, and why it exists. For smaller code, start with its contract and observable effect. Do not make readers learn modules, roles, phases, or storage details before they know why those details matter.
- **Disclose detail progressively.** Give a compact overview first, then offer deeper steps for architecture, control flow, state, code, tests, and risks. A reader should be able to stop after the overview and still explain the selected code accurately.
- **Explain behavior and responsibility.** Organize around the decisions, transformations, boundaries, and flows that answer the reader's question.
- **Respect the selected scope.** Read callers, dependencies, types, configuration, or tests where needed for understanding. Do not expand a function explanation into a full repository tour.
- **Pin the source actually used.** Use a Git revision for committed code or content digests for local files and supplied snippets. Recheck that source before handoff; Git and a remote are optional.
- **Claims travel with evidence.** Connect non-obvious claims to exact code, tests, configuration, docs, schemas, or a clearly labeled inference. Expose missing context.
- **Make outputs concrete.** Include a small coherent input and examples of meaningful intermediate state and final output, attached to the producing steps. Keep worked examples distinct from observed runs and from exact source. For a pure function, show returned values; for a change, compare before/after output when it changes.
- **Code and visuals stay synchronized.** A code-bearing story step opens with a short exact excerpt while matching diagram nodes are focused.
- **Teach first, assess second.** Keep concrete risks and uncertainties separate from the explanation. Do not manufacture findings or impose a repository-wide audit on a small target.
- **Be honest about coverage.** Catalog the source that supports the story and disclose excluded or unresolved areas within the selected scope.

Read [references/code-method.md](references/code-method.md) for scope, source capture, discovery, and evidence; [references/visual-language.md](references/visual-language.md) for synchronized diagrams and code; and [references/artifact-contract.md](references/artifact-contract.md) when creating the interactive artifact.

## Shared walkthrough library

Store generated HTML, the artifact JSON, source captures, and local supporting assets in an artifact folder under `~/.agents/walkthroughs/`. Use a repository/target/snapshot-specific folder, and preserve other walkthroughs. A requested output location takes precedence; inline explanations do not need a library entry.

Omit `--output` to let the renderer choose a collision-resistant artifact folder. It prints the artifact path, keeps its JSON beside the HTML, creates a diagram thumbnail, and rebuilds `~/.agents/walkthroughs/index.html` as a searchable gallery shared by code and PR walkthroughs. For a folder chosen before source capture, pass `--output "$HOME/.agents/walkthroughs/<artifact-folder>/index.html"`. Outputs outside the library stay at their requested location and do not update the gallery. `--library-root <directory>` supports an explicitly selected alternate library or isolated validation.

The gallery indexes title, repository, type, date, target, and snapshot; it does not establish source freshness. Include both the artifact and gallery links in handoff.

## Workflow

### 1. Resolve the target and capture its source

Identify the selected snippet, symbol, files, notebook, module, or codebase and the question the reader wants answered. Infer a sensible scope from the supplied target; clarify only when ambiguity materially changes the explanation.

Read applicable `AGENTS.md` and relevant project guidance when working in a project. For a repository target without an explicit revision, use committed `HEAD` and disclose local changes. If the request selects a local file, uncommitted content, or pasted code, explain that content rather than silently substituting `HEAD`.

Record the source using the snapshot forms in [the artifact contract](references/artifact-contract.md): immutable Git ref/SHA for committed source, or SHA-256 digests of the captured files/snippets. Notebook cell identifiers and execution evidence matter: source order does not establish execution order or prove displayed outputs are current.

### 2. Discover the context needed to explain it

For a snippet or function, identify inputs, outputs, branches, loops, side effects, failure conditions, and relevant callees. For a file or module, identify its public surface and who owns each responsibility. For a larger codebase, inventory entry points, major owners, state, external contracts, tests, and operations.

For declarative code such as queries, styles, schemas, or infrastructure definitions, explain evaluation rules, dependencies, constraints, and resulting structures rather than forcing an imperative execution story.

Read full implementations for central owners and enough supporting code to avoid attributing behavior to the wrong layer. Treat generated, vendor, or data artifacts as context unless they are central to the reader's question. Label unavailable imports, callers, or runtime assumptions as evidence gaps.

### 3. Trace representative behavior

Follow the smallest set of paths that explains the target. This may be one input through an algorithm, branches and edge cases, a script's execution, notebook cell dependencies, a request across modules, or startup and persistence across services.

Trace control and data, state changes, observable outputs, and failure behavior. Distinguish code-defined behavior from a demonstrated execution. Do not claim a test ran or a notebook output is reproducible merely because it is present.

Choose a small representative input and show what it produces along this journey: for example, a saved metadata row, the checkpoint used to resume it, and the resulting report or response. Prefer a safe local fixture or existing sanitized output when available; otherwise derive a clearly labeled worked example from the pinned code. Explain what persists, what a restart reuses, and which totals or identifiers connect the stages. Validate formats and cross-stage consistency. If no useful intermediate state exists, show the final observable result without inventing storage. Use the `examples` / `example_ids` contract for the interactive site.

### 4. Build the evidence ledger and reader story

Mark central claims as `stated`, `demonstrated`, `inferred`, `disputed`, or `unknown`, with exact source and confidence. Prefer implementation and tests over aspirational documentation; preserve contradictions as questions.

Choose an arc suited to the scope. A function can move from its contract and observable result to a worked input, key decisions, and edge cases. A module can move from its purpose and public API to its internal flow and callers.

For a codebase, use two explicit layers:

1. **Outcome and motivation:** what the software makes or enables, for whom, and what problem it replaces.
2. **Simple operating model:** important inputs → the transformation in plain language → observable outputs. Keep the first visual to roughly three to five conceptual nodes.
3. **Key ideas:** the few design choices that explain how the outcome is achieved or why this approach differs.
4. **Optional deep dives:** boundaries, entry points, runtime journeys, state, extension points, tests, operations, and risks.

Keep overview titles understandable without code knowledge and prefer one to three short paragraphs. Move file paths, exhaustive role or phase lists, exceptions, and multi-excerpt evidence into deep dives. Each step should teach one idea with one visual focus and minimum sufficient evidence. Illustrative inputs are allowed when labeled as worked examples rather than recorded executions.

### 5. Select exact excerpts and a visual model

Extract real text from the captured source. Prefer roughly 8–25 lines and one idea per excerpt; a shorter snippet needs no padding. Include source identifier/path, line range, language, exact content, emphasis, and an immutable link when available. For notebooks, use stable cell identifiers and cell-local line numbers. Preserve supplied code exactly and distinguish it from illustrative examples.

Choose the least complex visual that answers the question: expression/data transformation, branch/loop flow, sequence, state lifecycle, ownership map, dependency fan-out, or deployment topology. For a broad target, the first visual should explain the product rather than the code layout: show intent or input, the core transformation, and the useful output; introduce processes, modules, and state stores in later visuals. Use 3D only when depth has a real meaning. Maintain location and context as the story focuses; keep critical distinctions visible without relying solely on motion, depth, hover, or color.

### 6. Add a secondary review lens where useful

Include only concrete, evidence-backed risks relevant to the target, such as a surprising edge case, unsafe assumption, hidden coupling, recovery gap, or missing validation. Attach severity, confidence, trigger, impact, evidence, and a resolution direction. Use an empty findings list when nothing actionable was verified. Keep wider unknowns in coverage rather than asserting conclusions about code you did not inspect.

### 7. Build and validate the artifact

For the interactive deliverable, write data following [references/artifact-contract.md](references/artifact-contract.md), then render and validate:

```bash
python3 <skill-dir>/scripts/render_walkthrough.py --data <walkthrough.json>
python3 <skill-dir>/scripts/validate_walkthrough.py --html <rendered-path>
```

The validator checks artifact structure, not source accuracy. Compare excerpts and snapshot identifiers against the captured source separately. Use an available browser to verify desktop/mobile layouts, story controls, keyboard navigation, code switching, diagram focus, review-lens separation, reduced motion, links, and console errors. Report unavailable checks as unverified.

Before handoff, re-resolve the selected Git ref or recalculate digests for every captured file/snippet. If the source changed, rebuild or explicitly mark the artifact stale. For an immutable historical revision, report that revision rather than requiring it to match current `HEAD`.

## Handoff

Report the artifact path and local URL when applicable, selected scope and snapshot, behavior represented, validation performed, staleness, and material exclusions or evidence gaps. For an inline explanation, include enough source identifiers to make the same evidence boundary clear. Mention publishing only when requested.

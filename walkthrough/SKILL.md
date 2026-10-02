---
name: walkthrough
description: Build an author-perspective, evidence-linked visual walkthrough of a pull request or local code change. Use when a reviewer needs to understand intent, architecture, behavior, key code, tests, and review risks through synchronized prose, exact code excerpts, and purposeful 2D or 3D diagrams. Do not use for a findings-only code review or a generic codebase architecture map.
---

# PR Review Buddy

Create a reviewer aid that makes the change easy to understand before it judges the change. Reconstruct the strongest evidence-supported version of the author's case, show how the changed system works, and keep the exact code beside the explanation and visual focus.

The default deliverable is a local interactive site generated under `.walkthrough/`. Remain read-only with respect to product code, GitHub, and other external systems unless the user separately asks for changes or publishing.

## Core contract

- **Orient first, audit second.** The main story explains intent, design, behavior, and validation. Put fresh findings in a visually separate review lens; do not let critique hijack the walkthrough.
- **Represent, do not impersonate.** Prefer “The author is solving…” or “The implementation suggests…” over unsourced first-person claims. Label inferred rationale and unresolved questions.
- **Claims travel with evidence.** Every non-obvious claim should connect to an exact code excerpt, diff line, test, spec, issue, benchmark, PR comment, or clearly labeled inference.
- **Code and prose stay synchronized.** A story step that discusses code must select a short, exact, copyable excerpt beside the prose and highlight the corresponding diagram node.
- **Visuals explain structure or behavior.** Diagrams are semantic models, not decoration. Use consistent encodings and scale. Prefer 2D unless depth materially explains hierarchy, concurrency, topology, or magnitude.
- **Be concise without hiding scope.** Teach the smallest coherent story, then expose coverage, de-emphasized files, assumptions, and missing evidence so the reviewer knows what was and was not represented.
- **Pin the review target.** Record base/head refs and immutable SHAs. Detect and report staleness if the head changes after collection.

Before building a walkthrough, read:

- [references/review-method.md](references/review-method.md) for author-perspective reconstruction, evidence, review coverage, and the secondary correctness pass.
- [references/visual-language.md](references/visual-language.md) for story structure, diagram selection, code presentation, motion, and accessibility.
- [references/artifact-contract.md](references/artifact-contract.md) when using or extending the bundled renderer.

Read [references/research-notes.md](references/research-notes.md) only when evolving this skill or discussing why its design differs from other review workflows.

## Workflow

### 1. Resolve and freeze the change

Accept a PR URL/number, current branch PR, commit range, or local changes. Prefer the PR's declared base. Otherwise resolve the repository's remote default branch and use the merge base.

For a GitHub PR, collect at least title, body, URL, base/head refs and OIDs, commits, changed files, reviews, comments, and checks with `gh`. For a local range, record the exact refs and resolved SHAs. Include staged and working-tree diffs only when the requested target includes them.

Inspect the complete diff. Also read the full current versions of important changed files and enough unchanged owners, callers, types, configs, tests, and documentation to understand the change in-system. Follow repository instructions such as `AGENTS.md`, `CONTRIBUTING.md`, and relevant ADRs.

Complete when the exact review target, immutable base/head, full change inventory, intent sources, and available validation signals are known.

### 2. Reconstruct the author's case

Build an evidence ledger before writing the story:

1. What problem or constraint motivated the change?
2. What observable behavior changes, and what deliberately stays the same?
3. What approach did the author choose, and what alternatives or tradeoffs are documented?
4. Which components own the change, and how does data/control move through them?
5. How is the behavior demonstrated or tested?
6. What deserves reviewer attention or an author answer?

Resolve conflicts by source strength: executable behavior and tests; approved specs/ADRs; PR and issue discussion; commit messages; code-shape inference. Preserve disagreements instead of blending them into a false consensus.

Complete when each central claim is marked as stated, demonstrated, inferred, disputed, or unknown and has a source or an explicit evidence gap.

### 3. Choose the reviewer story

Start with the whole change, then move through its runtime or conceptual sequence rather than alphabetical file order. A useful default arc is:

1. **Why / contract:** problem, scope, user or caller-visible promise.
2. **Before → after:** stable architecture and the seam that changes.
3. **Key mechanism:** the few implementation decisions that make the change work.
4. **Behavior journey:** request, event, state, data, or user action through the system.
5. **Proof:** tests, checks, screenshots, benchmarks, or manual validation.
6. **Review lens:** risks, uncertainties, tradeoffs, and actionable findings.
7. **Coverage:** changed areas represented, de-emphasized mechanical work, and gaps.

Tiny changes may need only three or four steps. Large changes may need multiple chapters, but every step must teach one reviewer-relevant idea. Keep the default overview explorable; make story mode opt-in.

Complete when the story has a deliberate order and every step has one takeaway, one visual focus, and the minimum evidence needed to support it.

### 4. Select exact code excerpts

Use real text from the pinned revision or diff. Normally keep one excerpt to roughly 8–25 lines and one idea. Split longer logic into multiple excerpts. Show before/after excerpts when the contrast is the lesson; use a diff excerpt when line-level change is the lesson; use the current version when surrounding control flow is the lesson.

Each excerpt must include path, side/revision, start/end lines, language, exact content, and a PR diff or immutable blob URL when available. Never synthesize code and present it as source. Avoid screenshots of code.

Complete when every code-bearing story step opens with the relevant excerpt visible beside the prose and each excerpt can be traced to the pinned change.

### 5. Design the visual model

Choose the least complex visual that makes the central relationship clearer:

- 2D flow or sequence for requests, events, state, and user actions.
- Dependency or ownership map for module boundaries and blast radius.
- State comparison or before/after layout for behavior changes.
- Timeline for ordering, retries, races, lifecycle, or migration.
- 3D/layered scene only when depth expresses real hierarchy, parallelism, topology, or scale.

Start zoomed out. Story transitions should smoothly focus the relevant subsystem and then restore context; do not teleport between disconnected views. When comparing old/new or two paths, keep them side by side with matched scale and semantic color. Encode magnitude honestly rather than using arbitrary visual size.

Complete when every visual element has a meaning, every important relationship has a direction or label, and the diagram remains understandable without motion.

### 6. Run the secondary review pass

After the walkthrough story is stable, check the entire diff and affected call sites for concrete regressions, spec divergence, unsafe assumptions, missing tests, security/permission/dependency impact, backward compatibility, unnecessary complexity, and misleading documentation.

Verify each candidate finding against code and tests. Keep spec/behavior, design/standards, and operational/security concerns distinguishable. Include only actionable findings an author would likely address; attach severity, confidence, triggering condition, impact, evidence, and a direction for resolution. Treat optional polish as optional.

Do not post comments, approve, request changes, or modify code unless separately requested.

Complete when the whole diff is accounted for and every displayed finding is evidence-backed, line-anchored where possible, and visually separate from the author's case.

### 7. Build the artifact

Write structured data that follows [references/artifact-contract.md](references/artifact-contract.md), then render it with:

```bash
python3 <skill-dir>/scripts/render_walkthrough.py \
  --data <walkthrough-data.json> \
  --output .walkthrough/<pr-or-branch>-<head-sha>/index.html
```

The bundled template provides a synchronized narrative, diagram, code panel, story controls, review lens, and coverage view. Extend it for a genuinely useful custom 3D scene rather than forcing unusual changes into generic boxes.

Keep external assets local or embedded. Do not publish private code or PR context. Publishing requires an explicit user request and an explicit destination/access choice.

Complete when the artifact opens locally and its meta panel shows the pinned base/head used to build it.

### 8. Validate from a reviewer's point of view

Run the deterministic validator:

```bash
python3 <skill-dir>/scripts/validate_walkthrough.py \
  --html .walkthrough/<pr-or-branch>-<head-sha>/index.html
```

Then use an available browser to verify desktop and mobile layouts, step navigation, story play/pause, keyboard controls, code switching, diagram focus, 3D drag/zoom when present, review-lens separation, links, and readable no-motion behavior. Inspect browser errors. If browser validation is unavailable, report it as unverified.

Finally re-resolve the current head. If it differs from the artifact's `head_sha`, mark the walkthrough stale and do not present it as current.

Complete when validation passes, the rendered claims match their evidence, and any unavailable checks are stated plainly.

## Handoff

Report the artifact path and local URL, target/base/head, the first story step, whether findings were included, deterministic validation result, browser/mobile validation result, staleness result, and material evidence gaps. Mention public publishing only if the user requested it.

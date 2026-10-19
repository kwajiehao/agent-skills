---
name: pr-review
description: Review a pull request or local diff for correctness, fix scope, compatibility, and operational risk, with a concise verdict and concrete evidence. Use for findings-oriented reviews; use dep-review for dependency upgrades and pr-walkthrough for visual explanations.
---

# PR Review

Help the user decide whether a change is ready and what consequential issues
remain. Follow repository review rules and the user's requested scope. A review
does not authorize application edits, external comments, or production actions.

## Establish the change and decision

- Record the repository, PR URL when present, base/head SHAs, and dirty state.
  Read applicable AGENTS.md files and the PR's problem statement and discussion.
  Distinguish the reviewed commit from local uncommitted work.
- For a repeat review, load the existing ledger. Compare its head with the
  current head, inspect the delta, and recheck conclusions affected by changes
  to callers, dependencies, or deployment. Expand beyond the delta when needed.
- Use an existing suitable checkout. Use an isolated worktree when verification
  would otherwise disturb existing edits; do not reset the user's checkout.

## Evaluate behavior and proportionality

Trace the relevant trigger through validation, callers, state changes, and
failure handling. Check whether the original failure is real, whether the fix
addresses its root cause, and whether relevant variants or alternate paths
remain. Inspect compatibility, rollout, retry, partial failure, and concurrency
only where the change makes them consequential.

Execute the smallest meaningful reproduction or existing checks for material
claims when feasible. Include a baseline or negative control when it changes
the interpretation. Do not turn a toy recreation into proof about the product;
record mocks, fidelity limits, missing access, and unverified deployment facts.
Passing unrelated tests is not evidence for the finding.

Prefer the smallest sound change. Separate demonstrated defects from optional
architecture, ownership, observability, and performance improvements. Label
worst-case calculations and distinguish them from measured behavior. Test effort
should match the risk; a read-only review need not add tests to the repository.

Use specialized security skills only when the requested review needs them.
Do not automatically turn ordinary PR review into a full security audit.

## Deliver the review

Lead with the merge/readiness verdict and the strongest supporting reason.
Usually surface at most three consequential issues; disclose any additional
material blockers rather than concealing them to meet a count. For each issue,
give the exact code location, concrete trigger, user or operational consequence,
and evidence status: reproduced, traced but unexecuted, or unresolved. State the
smallest useful correction. Keep optional follow-ups separate.

Finish with checks actually executed, the reviewed SHA, and material limits.
If no consequential issue was found, say so without implying exhaustive proof.
Draft a review comment only when requested; sending or posting needs the user's
explicit approval for that specific message.

## Carry review state forward

For substantial or repeated PR reviews, keep a compact per-PR ledger using
[the ledger template](references/ledger.md). Prefer
`~/.agents/reviews/<owner>-<repo>/pr-<number>.md`; for local changes, use a stable
task slug. Preserve prior evidence and update the reviewed head and next step.
If that destination is outside permitted writes, save it in the authorized task
workspace and identify its path. Do not broaden filesystem permissions merely
to relocate notes. Do not write to the reviewed source repository for bookkeeping
when the user asked for a read-only review.

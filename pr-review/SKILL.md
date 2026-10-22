---
name: pr-review
description: Review a pull request or local diff for correctness, requirement coverage, compatibility, and operational risk, verifying consequential behavior with concrete evidence. Use for findings-oriented reviews; use dep-review for dependency upgrades and pr-walkthrough for visual explanations.
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

Prefer the smallest sound change. Separate demonstrated defects from optional
architecture, ownership, observability, and performance improvements. Label
worst-case calculations and distinguish them from measured behavior. Test effort
should match the risk; a read-only review need not add tests to the repository.

Use specialized security skills only when the requested review needs them.
Do not automatically turn ordinary PR review into a full security audit.

## Verify the implementation

Identify the consequential requirements within the requested scope from the
user's request, PR discussion, and repository contracts. Check whether the
implementation fulfills them, including promised durable effects and relevant
rejection or recovery behavior. A PR checklist or author summary is context;
inspect the actual implementation and assertions independently.

For each consequential requirement, record the implementation location, the
test/assertion or runtime observation that checks it, and the observed result.
Distinguish executed evidence, traced but unexecuted behavior, and unresolved
gaps. Keep this map compact; use the ledger for substantial reviews and summarize
coverage and material gaps in the response.

Inspect what a test proves: identify a plausible defect its assertions would
catch. Exercise real implementation behavior and derive expected results from
the requirement or an independent reference. Assertions that only confirm a
configured mock return or mirror the implementation do not establish the
behavior under test. Compilation supports build/type claims; runtime promises
need relevant behavior checks. Mocks may isolate dependencies; name the
boundaries they omit. Passing unrelated tests is not evidence for a requirement.

Execute the smallest credible reproduction or relevant checks when feasible.
For a fix, compare the original and changed behavior or use a negative control
when it clarifies whether the check detects the defect. Reuse existing CI or
retained results only when they cover the reviewed code and relevant behavior;
a test's presence does not establish that it ran. Record commands, outcomes,
environment limits, and unverified deployment facts. Do not turn a toy recreation
into proof about the product or modify product code to make a review check pass.

Before reporting a blocker, check callers, existing guards, and relevant tests
for evidence that refutes it. Missing access or an unexecuted check is a
verification gap, not by itself a demonstrated implementation defect. Name the
smallest next check that would resolve consequential uncertainty.

## Deliver the review

Lead with the merge/readiness verdict and the strongest supporting reason.
Use ready, changes needed, or evidence incomplete. Do not call the change ready
when an unmet requirement or consequential verification gap prevents a sound
decision. Separate confirmed defects from incomplete evidence; proportionate
verification does not require running every test or proving every possible case.

Usually surface at most three consequential issues; disclose any additional
material blockers rather than concealing them to meet a count. For each issue,
give the exact code location, concrete trigger, user or operational consequence,
and evidence status: reproduced, traced but unexecuted, or unresolved. State the
smallest useful correction. Keep optional follow-ups separate.

Finish with requirement coverage, checks actually executed or reused, the
reviewed SHA, and material limits. State consequential uncovered requirements
and unexecuted checks explicitly.
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

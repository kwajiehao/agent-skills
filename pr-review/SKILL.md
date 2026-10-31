---
name: pr-review
description: Review a PR or local diff for correctness, design fit, and operational risk by tracing the operation and challenging consequential failure paths. Use for findings-oriented reviews; use dep-review for dependency upgrades and pr-walkthrough for visual explanations.
---

# PR Review

Help the user decide whether a change is ready and what consequential issues
remain. Follow repository review rules and the user's requested scope. A review
does not authorize application edits, external comments, or production actions.

## Establish the change and decision

- Record the repository, PR URL when present, base/head SHAs, and dirty state.
  Read applicable AGENTS.md files and the PR's problem statement and discussion.
  Distinguish the reviewed commit from local uncommitted work.
- For a repeat review, load the existing ledger and recover its scope, reviewed
  revision, finding dispositions, evidence and next step. Compare both base and
  head with the current change; inspect the delta and recheck conclusions affected
  by changed callers, dependencies or deployment. Expand beyond the delta when
  needed; do not restart unchanged investigation without a concrete reason.
- Use an existing suitable checkout. Use an isolated worktree when verification
  would otherwise disturb existing edits; do not reset the user's checkout.

## Trace the operation and challenge the design

Choose a concrete user/caller operation affected by the change. Trace it from
entry to the observable result, including durable effects when promised. Follow
the actual callers and consumers across handoffs, including relevant unchanged
code; a function returning successfully may leave the operation incomplete.
For a fix, establish the original failure and whether the proposed design repairs
its cause while preserving nearby valid behavior.

At each step and handoff, establish:

- What input, identity, permissions and state enter, who owns the next action,
  and which guarantee that action assumes from the previous step.
- What must be validated or changed, when an effect becomes durable, and what
  observable evidence establishes success for the caller.
- Credible ways the step can fail or return an uncertain result, their effect on
  later steps and the final outcome, and the guard or recovery that handles them.

Challenge the design with failures grounded in the operation: malformed or stale
input, identity/permission changes, failure between validation and use, dependency
rejection, partial effects, a committed effect followed by a lost acknowledgement,
retries, interruption and concurrent state changes. Choose applicable failures
at each step; a small local operation needs a correspondingly short trace. Include
rollout/version compatibility where producers and consumers can differ.

Follow each material failure through error propagation, cleanup, retry and
reconciliation. Check what the next component actually does, including whether
it can report success too early, repeat an effect or leave unrecoverable state.
Validate suspected failures against existing guards and caller behavior. A
credible guard with supporting evidence is a successful design check; do not
invent a finding for every step or require protection against arbitrary faults.

Compare the design with the existing path and the smallest sound alternative.
Challenge new flags, configs, helpers, shared abstractions and orchestration
against the concrete missing behavior and actual consumers. Ask whether complexity
removes a demonstrated failure or merely moves it to another component. Keep a compact
step/handoff map with code locations, assumed guarantees, challenged failures,
guards/recovery and evidence status in the ledger for substantial reviews.

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

Compare the tested path with the actual public invocation. Identify setup,
transport, or state transitions that the tests bypass, and check any that could
invalidate a consequential guarantee. If such a boundary cannot be exercised,
record the verification gap.

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

## Follow-up reviews and authorized fixes

Keep a stable ID for each consequential finding. After a change, recheck its
trigger and affected behavior against the new revision; mark it resolved only
with supporting evidence, and preserve any untested boundary. Reuse unaffected
evidence with its covered revision and limits. Rerun expensive checks when the
change or environment invalidates them, not merely to obtain another green run.

When the user also authorizes fixes, work through concrete findings within that
scope: fix, inspect the resulting diff, and recheck the finding and affected
requirements. A review alone remains read-only. Stop the loop when the agreed
requirements are supported and no consequential finding remains, or when a
specific access/evidence blocker or material scope decision prevents progress.
Record that boundary and the smallest next action. Do not prolong the loop for
optional redesign, or treat repeated reviewer agreement as independent evidence.

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
and unexecuted checks explicitly. Include a concise operation flow and the
material failure boundaries when they explain the verdict; keep the detailed
step map in the ledger rather than listing every hypothetical failure.
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

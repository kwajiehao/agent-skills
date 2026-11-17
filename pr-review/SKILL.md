---
name: pr-review
description: Review a PR or local diff for correctness, performance, design fit, and operational risk by tracing the operation and challenging consequential failure paths. Use for findings-oriented reviews; use dep-review for dependency upgrades and pr-walkthrough for visual explanations.
---

# PR Review

Decide whether the change is ready and identify consequential issues. Follow the
user's scope and repository instructions. Review alone does not authorize source
edits, external comments, production actions or costly experiments. Apply
[technical-writing](../technical-writing/SKILL.md) to explanations.

## 1. Establish the decision and revision

Record the repository, PR URL, base/head SHAs and relevant dirty state. Read
applicable AGENTS.md files, the problem statement and discussion. Use a suitable
checkout or an isolated worktree; preserve existing edits.

For a follow-up, load the [review ledger](references/ledger.md), compare both
base and head, and recheck conclusions affected by the delta, including changed
callers or deployment. Reuse unaffected evidence with its revision and limits;
do not restart the investigation without a reason.

Establish who encounters the problem, the evidence for it and the outcome needed.
Compare the approach with existing mechanisms or a smaller change where credible.
Explain material tradeoffs in compatibility, operational burden and cost. Missing
context is a question, not proof that the change is unnecessary.

## 2. Trace one concrete operation

Follow an affected operation from its real entry point to the caller-visible
result and any promised durable effect. Include relevant unchanged callers and
consumers. For a fix, establish the original failure and whether the change
repairs its cause while preserving nearby valid behavior.

At consequential handoffs, identify the producer, consumer, concrete arguments
or stored rows, required identity/state and component enforcing the guarantee.
Trace failures through the caller's next action: rejection, partial effects,
lost acknowledgement, retry, interruption or concurrent change. Select cases
that fit this operation; do not manufacture findings for every possible fault.

Check the existing-user path when shared behavior changes. For deployment or
startup changes, consider disabled features and existing state, not only a fresh
enabled installation. Include mixed-version behavior where components can differ.
Check whether a successful return actually establishes the promised outcome.

Challenge added flags, helpers and orchestration against a concrete unmet need.
Prefer reuse and the smallest sound change. Separate demonstrated consequences
from optional simplification or stylistic preference.

## 3. Connect each consequential claim to evidence

Use one compact map in the ledger, or inline for a small review:

| Claim | Enforcing component / code | Distinguishing case and expected result | Evidence / gap |
| --- | --- | --- | --- |
| Required behavior | Actual consumer, not just its helper | A plausible violation the check would catch | Executed, traced but unexecuted, or unresolved; revision and limits |

Start with the component enforcing the claim, then inspect evidence for that
component. A passing helper test cannot establish a guarantee enforced elsewhere.
Compare fixtures with the actual caller's inputs, consumed representation,
permissions and prior state. Semantic parsing does not test byte-sensitive
consumers. Name omitted setup, transport, startup or recovery boundaries that
could invalidate the claim.

Derive expected results from the requirement or an independent reference. For a
test that merely mirrors implementation, identify the claimed behavior, a
plausible violation that still passes, and whether to remove it or replace its
assertions. Mocks may isolate dependencies and literal assertions may enforce a
real contract; neither is automatically redundant. Do not count mocked consumer
behavior or argument forwarding as end-to-end verification.

Run the smallest credible reproduction or relevant check when feasible. For a
fix, compare original and changed behavior or use a useful negative control.
Choose contrasting cases that distinguish the guarantee: an existing caller,
rejected input, interrupted operation or next invocation after partial effects,
as appropriate. Preserve the conditions implicated by the actual failure.
Compilation proves build/type properties; runtime promises need behavior evidence.

Record commands, observed results, covered revision and limitations. A test's
presence does not establish execution; unrelated passing tests do not establish
a claim. Reuse CI or prior results only when the changed path and conditions
remain covered. If a consequential boundary cannot be verified, retain that gap
in the verdict instead of treating helper success as readiness.

Before reporting a defect, check actual callers, existing guards and contrary
evidence. Missing access or measurement is a verification gap, not automatically
a defect. State the smallest check that would resolve consequential uncertainty.
Do not modify product code merely to make a review experiment pass.

## 4. Assess performance along that operation

Identify material performance changes even when the PR makes no performance
claim. Select the few relevant outcomes: latency, throughput, CPU/memory, I/O,
remote calls, queueing or cost. Establish workload size, invocation frequency,
concurrency and resource limits from callers, configuration or telemetry; label
assumptions and unknown budgets.

Compare work per invocation and the number of invocations before and after.
Trace loops, queries, fan-out, allocations, serialization and blocking through
consumers, including retry/recovery amplification. Check that pagination,
indexes, caches, pool limits or other bounds actually constrain this workload.
Weigh their resource and operational costs against the problem they solve.

Distinguish measured results, code-derived counts/complexity and unknown runtime
effects. An extra query alone does not establish a latency regression. When a
measurement would settle a material uncertainty, use a bounded comparison on the
same representative workload and environment, preserving relevant cache state,
data size and concurrency. Report what it omits; do not expand authorization.

Report a performance defect when a concrete trigger and traced or measured
mechanism support consequential impact. Missing benchmarks alone are a gap;
speculative tuning stays separate from findings. Keep this section brief when no
material performance path changes.

## 5. Deliver the verdict and close the loop

Lead with **ready**, **changes needed** or **evidence incomplete**, and the main
reason. Do not call the change ready while a consequential requirement is unmet
or unverified. Explain the motivation and design through the concrete operation
so someone unfamiliar with the conversation can follow.

For each finding, give the location, trigger, consequence, evidence status and
smallest useful correction. Usually lead with at most three; disclose additional
material blockers rather than hiding them. Separate confirmed defects, evidence
gaps and optional suggestions. Summarize executed/reused checks, reviewed SHA,
performance conclusions and remaining limits. No findings does not mean proof of
all possible behavior. Draft comments only when requested; posting requires the
user's approval of the specific message.

For substantial or repeated reviews, retain the compact ledger at
`~/.agents/reviews/<owner>-<repo>/pr-<number>.md`, or an authorized task-workspace
path if necessary. For local changes use a stable slug. Do not modify the reviewed
repository merely for read-only review bookkeeping or broaden permissions to
relocate notes.

Keep stable finding IDs. Mark a finding resolved only after rechecking its trigger
and affected behavior on the new revision. Preserve untested boundaries and
reuse unaffected evidence. When fixes are authorized, fix, inspect the final diff
and verify affected claims. Stop when the requested requirements are supported,
or identify the specific access, evidence or scope blocker and next action.
Do not prolong the work for optional redesign, repeat tests without a changed
reason, or count repeated reviewer agreement as independent evidence.

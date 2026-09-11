# Campaigns, Triage, and Feedback

Run fuzzing as a measured experiment. A raw exception or crash is a lead, not a
confirmed product bug. The campaign is useful only when findings become
reproducible evidence and durable improvements.

## Preflight

Before running:

- identify accepted requirement versions and any excluded unresolved semantics;
- record the product and harness revisions;
- confirm the target, command, environment, resource limits, and stop condition;
- verify that failure inputs, seeds, traces, and logs will be retained;
- verify secret and personal-data handling;
- run valid-behavior and defect-detection controls with explicit expected results;
- confirm the user authorized any network service, container, external compute,
  dependency installation, or disruptive fault injection involved.

Never fuzz production, a third-party endpoint, or an environment outside the
user's stated scope by inference.

## Budget progression

Use increasing budgets only when the previous tier is healthy:

1. **Replay controls:** known examples and historical failures.
2. **Smoke:** if unspecified, at most 30 seconds per target and two minutes total.
3. **Local campaign:** use an applicable approved profile or propose the command,
   targets, and expected resource use; do not exceed ten minutes without existing
   or new user authorization for that budget and scope.
4. **Extended or continuous campaign:** require an explicit budget, storage
  policy, owner, stop condition, and failure-notification path.

Reuse recorded approvals while their scope matches; do not reapprove every run.
The smoke defaults bound exploration, not compilation, service startup, or triage.
Record those costs separately. Allocate the total smoke budget across targets and
report any skipped targets. Default triage to five minutes total per invocation
when no policy exists; prioritize severe new signatures and preserve the rest.
Apply native case/memory limits and a wall-clock supervisor. Report a supervisor
timeout as incomplete execution, not a healthy campaign or an automatic product bug.

Stop early when the harness produces repeated shallow failures, timeouts, OOMs,
uncontrolled side effects, corrupt artifacts, or evidence that it is not
reaching the intended target.

## Record the campaign

Use [the campaign ledger template](../assets/campaign-ledger.template.md). Capture:

- start/end time and budget consumed;
- product, specification, harness, corpus, and dependency revisions;
- commands and sanitized environment;
- cases or executions per second;
- corpus growth and unique failure signatures;
- code/edge coverage when available;
- domain feature counts and declared cross-product counts;
- timeouts, OOMs, discarded inputs, flaky failures, and infrastructure errors;
- links to complete failure bundles;
- changes made to the fuzzing system before the next campaign.

The ledger indexes immutable per-run records. Use [run-evidence.md](run-evidence.md)
for native-runner integration or the optional recorder, including exact selected
source snapshots for uncommitted changes, machine-readable results, failure paths,
and explicit termination states. Never fill measurements from estimates or prose.
Handle interrupted execution and restart using [change-and-ci.md](change-and-ci.md).

Do not present test-case count or coverage percentage as a correctness claim.
Use trends to find stalls, unreachable behavior, or poor harness design.

## Triage every finding

### 1. Preserve

Immediately preserve the seed or input, operation history, failure signature,
logs, and revision information. Redact credentials, tokens, personal data, and
captured authorization headers.
Prefer synthetic inputs so exact replay artifacts can be retained safely. If raw
sensitive bytes are necessary, use only an explicitly approved restricted store;
publish sanitized derivatives and reference the protected original. Verify that
sanitization preserves reproduction before calling a derivative a reproducer.

### 2. Reproduce

Replay with the exact recorded revision and environment. Report the number of
successful reproductions out of attempts. For nondeterministic failures, improve
the reproduction rate with controlled scheduling, repeated execution, or
additional instrumentation rather than labeling an unreproduced result as fact.

### 3. Verify the symptom

Confirm that the observed behavior violates an approved requirement and is the
same failure the oracle reported. Check the target adapter, oracle, mocks,
fixtures, injected faults, and artifact-producing code for self-created errors.
Where useful, inspect the execution artifact independently from the code that
generated it.

### 4. Minimize

Reduce the input, command sequence, state, configuration, schedule, and injected
faults while preserving the same failure signature and requirement violation.
For flaky failures, preserve reproduction probability rather than demanding an
unrealistic deterministic minimum.

Matt Pocock's
[`diagnosing-bugs` skill](https://github.com/mattpocock/skills/blob/main/skills/engineering/diagnosing-bugs/SKILL.md)
provides the same useful discipline: build a red-capable feedback loop,
reproduce, minimize, and only then diagnose.

### 5. Classify

Use a primary cause when supported, with secondary contributing factors as needed.
Keep `Unknown` while evidence is insufficient. Confidence, severity, reproducibility
and workflow status are independent fields: a confirmed severe product race may
reproduce rarely. Do not downgrade it simply because it is nondeterministic.

| Classification | Meaning | Required durable action |
|---|---|---|
| Product bug | Approved behavior is violated by the target | Preserve minimized regression and open/link a fix request; do not alter product code unless asked |
| Specification gap | Correct behavior is ambiguous or absent | Ask the human, version the specification, then add or change the oracle |
| Generator gap | Important behavior is modeled but unreachable or implausibly rare | Fix constraints, action selection, scenario generation, seeds, or dictionaries |
| Oracle bug | Legitimate behavior is reported as failure or a requirement is checked incorrectly | Correct the oracle and retain the case as a must-not-fail regression |
| Harness/environment bug | The adapter, mock, setup, teardown, instrumentation, or environment created the result | Repair fidelity/determinism and replay before reopening product triage |
| Unknown | Evidence does not yet establish the cause | Preserve the case, record confidence/reproduction rate, and assign investigation |

Use [the failure record template](../assets/failure-record.template.md).

Deduplicate provisionally by violated property, failure mechanism, and relevant
stack/trace evidence. Do not merge solely by exception type. Retain original case
links and occurrence counts so a mistaken grouping can be undone. At the triage
budget, save an owned queue ordered by severity and uncertainty, with the next
replay/instrumentation step. Preserve and escalate serious evidence before lengthy
minimization; never discard a finding because reduction or replay is incomplete.
Link an existing issue or prepare a local fix request; publishing issues/messages
requires the same authorization as outside this skill.

## Close the feedback loop

### Confirmed product bug

- Preserve a minimized deterministic regression when possible.
- Link the regression to the violated requirement and failure record.
- Check whether the generator represents the broader bug class.
- Record a product fix request or existing fix; do not silently expand the task
  into product implementation.
- Replay both the minimized and original cases after any future fix.

### Oracle false positive

- State why the behavior is allowed.
- Correct the property without weakening unrelated guarantees.
- Keep the case as a negative regression that must no longer fail.
- Update the specification if the false positive exposed ambiguous language.

### Generator or reachability gap

- Identify the missing dimension, constraint, state transition, seed, token,
  fault point, or cross-product.
- Add semantic feature instrumentation for the gap.
- Show that the revised generator now reaches and checks it within its declared
  profile budget; use directed scenarios for PR requirements.
- Re-audit nearby combinations rather than special-casing only one input.

### Specification gap

- Present the smallest concrete scenario and competing interpretations.
- Obtain a human decision.
- Increment the specification version and record provenance.
- Update the oracle, generator, and regressions affected by the decision.

### Harness or environment bug

- Repair the adapter, setup, isolation, observation, or replay mechanism.
- Add a harness self-test or control that would have exposed the defect.
- Re-run earlier findings whose validity depended on the broken component.

## Learn from production escapes

When a bug reaches production without being found, first encode a replayable
reproducer, then ask why each layer failed:

1. Was the required behavior absent or ambiguous in the specification?
2. Was the relevant state/input/fault modeled?
3. Could the generator reach the necessary sequence and cross-product?
4. Did the oracle observe the violation?
5. Did the harness reproduce the real environment closely enough?
6. Did the campaign run the relevant target with enough useful diversity?
7. Was the failure found but rejected, deduplicated, or lost incorrectly?

A fixed regression protects one known case. Also improve the earliest deficient
layer so related unknown cases become discoverable.

## Completion criteria

Execution is complete when the runner has recorded a terminal outcome and retained
its evidence. Triage may remain pending: every occurrence needs a preserved case
or a link to a retained duplicate, and outstanding work needs an owner and next
step. A timed-out or interrupted execution is terminal but not successful.

The invocation is complete when the requested budget is accounted for, accepted
fuzz-infrastructure changes are verified, and replay/cleanup/backlog instructions
allow continuation. Close individual findings only after their durable feedback
is recorded. Product bugs may remain open in a separate fixing workflow unless
the user's request already includes their repair.

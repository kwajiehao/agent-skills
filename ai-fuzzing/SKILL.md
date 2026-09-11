---
name: ai-fuzzing
description: Assess a repository or component's fuzzing and property-testing state, recommend the next useful action, and design, build, update, run, or audit its tests. Accept a bare invocation or target path; infer the workflow from repository evidence. Use for fuzzing and property-testing setup, changes, findings, and production escapes, not ordinary example-based test writing or unrelated diagnosis.
---

# AI-Assisted Fuzzing

Build a durable bug-discovery system, not a batch of AI-written example tests.
Use the model to discover and clarify the test space, construct and improve the
harness, and investigate results. Use deterministic project-native tooling for
the high-volume fuzzing loop.

A generator is not a complete fuzzer. Treat the working system as:

```text
generator or mutator
+ target harness
+ oracle or checks
+ execution loop
+ persistence and replay
```

Coverage guidance, shrinking, and corpus management are strongly preferred when
the target and selected tooling support them.

This workflow builds on Dan Luu's arguments for randomized generation,
continuous exploration, regression retention, and independent false-positive
checking in [his AI-coding essay](https://danluu.com/ai-coding/) and
[earlier testing essay](https://danluu.com/testing/). It turns those arguments
into an operational workflow; it is not a named framework from those essays.

## Start from the repository or component

A bare invocation is enough. Use the current working directory when no target is
given. A path, component name, or repository narrows the scope; resolve it from
the code and call sites. Do not require the user to choose a mode, list properties,
name a harness, or repeat this skill's procedure.

First inspect repository instructions, relevant source and interfaces, existing
example/property/fuzz tests, accepted contracts, build/CI commands, local changes,
and relevant prior runs/findings when available. Discover native testing artifacts
even if there is no `fuzzing/` directory or `FUZZING_SPEC.md`. Check actual evidence
and freshness; a filename, successful compilation, or old passing run does not
establish readiness. Read only the mode references needed after this assessment.

Assess each relevant target separately: one repository can have mature fuzzing
for its parser and none for its persistence layer. For a broad scope, prioritize
one useful seam using change impact, failure history, consequential behavior and
practical testability. Avoid turning discovery into an exhaustive repository audit.

For a bare invocation or a request for recommendations, return a short assessment:

- **State:** the target, what exists, and the most consequential gap, with evidence.
- **Recommended next action:** one concrete task, why it comes next, expected
  deliverable and applicable budget; include a real command/path when known.
- **Other options:** at most two worthwhile alternatives, only if they change the
  decision. Name any missing semantic decision or execution scope for that action.

This discovery is read-only: it does not run project commands or modify files just
to produce a proposal. Do not ask a generic "what would you like to do?" or present
internal mode names as choices. A follow-up such as "go ahead" selects the concrete
recommendation, retaining its scope and budget; refresh only evidence that changed.
It does not resolve an explicitly open semantic question or grant unnamed access.

When the surrounding request already includes setup, updating tests, executing a
run, or implementation followed by fuzzing, use the same discovery to select and
perform the authorized work. Briefly state the selected action and proceed; the
recommendation is not an additional confirmation gate. Explicit audit, replay,
triage, or review-only scope takes priority over inferred maintenance needs.

## Infer the next action

Use the evidence below to select work, not a mandatory sequence for every target.
Prioritize consequential unresolved failures and unsafe/incomplete execution when
relevant to the request. Preserve independent progress on unaffected targets.

| Observed state | Useful next action |
|---|---|
| Retained finding or production escape needs investigation | **Campaign: triage** the evidence within the triage budget |
| Interrupted run or incomplete terminal evidence | **Campaign: resume** by checking retained evidence, owned resources and restart safety |
| Relevant code/dependency change invalidates target coverage or prior evidence | **Change**: update affected tests when requested, replay and run the bounded profile |
| Existing harness has unknown fidelity, weak checks, missing required coverage, or no trustworthy recent audit | **Audit** the gap; propose a targeted harness/generator/oracle repair from its findings |
| Accepted requirements exist but the useful target has no adequate harness | **Build** the smallest target from those requirements |
| A useful target lacks settled semantics | **Specify** only missing meanings; build from accepted requirements independently when authorized |
| Validated target is ready and a run would add useful evidence | **Campaign** using its applicable existing profile and retained corpus |
| Relevant tests are current and recent evidence is adequate for their scope | Say no immediate repair is indicated; suggest further exploration or a new target only with a concrete reason |

Do not equate missing skill-specific documents with missing tests or accepted
contracts. Do not manufacture maintenance work when the evidence is current.

For an end-to-end request, specify the smallest useful target, build from its
accepted requirements, run a bounded smoke campaign, and audit the evidence.
Human confirmation applies to new or changed normative semantics, not to an
entire document or every execution. Continue independent authorized work while
affected checks await a decision. Reuse existing approvals and campaign policy.

Scale artifacts to the target. For a small first target, accepted requirement IDs,
the relevant input/effect model, and runnable commands can be a short spec. Omit
inapplicable template sections. Read only references needed by the active mode;
local-only setup does not need an extended-campaign policy or a new CI service.

## Change

Read [change-and-ci.md](references/change-and-ci.md). Map the diff to affected
requirements, targets, scenarios, and dependencies. Reuse accepted contracts;
update affected generators and oracles, replay regressions, and run the existing
bounded profile. Report skipped targets, invalidated evidence, and semantic
decisions. Established tests must run through ordinary project commands and CI
without a model. The skill maintains that system when invoked; it does not
automatically run on every code change or install a scheduler.

## Specify

Read [interview-and-spec.md](references/interview-and-spec.md). Discover facts
from the repository, documentation, schemas, existing tests, incidents, and
call sites. Ask the human only for decisions, meaning, risk tolerance, and
information that cannot be discovered.

Interview in dependency-ordered rounds: ask the questions whose prerequisites
are settled, give a recommended answer, incorporate the response, and expose
the next unresolved frontier. This adapts Matt Pocock's
[design-tree grilling technique](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md)
to property discovery.

Create or update a versioned fuzzing specification using
[fuzzing-spec.template.md](assets/fuzzing-spec.template.md). Give every
normative requirement a stable ID and record its source. Separate:

- confirmed requirements;
- accepted authoritative requirements;
- behavior inferred from code or existing tests;
- hypotheses worth probing;
- unresolved semantics.

Never silently turn current implementation behavior into the contract. Ask for
confirmation of new or changed normative semantics with a concrete scenario.
An unresolved requirement blocks only the checks that depend on that meaning.

## Build

Read [harness-design.md](references/harness-design.md). Choose generation and
oracle techniques based on the target's shape, using project-native tools when
possible. Build the smallest harness that exercises a meaningful behavioral
seam, then make it deterministic, replayable, observable, and fast.

For filesystem, database, network, queue, process, clock, or other side effects,
also read [side-effects.md](references/side-effects.md). Use its infrastructure
profile when durability, concurrency, or recovery is in scope.

The implementation must include:

- generated values, structures, actions, schedules, or faults;
- a driver that reaches the real target behavior at the chosen seam;
- explicit oracles linked to requirement IDs;
- seed/input/trace capture and single-case replay;
- bounded resource use and useful failure evidence;
- shrinking or reduction when feasible;
- observed scenario and oracle-execution counts for important states and sequences;
- normal project build/CI integration and machine-readable per-run evidence.

Do not derive both the implementation and its oracle solely from the same code.
Do not accept a harness that mocks away the behavior under test, manufactures a
failure, or merely asserts that the process did not crash when semantic
correctness is required.

Dependency installation, external services, new infrastructure, or material
changes to the target require the same authorization they would outside this
skill.

## Campaign

Read [campaign-and-feedback.md](references/campaign-and-feedback.md). Run the
smallest useful local smoke campaign first. Reuse an applicable approved profile.
If the user supplied no budget, cap smoke fuzzing at 30 seconds per target and
two minutes total. Report the result before increasing that budget; runs longer
than ten minutes require an
existing applicable approval or a new explicit budget. Budget triage separately.

Use the repository's existing artifact convention. If none exists, default to:

```text
fuzzing/
|-- FUZZING_SPEC.md
|-- targets/
|   `-- <target>.<profile>.json
|-- CAMPAIGN_LEDGER.md
|-- runs/
|   `-- <unique-run-id>/
`-- failures/
    `-- <failure-id>/
```

Record campaigns with [campaign-ledger.template.md](assets/campaign-ledger.template.md)
and findings with [failure-record.template.md](assets/failure-record.template.md).
Read [run-evidence.md](references/run-evidence.md) for the execution contract and
optional recorder. Preserve immutable evidence per run; the ledger is an index.
Use synthetic data and sanitized output. If exact replay requires sensitive raw
artifacts, retain them only in an explicitly approved restricted store and link
them from a sanitized report; never silently redact the only reproducer.

Preserve first, then reproduce and reduce within the triage budget. Classify
supported findings as a product bug, specification gap, generator gap, oracle
false positive, harness or environment bug, or unknown. Track reproducibility,
confidence, and severity
separately. Preserve an owned backlog when investigation exceeds its budget.
Route findings to durable feedback. Fix product code only when the user's
existing or new request includes the fix.

## Audit

Read [audit.md](references/audit.md). Audit the fuzzer empirically as well as by
inspection. Check requirement-to-oracle traceability, target reachability,
semantic combination coverage, replay, oracle independence, failure
minimization, determinism, throughput, corpus quality, and environment fidelity.

Whenever safe and authorized, test the tester with known historical failures,
negative controls, or isolated seeded defects. Treat line or branch coverage as
an exploration signal, never as evidence that the declared behavior is correct.

End with one of these verdicts and concrete evidence:

- **Ready for campaign**
- **Useful with gaps**
- **Not trustworthy yet**
- **Blocked**, with the missing access, decision, or test seam named

## Feedback invariant

No confirmed finding is complete until its durable consequences are recorded:

```text
product bug       -> minimized regression + linked product issue or fix request
specification gap -> human decision + new specification version
generator gap     -> reachable scenario or distribution improvement
oracle bug        -> corrected oracle + must-not-fail regression
harness bug       -> fidelity or determinism repair
uncertain finding -> preserved evidence + reproduction rate + owned investigation
```

For a production bug that fuzzing missed, determine why the current system did
not find it. Updating only a handwritten regression is insufficient when the
escape exposes a missing requirement, oracle, state transition, fault point, or
important cross-product.

See [research.md](references/research.md) for the annotated sources behind the
workflow.

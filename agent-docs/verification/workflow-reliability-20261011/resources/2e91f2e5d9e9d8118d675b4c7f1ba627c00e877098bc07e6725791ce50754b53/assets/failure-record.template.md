# Fuzz Failure: <failure-id>

| Field | Value |
|---|---|
| Workflow status | `Untriaged` / `Investigating` / `Awaiting decision` / `Fix pending` / `Rejected` / `Closed` |
| Primary cause | `Unknown` / `Product bug` / `Specification gap` / `Generator gap` / `Oracle bug` / `Harness/environment bug` |
| Confidence | `Suspected` / `Confirmed` / `Rejected` |
| Severity and reason | `<impact, independently of reproduction frequency>` |
| Owner / next action | `<owner; bounded replay or investigation step>` |
| Run evidence | `<immutable manifest/result and occurrence links>` |
| Duplicate grouping | `<provisional signature; original cases retained; occurrence count>` |
| First observed | `<timestamp>` |
| Product revision | `<commit/version>` |
| Harness revision | `<commit/version>` |
| Specification version | `<version>` |
| Corpus revision | `<digest/version>` |
| Violated requirement IDs | `<IDs or none>` |

## Summary

<One precise sentence describing the observed failure.>

## Reproduction

- Replay command: `<redacted command>`
- Seed/input: `<seed, path, or digest>`
- Environment: `<sanitized relevant configuration>`
- Attempts: `<count>`
- Successful reproductions: `<count>`
- Reproduction rate: `<percentage>`
- Failure signature: `<stable signature>`
- Reproducibility: `<deterministic/intermittent/not reproduced/not attempted>`
- Investigation budget consumed/remaining: `<time and next limit>`
- Replay artifact policy: `<synthetic/sanitized and verified/restricted raw reference>`
- Side-effect baseline and cleanup: `<owned state; reset; remaining resources>`

## Original generated case

```text
<input, command history, schedule, or link to binary artifact>
```

## Minimized reproducer

```text
<smallest input/history/schedule that preserves the same failure>
```

List any remaining element that appears load-bearing. For flaky failures, state
how minimization affected the reproduction rate.

## Expected and observed behavior

**Expected:** <approved requirement or explicitly uncertain interpretation>

**Observed:** <measured behavior>

**Evidence:** <redacted logs, trace, durable state, sanitizer report, screenshot,
or links to stored artifacts>

## Harness validation

- [ ] The real target path was exercised.
- [ ] The oracle checks an approved requirement, or the semantic gap is explicit.
- [ ] Mocks/fakes did not manufacture the result.
- [ ] The artifact was inspected independently from its producer where useful.
- [ ] Shared artifacts are sanitized; any necessary raw evidence is in an approved restricted store.
- [ ] A sanitized reproducer still reproduces, or its limitations are explicit.

## Classification rationale

<Why this classification fits and plausible alternatives do not.>

## Durable feedback

- Product regression or issue: `<link/path/status>`
- Specification change: `<version/requirement IDs or none>`
- Generator change: `<scenario/dimension/reachability change or none>`
- Oracle change: `<check/must-not-fail regression or none>`
- Harness/environment change: `<control/fidelity/determinism change or none>`
- Campaign follow-up: `<replay/target/budget>`

## Closure

- Closed by/date: `<responsible person or agent/date>`
- Evidence of closure: `<commands/results>`
- Original case replayed after changes: `<result>`
- Minimized case replayed after changes: `<result>`

# Fuzzing Specification: <target>

| Field | Value |
|---|---|
| Specification version | `<integer>` |
| Status | `Draft` / `Partially accepted` / `Accepted` / `Superseded` |
| Target revision | `<commit/version>` |
| Prepared by | `<human/agent>` |
| Acceptance | `<per-requirement decisions below; open decisions do not block unrelated checks>` |

## Goal and behavioral seam

**Goal:** <bug classes, risks, or behaviors this campaign should investigate>

**Target:** <function, API, component, workflow, or system>

**Behavioral seam:** <public boundary through which the real behavior is exercised>

**Observable evidence:** <outputs, state, durable records, events, logs, side effects>

**Out of scope:** <explicit exclusions>

## Evidence consulted

| ID | Source | Location/link | What it establishes | Authority |
|---|---|---|---|---|
| E-001 | `<requirements/code/test/incident/schema>` | `<location>` | `<fact>` | `<authoritative/informative>` |

## Normative requirements and oracles

| Requirement ID/version | Behavior | Status | Acceptance/source | Oracle/check | Observable at seam | Priority |
|---|---|---|---|---|---|---|
| REQ-001/v1 | `<statement>` | `<Confirmed/Authoritative/Open>` | `<accepted source/version or human/date/decision>` | `<executable property>` | `<yes/how>` | `<critical/high/normal>` |

State excluded guarantees explicitly. Accept new/changed meanings per requirement;
preserve prior decisions while their meaning and accepted source remain unchanged.

## Inferred behavior and hypotheses

These statements guide exploration but must not fail the product as normative
requirements until approved.

| ID | Statement | Evidence | Status | Validation needed |
|---|---|---|---|---|
| INF-001 | `<current behavior or candidate property>` | `<source>` | `<inferred/hypothesis>` | `<question or experiment>` |

## Input model

| Dimension | Valid domain/grammar | Invalid or almost-valid | Boundaries/special values | Constraints | Feature label |
|---|---|---|---|---|---|
| `<name>` | `<values/shape>` | `<forms>` | `<values>` | `<relationships>` | `<label>` |

### Important cross-products

| Scenario ID | Ordered predicate and shared operation/resource | Observed evidence | Linked oracles | Required profile/minimum checked histories |
|---|---|---|---|---|
| SCN-001 | `<actual commit -> response lost -> restart -> same operation retried>` | `<trace/durable state>` | `<requirement IDs>` | `<PR: 1 directed case; extended: additional variation>` |

Record generated, observed, and checked counts separately. A scenario counts as
checked only when its observed predicate holds and all its required oracles run.

## State and action model

### States

| State | Meaning | Observable evidence |
|---|---|---|
| `<state>` | `<definition>` | `<how detected>` |

### Actions

| Action | Preconditions | Generated arguments | State/result effect | Invalid-transition behavior | Feature label |
|---|---|---|---|---|---|
| `<action>` | `<conditions>` | `<strategies>` | `<expected effect>` | `<reject/ignore/etc.>` | `<label>` |

## Fault and schedule model

| Fault/schedule | Injection point | Preconditions | Required behavior | Feature label |
|---|---|---|---|---|
| `<timeout/retry/duplicate/reorder/restart/race>` | `<boundary>` | `<conditions>` | `<requirement ID>` | `<label>` |

For infrastructure, define fault assumptions, acknowledgment/durability boundaries,
uncertain outcomes, and safety during faults. Specify restored conditions,
scheduling/workload assumptions, and a justified recovery deadline for progress.
Omit this expansion when the target is stateless and these concerns do not apply.

## Harness and environment constraints

- Project-native tool/framework: `<existing or proposed>`
- Setup/teardown and isolation: `<details>`
- Determinism controls: `<RNG, clock, network, filesystem, scheduler>`
- Seed/corpus sources: `<locations>`
- Replay interface: `<required command/arguments>`
- Secrets and sensitive-data policy: `<redaction/exclusion>`
- External services or permissions: `<requirements>`
- Side-effect boundary: `<real product code, real dependencies, substitutes and fidelity limits>`
- Resolved resources: `<owned filesystem/database/broker/endpoints and isolation checks>`
- Observation: `<fresh readers, durable effects, independent traces>`
- Cleanup: `<per-case reset, timeout/interruption behavior, owned leftover resources>`
- Real-environment checks: `<which substitute assumptions are validated, or explicit gaps>`

## Development integration

- Affected paths/dependencies: `<target selection and shared callers>`
- Build, regression, smoke, and single-case replay commands: `<existing commands>`
- Profile locations: `<project config or target profile JSON>`
- CI job and scheduling state: `<installed/verified/local-only; link or reason>`
- Protected regressions/scenarios: `<must survive corpus minimization>`
- Audit evidence: `<run IDs; scope; changes requiring revalidation>`

## Campaign policy

| Tier | Budget | Targets | Stop conditions | Artifact location | Existing authorization/scope |
|---|---|---|---|---|---|
| Replay controls | `<cases/time>` | `<targets>` | `<expected outcomes>` | `<path>` | `<decision>` |
| Smoke/PR | `<default: 30s/target, 2m total exploration>` | `<targets>` | `<conditions>` | `<path>` | `<decision>` |
| Extended | `<approved time/compute/storage>` | `<targets>` | `<conditions>` | `<path>` | `<decision/owner/notification>` |
| Triage | `<default: 5m total per invocation>` | `<priority signatures>` | `<preserve owned backlog>` | `<path>` | `<decision/owner>` |

Account for compilation and service startup separately. Specify resource limits
and the retention/access policy for run records, corpora, and failure bundles.

## Open decisions

| Decision ID | Question | Why it changes the fuzzer | Recommended answer | Owner |
|---|---|---|---|---|
| OPEN-001 | `<question>` | `<impact>` | `<recommendation>` | `<human>` |

## Approval and change history

| Version | Date | Status | Changed requirements/generators/oracles | Acceptance decisions |
|---|---|---|---|---|
| 1 | `<date>` | `<Draft/Approved>` | `<summary>` | `<name>` |

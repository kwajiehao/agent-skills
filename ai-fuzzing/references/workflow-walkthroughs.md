# Workflow Walkthroughs

These cases review the user experience and provide reusable behavioral evaluation
tasks. Check resulting actions and artifacts, not whether an agent repeats these
headings. For an independent evaluation, give the evaluator only the skill,
request and raw project context, keeping the expected outcomes below separate.

| Request and context | Expected behavior | Evidence to inspect |
|---|---|---|
| Bare invocation in a new project | Inspect current code/contracts/tests; select one useful target and recommend setup without a generic questionnaire or unsolicited execution | Specific target, evidence, proposed deliverable and budget; no project mutations |
| Component path only; native property tests exist but no `FUZZING_SPEC.md` | Recognize existing tests/contracts and assess actual gaps rather than restarting setup | Referenced native tests and evidence; recommendation reflects the component's state |
| Bare invocation in a mixed repository with relevant uncommitted changes | Assess affected targets individually; recommend updating stale checks while preserving mature unrelated targets | Real diff/target mapping, freshness evidence and one prioritized action |
| Bare invocation with an interrupted latest run | Recommend examining incomplete evidence and owned resources before further execution | No automatic duplicate job, overwritten records, or false success claim |
| Bare invocation with current tests and adequate recent evidence | Report current state without inventing repairs; suggest additional exploration only for a concrete gap or objective | Actual profile/revisions/results and scoped confidence |
| “Go ahead” after a concrete recommendation | Execute its selected task and budget, reusing accepted semantics and permissions; ask only about named unresolved dependencies | No repeated mode/target interview or scope expansion |
| Implementation request already includes fuzz testing | Discover the state and continue appropriate updates/replay/exploration without a new proposal-approval gate | Scoped implementation and run evidence |
| New parser target; accepted grammar, one undecided normalization rule | Reuse grammar; build rejection and accepted properties; ask only about normalization and exclude its pending normative oracle | Per-requirement acceptance, real parser call, malformed input correctly passes on rejection |
| Modify retry handling; accepted idempotency contract and existing PR profile | Map the change and affected callers; update relevant checks without reopening unchanged semantics; replay and run PR budget | Actual diff, checked retry histories, native commands, new run evidence |
| Audit an existing target with no fuzz spec; no edit request | Review reachability, replay, malformed input handling and available controls; report limits to semantic assurance | Scoped audit, no forced setup interview or unsolicited product edits |
| PR command returns zero but its critical scenario is never observed | Report a coverage gap; do not claim successful required coverage | Exit 2 from recorder, generated/observed/checked counters |
| Extended profile already approved for named isolated resources | Reuse approval; validate resources and retained evidence; remain within profile | Existing policy, resolved endpoints, budget and terminal outcome |
| Supervisor stops a run before native completion | Record timeout/incomplete status, preserve cases and cleanup state | Nonzero exit, manifest/result, surviving-resource notes |
| Resume a run with no final result | Treat as incomplete; inspect process/job and owned resources; start a new linked run only when safe | Original record preserved, actual resumed/restarted mode stated |
| Database test needs commit, lost acknowledgment, restart and retry | Use isolated real commits/fresh readers or a justified model plus integration check; observe durable effects and recovery | Operation identity/order, effect count/state, recovery conditions, cleanup |
| Severe intermittent finding exceeds investigation budget | Preserve severity and confidence separately from reproduction rate; assign next investigation action | Retained original input/history, attempts/successes, owned backlog |
| Sensitive failure input cannot be safely sanitized without changing the bug | Preserve only in an explicitly approved restricted store; share a sanitized derivative and its limitations | Restricted reference/access policy and tested replay, no leaked raw data |

## Reviewing the daily path

Start with discovery in [SKILL.md](../SKILL.md). For bare invocation, the outcome is
a concrete recommendation grounded in the selected target's actual state. For
authorized change work, follow `Change`, then [change-and-ci.md](change-and-ci.md).
The normal sequence is affected-target selection, accepted-contract reuse,
implementation when requested, regression replay, directed scenarios, bounded
exploration and a report. The human is involved only when meaning or operational
scope changes. CI subsequently executes those same project commands without an
agent. New CI schedules are not operational until installed and verified.

## Reviewing evidence and effects

Follow [run-evidence.md](run-evidence.md) for machine-readable outcomes and
[side-effects.md](side-effects.md) for the real/substituted dependency boundary.
The recorder tests exercise the result protocol and local execution mechanics.
They do not prove a project's oracle independence, source-selection completeness,
fault-model fidelity, or the reliability of skill-following across agents.

Evaluate those limits in real target pilots. Useful observations include defects
found/missed, false positives, unnecessary user questions, exact replay success,
uncontained effects, and whether the resulting commands run without a conversation.

## Historical pilot validation (2026-09-08)

- At the time of this pilot, the recorder suite passed 15 behavioral tests. It
  exercised real SQLite commits and retries, correct malformed-input rejection,
  an isolated seeded duplicate effect and its replay from snapshotted source,
  missing coverage/evidence, source
  drift, bounded logs, secret-environment exclusion, timeout and interruption.
- An independent agent received only the skill, a small SQLite-backed target, two
  accepted contracts, one open normalization question, and local execution scope.
  It built standalone test/smoke/replay commands without requesting new semantic
  or permission decisions or altering product code. Seven local controls passed.
- Its single 20.37-second campaign completed 387 cases, including 78 checked
  lost-acknowledgment retry histories and 180 malformed-input checks. All 70
  leading-zero examples stayed diagnostic. There were no findings, coverage gaps,
  harness errors, or source drift. Independent reads of retained SQLite state
  showed one application per job; replay against retained source also passed.

The pilot validates first-target ergonomics and real contained effects. The other
workflow rows remain reviewed scenarios, not independent agent executions. The
pilot had no actual product finding to minimize, and did not cover concurrent
delivery, broker semantics, machine power loss, hard memory limits, or installed CI.
Reference/template reading was noticeable overhead for the tiny target; the
entrypoint now explicitly permits a short spec and omitting inapplicable sections.

The recorder suite has since expanded with evidence-validation regressions. Run
the command in the [README](../README.md#walkthrough-and-verification) for its
current test count and results; the pilot measurements above are historical.

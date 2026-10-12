# AI-assisted fuzzing

This skill helps an agent build and maintain a testing system that generates
inputs, actions, schedules, or faults; exercises your real code; and checks its
behavior against explicit requirements. The agent designs and improves the
system. Project-native tools perform the high-volume execution.

Use it as the fuzzing/property-testing part of a broader development workflow,
alongside ordinary tests and reviews. It supports pure functions, parsers,
stateful services, and infrastructure with side effects. A clean bounded campaign
is evidence about the selected checks and scenarios, not a proof of correctness.

## How you use it

Invoke `ai-fuzzing` using your agent's skill mechanism, or ask it to use the
[SKILL.md](SKILL.md) in this directory. Installation is covered in the
[repository README](../README.md).

The minimal invocation is enough:

```text
$ai-fuzzing
```

It inspects the current directory/repository. Optionally narrow the target:

```text
$ai-fuzzing src/queue/
```

The skill figures out what is already in place, whether changes or findings need
attention, and the next useful task. It considers each component separately and
recognizes existing native property tests even without its own specification files.
You do not need to know the testing stage or supply the workflow instructions.

For example, its recommendation might be:

> The queue has example tests but no generated retry histories. Its idempotency
> contract is already documented. I recommend adding a stateful harness against an
> isolated database, checking committed effects after acknowledgment loss and retry,
> then running a 30-second smoke campaign and leaving a replay command.

Bare invocation inspects and proposes; reply “go ahead” to execute that concrete
recommendation. If you already asked it to implement a change and test it, or to
set up/run fuzzing, it proceeds within that request after selecting the right work.
It asks only for genuinely missing meaning or execution scope. Established tests
then run through normal project commands and CI without a model or conversation.

You can still steer it with a short request:

| Situation | Example request | Expected result |
|---|---|---|
| Discover next work | `$ai-fuzzing` or `$ai-fuzzing src/queue/` | Evidence-backed state assessment and one recommended next action |
| First target | “Set up fuzzing here.” | Scoped requirements, a real harness, replay, smoke evidence and audit |
| Code change | “Update fuzz tests for this diff.” | Affected targets/properties updated, accepted contracts reused, regressions replayed and bounded exploration |
| Existing harness | “Audit this fuzzer.” | A scoped audit even if no formal fuzzing specification exists |
| Campaign | “Run the extended profile.” | Reuse applicable approval, run within its budget, retain evidence and triage backlog |
| Finding | “Investigate this failure.” | Preserve and replay it, investigate within the default or existing triage budget |
| Resume | “Continue from this run.” | Inspect saved evidence/resources, then use a new linked run or native checkpoint |

## The intended development loop

Set up each useful target once: identify accepted behavior, build an independent
check, choose a contained environment, verify replay, and connect commands to the
project's build and CI. Ask the agent to revisit affected targets when behavior,
dependencies, or architecture changes. This skill does not automatically attach
itself to every implementation task or start background jobs.

During normal development, deterministic regressions and directed required
scenarios give predictable feedback. Bounded exploration tries additional inputs
and retains discoveries. Approved extended jobs explore more seeds, histories,
faults and configurations. Findings improve the relevant requirement, generator,
oracle, harness or corpus, and product fixes when those are requested.

The human decides new or changed product meaning and execution scope. Previously
accepted requirements and applicable budgets are reused. An unresolved requirement
blocks only its dependent normative checks; useful independent work continues.
The report names any guarantee that remains untested.

Without an existing policy, smoke exploration is capped at 30 seconds per target
and two minutes total; triage has a separate five-minute total budget. Build and
environment startup costs are recorded separately. Longer campaigns use explicit
budgets, ownership and retention policy. A run can finish while investigation
remains in an owned backlog.

## What stays in your project

Use existing project conventions. Otherwise, the skill starts with:

```text
fuzzing/
  FUZZING_SPEC.md             accepted requirements and unresolved decisions
  targets/<target>.<tier>.json commands, budgets, required checks and provenance
  runs/<unique-id>/           immutable per-run evidence and retained cases
  CAMPAIGN_LEDGER.md          index of runs, gaps and follow-up work
  failures/<id>/              cause, evidence, reproduction and durable feedback
```

Harness source belongs with the project's tests/build. Keep protected regressions
and required scenarios when minimizing the exploratory corpus. Large corpora and
raw logs may live in retained artifact storage; do not commit sensitive data or
unbounded run output by default. Configure ignore/retention rules for the project.

The skill includes a small optional [run recorder](scripts/run_campaign.py) that
wraps a native test command and captures selected source snapshots, profile,
environment, output, result and termination reason. Use the existing runner if it
already does this. The [integration contract](references/run-evidence.md) explains
the profile, adapter report and exit codes. The recorder is not a fuzzing engine,
sandbox, scheduler or automatic secret redactor.
When adopting it, version a copy in your project so CI and other developers do not
depend on an agent's local skill installation.

CI succeeds only when the command completes, selected checks execute, required
scenarios reach their checked minimums, and no findings or harness errors occur.
Missing evidence, missing required coverage, timeout and interruption are distinct
non-success outcomes. Always retain run artifacts, including unsuccessful runs.

## Code with side effects

The skill tests effects in a contained environment and observes their actual
consequences. The [side-effect guide](references/side-effects.md) gives selection,
observation, isolation, cleanup and recovery rules.

- Files use owned temporary directories; filesystem semantics use a real filesystem.
- Database commit/restart behavior uses an isolated real database and fresh readers.
  A rollback fixture is suitable only when it preserves the behavior being checked.
- Retry logic can use a local server that receives a request and loses its response.
  Email and payment effects use local sinks or approved sandboxes with synthetic identities.
- Stateful cases preserve state within each history and reset between independent
  histories. Faults, observed effects and relevant scheduling choices are retained.

For example, a queue test can commit a business effect, lose the acknowledgment,
restart the worker and redeliver the same job. It checks durable state to determine
whether the declared duplicate-delivery contract holds. After faults stop, a
separate check verifies progress under the specified recovery conditions.

Controlled substitutes are useful when their boundary and assumptions are clear.
They must execute the relevant product logic. Claims about real persistence,
protocols or providers need corresponding integration evidence. Resolved resources
and credentials are checked before execution; a name like `TEST_DATABASE_URL`
does not establish safety. Cleanup targets only resources owned by the run.

## Walkthrough and verification

The routing above is the intended user contract. [Workflow walkthroughs](references/workflow-walkthroughs.md)
map representative requests to the responsible instructions and expected evidence.
They are review cases, not a claim that all agent behavior has been empirically proven.

The recorder's executable checks cover valid rejection, actual findings, required
coverage, missing evidence, interruption, source capture and isolated side effects.
They also check impossible history counts, bounded JSON metadata, complete
no-overwrite record publication, and finding retention through worker cleanup:

```bash
python3 -m unittest discover -s tests -v
```

The references provide mode-specific instructions; [research.md](references/research.md)
contains the annotated methodological sources.

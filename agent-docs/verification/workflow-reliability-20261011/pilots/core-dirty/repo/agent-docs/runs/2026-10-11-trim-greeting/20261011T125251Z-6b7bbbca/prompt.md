# Agent Task: 2026-10-11-trim-greeting Trim surrounding whitespace from greeting names

Read the task doc and listed context, then make the smallest correct change.

## Task Doc

/private/tmp/workflow-pilots-20261011.jYJEET/core-dirty/repo/agent-docs/tasks/2026-10-11-trim-greeting-trim-surrounding-whitespace-from-greeting-names.md

Immutable prepared copy: /private/tmp/workflow-pilots-20261011.jYJEET/core-dirty/repo/agent-docs/runs/2026-10-11-trim-greeting/20261011T125251Z-6b7bbbca/task.snapshot.md

Do not revise the task contract during execution. An intentional scope change
requires an explicitly revised task and a new prepared run; preserve the old run.

## Read First

- `agent-docs/MEMORY.md`
- `agent-docs/skills/README.md`
- `greeting.py`
- `tests/test_greeting.py`
- `CODING.md`
- `TESTING.md`

Read relevant durable memory and the local skill index. Follow indexed skills
when they apply; do not load unrelated history.

## Allowed Paths

- `greeting.py`
- `tests/**`
- `agent-docs/tasks/**`
- `agent-docs/runs/**`

## Required Test Commands

- `/private/tmp/agent-workflow-dev-20261011/bin/python -m unittest discover -s tests -v`

## Optional Smoke Command

None

## Acceptance Evidence

- Greeting names omit leading and trailing spaces, tabs, and newlines.: `/private/tmp/agent-workflow-dev-20261011/bin/python -m unittest discover -s tests -v`
- Existing greeting punctuation and internal name whitespace are preserved.: `/private/tmp/agent-workflow-dev-20261011/bin/python -m unittest discover -s tests -v`

The runner records whether each mapped command passes and hashes optional
evidence files. These gates do not prove requirements beyond the declared checks.

## Coordination

Mode: `solo`

Required subagent artifacts:
- None

The coordinator may implement directly. Optional subagent work can still be recorded in `subagents/`.

## Session Handoff

Keep durable notes in:

/private/tmp/workflow-pilots-20261011.jYJEET/core-dirty/repo/agent-docs/runs/2026-10-11-trim-greeting/20261011T125251Z-6b7bbbca/handoff.md

If using subagents, keep their briefs and findings in:

/private/tmp/workflow-pilots-20261011.jYJEET/core-dirty/repo/agent-docs/runs/2026-10-11-trim-greeting/20261011T125251Z-6b7bbbca/subagents

## Simplify And Review

Inspect the patch for unnecessary complexity and duplication. Use the client's
native simplify action when useful and available; no external CLI or model is
required. Include resulting edits in the required review.

After a reviewer inspects the final patch and writes `subagents/reviewer.md`,
bind that artifact to the current task and code (required for review/delegated):

```bash
/private/tmp/agent-workflow-dev-20261011/bin/python /private/tmp/workflow-pilots-20261011.jYJEET/core/loop/run_task.py /private/tmp/workflow-pilots-20261011.jYJEET/core-dirty/repo/agent-docs/tasks/2026-10-11-trim-greeting-trim-surrounding-whitespace-from-greeting-names.md --repo-root /private/tmp/workflow-pilots-20261011.jYJEET/core-dirty/repo --record-review --run-dir /private/tmp/workflow-pilots-20261011.jYJEET/core-dirty/repo/agent-docs/runs/2026-10-11-trim-greeting/20261011T125251Z-6b7bbbca
```

This records artifact freshness; it cannot prove reviewer independence. Any
subsequent code or reviewer-artifact changes require fresh review and recording.

## Verification

Use focused regression commands for red/green work. The final runner executes
declared test and smoke commands, so do not duplicate a complete verification
run immediately beforehand. After editing and required review, run:

```bash
/private/tmp/agent-workflow-dev-20261011/bin/python /private/tmp/workflow-pilots-20261011.jYJEET/core/loop/run_task.py /private/tmp/workflow-pilots-20261011.jYJEET/core-dirty/repo/agent-docs/tasks/2026-10-11-trim-greeting-trim-surrounding-whitespace-from-greeting-names.md --repo-root /private/tmp/workflow-pilots-20261011.jYJEET/core-dirty/repo --verify-only --run-dir /private/tmp/workflow-pilots-20261011.jYJEET/core-dirty/repo/agent-docs/runs/2026-10-11-trim-greeting/20261011T125251Z-6b7bbbca
```

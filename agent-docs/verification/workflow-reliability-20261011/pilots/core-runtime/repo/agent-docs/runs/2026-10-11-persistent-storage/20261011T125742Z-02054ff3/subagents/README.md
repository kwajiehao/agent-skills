# Subagents: 2026-10-11-persistent-storage Persist saved values across process restarts

Coordination mode: `solo`

Required artifacts:

- None

Use this directory only when a subagent is actually helpful or required by the
task's coordination mode.

The coordinator owns the run: it reads the task contract, invokes required
subagents, integrates accepted findings, runs the task commands, and runs final
verification. The runner remains the deterministic verifier.

When invoking a role, include the role characterization from the task metadata
as the first part of the brief. The characterization should describe the
relevant experience for this task, such as the domain, system type, scale,
language, or review specialty.

## Maker

The maker implements a bounded change inside assigned paths. The maker does not
decide final acceptance.

Characterization:

> Not required by this coordination mode.

Use `maker.md` for delegated maker work:

```md
# Maker Brief

Characterization: <copy the task-specific maker characterization>
Task:
Allowed paths:
Files owned:
Required tests:

# Maker Result

Files changed:
Commands run:
Notes:
```

## Reviewer

The reviewer independently reviews the diff, tests, and artifacts. The reviewer
does not edit by default; it reports findings with evidence.

Characterization:

> Not required by this coordination mode.

Use `reviewer.md` for required or optional review work:

```md
# Reviewer Brief

Characterization: <copy the task-specific reviewer characterization>
Task:
Diff/artifacts reviewed:
Focus areas:

# Reviewer Findings

- Severity:
  File:
  Issue:
  Evidence:
  Recommendation:

Verdict: approve | changes_requested
```

Each file should contain:

- the brief given to the subagent
- files or artifacts it reviewed
- findings, commands, and evidence
- recommended next action

For `review` and `delegated` modes, final verification requires
`subagents/reviewer.md` to contain an exact `Verdict: approve` line. The
coordinator owns final decisions and summarizes accepted findings back into
`../handoff.md`.

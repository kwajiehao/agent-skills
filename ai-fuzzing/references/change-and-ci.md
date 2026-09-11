# Changes, CI, and Resumption

Use for everyday changes affecting existing fuzz targets and for integrating
established targets into the development loop. Reuse project commands and CI.

## Test a change

1. Establish the actual comparison from the request and repository state. Include
   staged, unstaged, and relevant untracked work. Record the baseline; do not
   assume `HEAD~1` describes the user's change.
2. Map changed interfaces, shared dependencies, state transitions, schemas, and
   fault handling to requirement IDs and targets. Follow callers when a shared
   helper changes. Broaden target selection when the impact cannot be bounded.
3. Reuse accepted semantics and applicable execution approvals. Present only
   new/changed meanings for confirmation. Keep unresolved properties diagnostic;
   continue unaffected checks and report their limited scope.
4. Update affected generators, observers, models, replay formats, and scenario
   counters when implementation is requested. For a run/review-only request,
   report needed changes without silently implementing them.
5. Build affected targets, replay retained regressions, and run the existing PR
   or smoke profile. Explicitly report targets omitted to fit the total budget.
6. Report findings, unmet required scenarios, harness errors, and outstanding
   decisions with links to run records. Preserve the failure backlog.

If the requested behavior has no target, build the smallest useful one within
the authorized change. If a test seam needs a material product redesign outside
that scope, document the concrete seam and ask only for that expansion.

## Evidence freshness

Requirement acceptance persists until the meaning or authoritative source changes;
a new commit alone does not require reapproval. Track approvals per requirement.

Audit evidence has a narrower lifetime. Recheck affected controls and traceability
when the target, oracle, generator, observer, dependency, configuration, or fault
model changes. Revalidate replay after an input-format or framework change.
Record why prior evidence still applies when reusing it. Never migrate a stored
failure in place: retain the original and link the migrated form.

## Integrate once, execute routinely

Keep target source and configuration in the repository and build them with normal
tests. Expose discoverable commands for regression replay, bounded exploration,
single-case replay, and optional extended exploration. Document the real commands;
do not invent a parallel command system when the project already has one.

Use [target-profile.template.json](../assets/target-profile.template.json) as a
starting point only when the project lacks equivalent configuration. Each profile
records one target's command, selected requirements, required scenario counts,
budget, source inputs, and existing authorization. It is configuration, not a
grant of permission. Adapt it to the project's runner if that runner already
captures equivalent evidence. The optional recorder contract is in
[run-evidence.md](run-evidence.md).

When adopting the optional recorder for CI, copy and version it in the project's
test tooling, or use a pinned tool package. CI must not depend on an agent's home
directory or an unpinned skill installation. Record the helper version with runs.

| Tier | Required behavior | Human involvement |
|---|---|---|
| Local/PR | Build, deterministic regression replay, forced required scenarios, bounded fresh exploration | Only changed semantics or execution scope |
| Extended | Diverse seeds and schedules, broader environment/configuration coverage, corpus retention | Reuse approved resources, owner, storage and notification policy |
| Periodic audit | Challenge affected oracles, replay historical defects on appropriate revisions, review coverage gaps and production escapes | Resolve actual contract questions |

Required PR scenarios should have deterministic scenario replay or directed
generation so chance does not make CI intermittently miss its minimum coverage.
Keep exploratory seeds varied; retain seeds and failing traces for replay.
Corpus minimization must preserve protected regressions and required semantic
scenarios, even when their code coverage overlaps other cases.

Fail the relevant CI job on findings, missing required coverage, harness errors,
or incomplete execution. An unresolved optional hypothesis does not fail the
product; an unresolved required guarantee prevents claiming that guarantee was
verified. Temporary exceptions need a named gap, owner, and expiry; never silently
disable a failing check. A completed run is bounded evidence, not a release verdict.

If CI setup is in scope, wire and validate the existing CI job. If it requires
new external compute or permissions, finish the local integration and present
the concrete remaining configuration. A schedule or alert is only operational
after it is installed and verified; documentation alone does not start it.

## Resume without reconstructing the conversation

Read the target profile, accepted requirement versions, latest run manifest and
result, and open failure records. Determine what completed and what remains.
Reuse approvals only while target, environment, and budget scope still match.

A missing final result means incomplete execution, never success. Check for a
surviving process or owned remote job before starting another. Recover retained
inputs and inspect cleanup state. Do not kill unrelated processes or delete a
shared namespace. Resume from a framework checkpoint when supported; otherwise
start a new bounded run using the saved corpus/trace. Give it a new run directory
and link its predecessor. Preserve the original record, including interrupted
runs. Do not claim to continue the exact random stream without engine support.

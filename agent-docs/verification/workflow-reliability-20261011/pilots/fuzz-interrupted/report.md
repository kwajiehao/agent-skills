# Interrupted fuzz-run assessment

Scope: assessment only, offline; no project commands, tests, campaigns, installs, or project modifications were performed. Applied the frozen skill at `/private/tmp/workflow-pilots-20261011.jYJEET/fuzz-skill/SKILL.md` and its campaign, run-evidence, and resumption references.

## State

The job-effect store has an accepted contract of one durable effect per `job_id`, including retry after a committed effect's acknowledgement is lost (`repo/README.md`). The only source test exercises one successful delivery; it does not exercise lost acknowledgement and retry. Inspection of `store.py` shows an unconditional insertion on each call, with the timeout raised after commit. This is a concrete suspected contract violation on retry, not an executed or reproduced finding.

The prior run record (`repo/latest-run.json`) states `status: running`, records PID `2147483647`, and references `runs/prior/result.json` and owned resource `runs/prior/jobs.sqlite`. The entire referenced `runs` directory is absent. There is no terminal outcome, retained input/trace, source snapshot, target profile, command, budget, or report among the files found. The record therefore establishes incomplete execution, not success, and cannot establish a reproducible checkpoint.

Local process liveness is **unverified**. The sandbox rejected the read-only `ps` diagnostic; its subsequent escalation request was aborted without a process result. Do not infer that the recorded PID is alive or dead, or signal it without establishing identity and ownership. No owned process was launched by this assessment.

Repository snapshot: commit `d0a00dd` (`evaluation fixture`); `git status --short` showed only untracked `latest-run.json`. Project files were left unchanged. No applicable `AGENTS.md` was found in the inspected target tree or explicitly checked ancestors.

## Recommended next action

Complete a bounded interrupted-run recovery assessment first: verify the recorded PID's identity/liveness using an available read-only process inspection, locate any retained checkpoint/corpus/logs and the actual prior command/profile, and account for owned resources. Preserve `latest-run.json` unchanged; record recovery observations separately. A concrete diagnostic is `ps -p 2147483647 -o pid=,ppid=,etime=,stat=,command=`; budget about four minutes, with no new campaign or cleanup during that assessment.

Expected deliverable: a recovery record distinguishing confirmed process/resource state from missing evidence and stating whether a safe restart can be prepared. The existing evidence is insufficient to continue an exact random stream or reuse a recorded campaign budget. A later authorized run would require a new run directory linked to `prior-run`, an explicit bounded profile, and preserved source/input/result evidence.

After recovery, the useful testing task is a lost-acknowledgement/retry scenario asserting one durable effect per job ID. Accepted semantics already cover it; implementation or execution is outside this assessment's scope. The documented current test command is `python3 -m unittest discover -s tests -v`, but it was not run and does not currently cover that scenario.

## Evidence

Command outputs and limitations are retained in `assessment-command-output.md` next to this report. Source references: `repo/README.md`, `repo/store.py`, `repo/tests/test_store.py`, `repo/latest-run.json`.

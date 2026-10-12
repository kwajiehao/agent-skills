# Executable Run Evidence

Use the project's existing runner when it captures equivalent evidence. Otherwise
adapt [target-profile.template.json](../assets/target-profile.template.json) and
use [run_campaign.py](../scripts/run_campaign.py), a Python 3.10+ stdlib recorder
for macOS/Linux/WSL. It wraps one existing command; it does not generate inputs,
install CI, provision services, establish approvals, or sandbox the command.

## Profile and invocation

Keep one profile per target/budget in project configuration. Populate the template
from repository evidence and existing decisions. `command` is an argument array,
executed without an implicit shell from `--repo`. Put normal regression replay,
directed required scenarios and exploratory fuzzing in the project's own command.

Select `source_files` explicitly: relevant product and harness code, generator and
oracle code, spec, build/configuration files, lockfiles and necessary fixtures.
These are individual relative files, including relevant uncommitted/untracked
files. Symlinks and `..` are rejected. The recorder stores their exact bytes and
hashes; review the selection for secrets and completeness before capture. Record
toolchain and dependency identities and a retained corpus digest in `revisions`.
If a source closure is too large, use the native build's immutable source/build
artifact support instead of claiming a partial snapshot is complete.

Example invocation from the target repository; replace the script and plan paths:

```bash
python3 /path/to/ai-fuzzing/scripts/run_campaign.py \
  --repo . --plan fuzzing/targets/queue.smoke.json \
  --run-dir fuzzing/runs/queue-smoke-unique-id
```

The run directory must not already exist. The recorder writes `manifest.json`
before execution, `process.json` after launch, reviewed source snapshots under
`source/`, at most 1 MiB of combined output in `output.log`, and a final
`result.json`. Never reuse or edit an old run directory; link a predecessor using
an optional `parent_run` metadata field in the next profile. Artifact immutability
here means append-only usage by the recorder, not tamper-proof storage.
JSON records are fully serialized and flushed before atomic, no-overwrite
publication; the run filesystem must support same-directory hard links.

For independent project/CI use, copy and version the recorder in the project's
test tooling or replace it with the existing native runner. Use that project path
in CI; the example skill path above is for initial local integration.

The child receives `PATH`, explicit profile `environment` values, and `FUZZ_RUN_DIR`.
It does not inherit other ambient credentials or configuration. All passed values,
the command, selected sources and output are retained: use only reviewed synthetic
data and nonsecret configuration with this helper. It does not redact automatically.
Use the project's approved restricted runner/store when secrets are necessary.
Set native memory/case/step limits in the command or isolated environment; the
helper enforces only a wall-clock timeout and its own output/report limits.

Do not daemonize or detach descendants. The helper terminates its process group
at exit, timeout, or ordinary interruption; a container/remote job or detached
process needs its own owned lifecycle. It cannot contain filesystem/network effects.
If the host denies group cleanup, the recorder attempts direct-child termination
and retains a diagnostic requiring inspection of owned descendants. Cleanup failure
cannot turn an otherwise successful run into a passing result.

## Native adapter result

The project command should join its workers and write a complete `report.json`
under `FUZZ_RUN_DIR` before exiting. The recorder reads it after owned-process
cleanup and output collection, so findings/errors flushed during teardown are
included and final artifact paths are checked. Timeout/interruption still mean
incomplete execution even when a partial report survives and is retained.
Generate it from actual engine/observer results, never agent estimates. A small
adapter may translate native test output. Commands without an adapter remain
usable directly, but cannot receive a successful result from this recorder.
Both the profile and report require integer `schema_version: 1`, not `true` or
`1.0`. Profile `timeout_seconds` must be positive and representable as a finite
Python float; invalid profiles are rejected before launching the command.

```json
{
  "schema_version": 1,
  "cases": 40,
  "oracle_checks": {"REQ-001": 40},
  "scenarios": {
    "SCN-001": {"generated": 5, "observed": 3, "checked": 3}
  },
  "findings": [],
  "harness_errors": []
}
```

Counts are nonnegative integers. Scenario counts use cases/histories and require
`checked <= observed <= generated` and `observed <= cases`; count each history
at most once per scenario, even if its events repeat. Scenarios may overlap, so
their counts need not sum to at most `cases`. Generated histories that were not
executed may exceed `cases`. The checked predicate includes all linked oracles
and correct order/entity identity. `requirements` lists accepted checks
that must execute at least once. `required_scenarios` maps IDs to minimum checked
counts; use `{}` only when no meaningful combination is required for this target.

Every finding is an object such as
`{"id": "F-001", "artifact": "findings/F-001.json"}` pointing to a retained file
inside the run directory. Preserve the actual input/history and failure signature
there before reporting it. A report is at most 1 MiB; large traces belong in linked
artifacts. Artifact paths are validated after owned-process cleanup; a case removed
during teardown is an evidence error, not a retained finding.

Extra native metrics may be included. Profile and report JSON require unique keys
within every object, including nested objects and escaped spellings of the same
key. They must contain only finite numbers and at most 64 nested object/array
levels, counting the root container as level 1. Duplicate keys, nonfinite values
(including numeric overflow) or excessive nesting in a report produce a valid
`harness_error` result with a diagnostic and
`report: null`; the raw `report.json` remains for investigation. Known-defect
self-tests validate expected failures inside the adapter; they do not become
ordinary product findings.

## Outcomes and CI

| Exit code | Status | Meaning |
|---|---|---|
| 0 | `completed` | Command succeeded, cases ran, selected checks/scenarios met minimums, no findings/errors |
| 1 | `findings` | Valid report contains retained findings; product cause still needs triage |
| 2 | `coverage_gap` | Command succeeded but required checks/scenarios or executed cases are missing |
| 3 | `harness_error` | Missing/malformed evidence, explicit harness error, unexplained command failure, or selected source drift |
| 4 | `timed_out` | Supervisor deadline expired; execution is incomplete |
| 5 | `interrupted` | Ordinary SIGINT/SIGTERM interruption was recorded |

Timeout/interruption and evidence errors take precedence over successful claims;
reported harness errors take precedence over findings, and findings over coverage
gaps. The final result retains parsed findings and gaps together when available.
Missing `result.json` after a machine crash or SIGKILL means incomplete, never
success. Raw artifacts may survive even without a valid final report: inspect them
when resuming. The helper never restarts an interrupted campaign automatically.

CI consumes the exit code and archives the whole run directory on every outcome.
Keep the ledger as links/summaries derived from those files. Triage and cleanup are
separate work with their own budget and owner; exit 1 does not mean diagnosis is done.

## Limits to replay and trust

Source is snapshotted before running in the original repository, and selected
files are hashed again afterward. Detected drift prevents a passing result. Avoid
concurrent edits during a run: the helper cannot detect change-and-revert races,
unlisted dependencies, mutable services, or a dishonest adapter. Pin and retain
external build/service/corpus artifacts, and capture real schedules where needed.

Replay in a disposable environment using the retained source, dependency/toolchain
identities, profile, input/history and environment baseline. Validate replay as part
of the harness audit. Never restore snapshots over the user's working files.
The recorder validates evidence structure and minimum counts; empirical controls
and independent observation establish whether that evidence describes real testing.

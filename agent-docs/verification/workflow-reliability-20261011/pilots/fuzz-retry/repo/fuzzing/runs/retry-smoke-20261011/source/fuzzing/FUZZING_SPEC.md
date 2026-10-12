# Retry contract v1

Source: accepted requirements in README.md. No new product semantics added.

- REQ-001: Exactly one durable effect per job_id, including repeated delivery
  after a committed effect's acknowledgement was lost.
- REQ-002: lose_ack=True commits an effect and then raises TimeoutError.

Inputs are histories of 2–14 calls using synthetic string job IDs, integer
amounts in the signed 32-bit range, and acknowledgement-loss schedules. Every
retry retains its original amount; changed amounts and malformed inputs are
excluded. The generator forces an acknowledgement loss followed by a healthy
retry for the same ID, varying surrounding jobs, faults, and retry counts.

The real apply_job executes against an owned temporary SQLite file per history.
The driver opens a fresh SQLite connection after every call and checks row counts
against the independent set of delivered IDs (REQ-001). For each lost ack it
checks TimeoutError and visible committed state (REQ-002). Each apply_job call
opens/closes its connection, so subsequent deliveries reopen persisted state.
This models acknowledgement loss, not OS crashes, concurrency, disk faults,
external queues, or power-loss durability.

SCN-001 requires the same job to commit, raise TimeoutError, then receive a
healthy retry. Generated counts use the planned ordered history. Observed counts
require actual timeout plus independently visible durable rows and subsequent
successful return. Checked counts additionally require both linked oracles to
execute; a failed oracle still counts as checked. Profile minimum is one history.
Counts are histories, while requirement counts are individual oracle evaluations.

Normal integration: `python3 -m unittest discover -s tests -v` runs the retained
regression plus 32 deterministic generated histories. A current product bug
therefore fails CI; expected failures are not marked xfail or swallowed.

Standalone replay: `python3 tests/retry_fuzz.py --replay fuzzing/corpus/lost-ack-retry.json`
Seed replay: `python3 tests/retry_fuzz.py --seed 20261011`
Reduction: `python3 tests/retry_fuzz.py --reduce <original.json> --output <new.json>`

Campaign: run the skill's stdlib run_campaign.py recorder using
`--repo . --plan fuzzing/targets/retry.smoke.json --run-dir <new-run-dir>`.
Native limit 25 seconds/128 histories, supervisor limit 30 seconds. Stop on the
first finding to avoid repeated shallow failures. Synthetic cases, traces, exact
selected source bytes, toolchain versions, and machine-readable counts are
retained. Databases are disposed after fresh-reader traces capture their state.
No installations, external services, or product edits are in scope.

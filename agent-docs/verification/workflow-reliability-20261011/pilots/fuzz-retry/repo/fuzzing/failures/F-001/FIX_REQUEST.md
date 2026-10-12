# Product fix request: make durable job effects idempotent

Accepted behavior is one durable effect per job_id, even when a commit succeeds
but acknowledgement is lost and the caller retries. The current unconditional
INSERT produces two rows after the two calls in lost-ack-retry.json.

Implement idempotent persistence for repeated job_id delivery while preserving
the accepted commit-then-TimeoutError boundary. This request does not choose
semantics for repeated IDs carrying different amounts; the current tests retain
the same amount across retries. Product changes were not authorized in this task.

Acceptance checks: ordinary `python3 -m unittest discover -s tests -v` passes;
original and minimized F-001 replay exit 0 with exactly one durable row; the
existing single-delivery behavior and lost-ack commit controls continue to pass.
Replay commands and retained evidence are in [FAILURE.md](FAILURE.md).

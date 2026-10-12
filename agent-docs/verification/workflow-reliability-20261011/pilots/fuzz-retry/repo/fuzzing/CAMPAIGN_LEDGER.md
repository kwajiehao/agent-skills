# Retry campaign ledger

Product: 78af9806e734d92d42a83f1aabbd000e94705fd2, unchanged store.py.
Specification: [v1](FUZZING_SPEC.md). Harness: tests/retry_fuzz.py, final v2.
Python 3.13.5; SQLite 3.50.1; stdlib only. Synthetic local data only.

| Campaign | Immutable manifest / terminal result | Wall / target seconds | Cases | Outcome |
|---|---|---|---|---|
| Initial | [manifest](runs/retry-smoke-20261011/manifest.json) / [result](runs/retry-smoke-20261011/result.json) | 0.075544 / 0.002249 | 2 | Findings; reader closure repaired afterward |
| Final v2 | [manifest](runs/retry-smoke-20261011-v2/manifest.json) / [result](runs/retry-smoke-20261011-v2/result.json) | 0.039003 / 0.002317 | 2 | Findings; no harness errors, coverage gaps, source drift, or diagnostics |

Both campaigns stopped on the first shallow finding. Combined measured recorder
wall time is 0.114547 seconds, below the assigned 30-second campaign budget.
The profile enforces 25 native seconds / 128 generated histories / 14 calls per
history with a 30-second supervisor deadline. Case rates are measured in report.json
(889.43 and 863.15 per second), based on only two histories; these are not useful
performance estimates. No code coverage was measured.

| Scenario | Generated | Observed | Checked | Requirement evaluations (final run) |
|---|---|---|---|---|
| SCN-001: same-ID commit, ack loss, healthy retry | 1 | 1 | 1 | REQ-001: 3; REQ-002: 1 |

Each run executed one valid single-delivery control and one generated history.
Normal integration additionally executed 32 seeds and one retained regression;
seven test methods ran, with 33 assertion failures and zero errors. Four harness
controls passed, also with ResourceWarning promoted to an error.

Finding [F-001](failures/F-001/FAILURE.md) is confirmed, reproducible (original 1/1,
minimized 3/3), and linked to a local product fix request. It remains fix pending,
owned by the project owner. All case databases were cleaned up; empty run database
directories and immutable synthetic traces remain.

Audit verdict: **Useful with gaps**. The accepted acknowledgement-loss retry seam
is exercised and oracles can fail. The initial corpus is deliberately small and
the campaign stopped immediately on a confirmed defect; random tests provide
broader schedules but no claim about concurrent delivery, OS crashes, power loss,
or changed amounts is made. Those are excluded from this target's accepted scope.

Next action: repair product idempotency in the separate authorized fixing workflow,
then replay original/minimized cases and run the ordinary property suite before
another bounded campaign.

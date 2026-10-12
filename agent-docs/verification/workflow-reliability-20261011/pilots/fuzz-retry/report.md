# Retry fuzz pilot result

Completed the requested replayable fuzz/property target and bounded campaign.
Confirmed product bug: acknowledgement loss after commit followed by same-job
retry creates two durable effects, violating the accepted exactly-once contract.
No store.py changes, installations, external services, or semantic approvals.

Evidence: [final machine-readable run result](repo/fuzzing/runs/retry-smoke-20261011-v2/result.json),
[failure and exact replay](repo/fuzzing/failures/F-001/FAILURE.md),
[local product fix request](repo/fuzzing/failures/F-001/FIX_REQUEST.md),
[campaign ledger](repo/fuzzing/CAMPAIGN_LEDGER.md), and
[accepted-contract specification](repo/fuzzing/FUZZING_SPEC.md).

Final run: 0.039003 seconds wall / 0.002317 seconds target, two histories;
required retry scenario generated/observed/checked 1/1/1; no harness errors,
coverage gaps or source drift. Initial plus final recorder time: 0.114547 seconds,
well within the 30-second campaign budget. Campaign stopped on the first finding.

Original replay 1/1; minimized replay 3/3; a direct target script independently
observed two rows for one job using amount 1. Four harness controls passed. The
ordinary unittest command ran seven test methods and reports 33 failures (32
generated subtests plus the regression), zero errors; these expose the unfixed
product contract violation. Existing single delivery still passes.

Audit verdict: Useful with gaps. Local SQLite acknowledgement-loss/retry behavior
is covered; concurrent delivery, process/power loss, malformed or changed amounts,
and external services are excluded. Each history uses a fresh owned database,
and all temporary SQLite directories were cleaned up after trace capture.

Exact standalone replay (expected exit 1 until product repair):

```sh
/private/tmp/agent-workflow-dev-20261011/bin/python /private/tmp/workflow-pilots-20261011.jYJEET/fuzz-retry/repo/tests/retry_fuzz.py --replay /private/tmp/workflow-pilots-20261011.jYJEET/fuzz-retry/repo/fuzzing/failures/F-001/minimized.json
```

The ai-fuzzing skill shaped the generated histories, independent durable-state
oracles, semantic counters, immutable run evidence, controls, replay/reduction,
and durable feedback. A reader connection lifecycle warning found during testing
was fixed in the harness and verified with ResourceWarning-as-error controls;
the original run evidence remains unchanged.

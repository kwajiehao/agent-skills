# F-001: duplicate durable effect after lost acknowledgement

Status: Fix pending. Classification: confirmed product bug. Severity: high for
the store's exactly-once effect contract. Owner: project owner; next action is
the local [product fix request](FIX_REQUEST.md). Product repair is outside this task.

Requirement: REQ-001 in [specification v1](../../FUZZING_SPEC.md), accepted in
README.md. Product revision: 78af9806e734d92d42a83f1aabbd000e94705fd2.
Exact product/harness source, command and final run result are retained in
[the final campaign](../../runs/retry-smoke-20261011-v2/result.json).

The first call with lose_ack=True commits one row and raises TimeoutError.
A healthy retry of the same job commits a second row. Expected count is one;
observed count is two. store.py inserts unconditionally and has neither a unique
job key nor a duplicate-delivery guard. The real SQLite result also reproduces in
a direct apply_job script that does not import the fuzz harness, using amount 1.

Exact standalone replay from any working directory (exit 1 is the detected bug):

```sh
/private/tmp/agent-workflow-dev-20261011/bin/python /private/tmp/workflow-pilots-20261011.jYJEET/fuzz-retry/repo/tests/retry_fuzz.py --replay /private/tmp/workflow-pilots-20261011.jYJEET/fuzz-retry/repo/fuzzing/failures/F-001/minimized.json
```

[Original generated case](../../runs/retry-smoke-20261011-v2/findings/F-001-original.json)
uses seed 20261011; it already has the minimum two actions. The action-deletion
reducer confirms that neither action can be removed while retaining the ordered
lost-ack/retry scenario and violation. [Minimized trace](minimized.json) retains
the complete synthetic input and durable rows. Amount simplification is represented
by the [retained regression](../../corpus/lost-ack-retry.json), using amount 1.

Reproduction: original 1/1 ([trace](original-replay.json)); minimized 3/3
([first](replay-1.json), [second](replay-2.json), [third](replay-3.json)).
Every independent execution starts with a fresh SQLite file. Each per-case
directory is cleaned up after recording the trace. No open external resources,
services, credentials, or production data were involved.

Harness validation: real apply_job is exercised; the independent fresh-connection
row-count oracle uses the accepted contract; no mock is used in campaigns or
regressions. Four empirical controls pass, including a valid commit, actual lost
ack commit, exact replay determinism, unrelated/reversed scenario rejection,
and a separately labeled audit-only seeded defect that suppresses TimeoutError.
The initial harness's reader lifecycle warning was repaired with explicit reader
closure; the final campaign and ResourceWarning-as-error controls passed.

Durable feedback: normal unittest discovery runs the deterministic 32-seed
generator and retained regression and currently fails on this product violation.
The generator forces the broader lost-ack/retry class, with surrounding deliveries,
repeated faults and valid amount boundaries across seeds. Repair must be followed
by original/minimized replay and the property suite. No specification change or
new semantic decision is required.

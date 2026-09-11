"""A small deterministic scenario runner, not a production queue fuzzer."""

import json
import os
from pathlib import Path
import random
import tempfile

from queue_target import applications, deliver, initialize, parse_count


run_dir = Path(os.environ["FUZZ_RUN_DIR"])
report = {
    "schema_version": 1, "cases": 0,
    "oracle_checks": {"REQ-ONCE": 0, "REQ-REJECTION": 0},
    "scenarios": {"SCN-RETRY": {"generated": 0, "observed": 0, "checked": 0}},
    "findings": [], "harness_errors": [],
}
randomizer = random.Random(42)
for index in range(5):
    job = f"job-{randomizer.randrange(10000)}"
    trace = [{"action": "deliver", "job": job, "lose_ack": True}]
    counts = report["scenarios"]["SCN-RETRY"]
    counts["generated"] += 1
    with tempfile.TemporaryDirectory(prefix="queue-case-", dir=run_dir) as case:
        database = Path(case) / "queue.sqlite"
        initialize(database)
        try:
            deliver(database, job, lose_ack=True)
        except TimeoutError:
            trace.append({"observed": "ack_lost", "job": job})
        committed = applications(database, job)
        trace.append({"observed": "durable_effect", "job": job, "count": committed})
        # The second call opens a new connection and retains the committed state.
        deliver(database, job)
        trace.append({"action": "retry", "job": job})
        observed = applications(database, job)
        if committed == 1:
            counts["observed"] += 1
            counts["checked"] += 1
        report["oracle_checks"]["REQ-ONCE"] += 1
        if observed != 1:
            failure = f"F-{index}"
            artifact = run_dir / f"{failure}.json"
            artifact.write_text(json.dumps({"trace": trace, "expected": 1, "observed": observed}))
            report["findings"].append({"id": failure, "artifact": artifact.name})
    report["cases"] += 1

for data in (b"", b"-1", b"12a", b"\xff"):
    try:
        parse_count(data)
    except (ValueError, UnicodeDecodeError):
        report["oracle_checks"]["REQ-REJECTION"] += 1
    else:
        report["oracle_checks"]["REQ-REJECTION"] += 1
        failure = f"P-{data.hex() or 'empty'}"
        artifact = run_dir / f"{failure}.json"
        artifact.write_text(json.dumps({"input_hex": data.hex(), "violation": "parser accepted forbidden input"}))
        report["findings"].append({"id": failure, "artifact": artifact.name})
    report["cases"] += 1

(run_dir / "report.json").write_text(json.dumps(report))

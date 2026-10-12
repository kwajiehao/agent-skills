"""Deterministic generated histories for the README's accepted retry contract."""
import argparse
from collections import Counter
from contextlib import closing
import json
import os
from pathlib import Path
import random
import sqlite3
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from store import apply_job


def generate(seed):
    rng = random.Random(seed)
    jobs = [f"job-{seed}-{i}" for i in range(rng.randint(1, 4))]
    amounts = {job: rng.choice([0, 1, -1, 2147483647, -2147483648, rng.randint(-1000, 1000)])
               for job in jobs}
    action = lambda job, lost: dict(job_id=job, amount=amounts[job], lose_ack=lost)
    # A directed ingredient makes the critical ordered scenario reachable for
    # every seed; other jobs and extra retry/fault schedules vary deterministically.
    history = [action(jobs[0], True)]
    for _ in range(rng.randint(0, 12)):
        history.append(action(rng.choice(jobs), bool(rng.getrandbits(1))))
    history.append(action(jobs[0], False))
    return {"seed": seed, "actions": history}


def execute(case, database_root=None):
    counts = Counter()
    failures = []
    trace = []
    lost_commits = set()
    scenario = False
    # Each history has an owned disposable DB. Real commits, closes, and fresh
    # readers preserve state within the history without leaking between histories.
    with tempfile.TemporaryDirectory(prefix="retry-case-", dir=database_root) as tmp:
        path = Path(tmp) / "jobs.sqlite"
        seen = set()
        for index, action in enumerate(case["actions"]):
            outcome = "returned"
            try:
                apply_job(path, **action)
            except TimeoutError:
                outcome = "timeout"
            # No unexpected exception is swallowed: those are harness/target
            # errors for triage, never successful property evaluations.
            seen.add(action["job_id"])
            with closing(sqlite3.connect(path)) as reader:
                rows = reader.execute("SELECT job_id, amount FROM effects ORDER BY rowid").fetchall()
            durable = Counter(job for job, _ in rows)
            violations = []
            for job in sorted(seen):
                counts["REQ-001"] += 1
                if durable[job] != 1:
                    violations.append({"requirement": "REQ-001", "job_id": job,
                                       "expected": 1, "actual": durable[job]})
            if action["lose_ack"]:
                counts["REQ-002"] += 1
                if outcome != "timeout" or durable[action["job_id"]] < 1:
                    violations.append({"requirement": "REQ-002", "job_id": action["job_id"],
                                       "expected": "timeout with committed effect", "actual": outcome})
                if outcome == "timeout" and durable[action["job_id"]] >= 1:
                    lost_commits.add(action["job_id"])
            elif action["job_id"] in lost_commits and outcome == "returned":
                scenario = True
            failures.extend(dict(step=index, **item) for item in violations)
            trace.append({"step": index, "action": action, "outcome": outcome,
                          "durable_rows": rows, "violations": violations})
    return {"case": case, "trace": trace, "violations": failures,
            "oracle_checks": dict(counts), "scenario_observed": scenario,
            "scenario_checked": scenario and counts["REQ-001"] > 0 and counts["REQ-002"] > 0}


def planned_scenario(case):
    lost = set()
    for action in case["actions"]:
        if action["lose_ack"]:
            lost.add(action["job_id"])
        elif action["job_id"] in lost:
            return True
    return False


def reduce_case(case, database_root=None):
    """Remove actions while retaining a real duplicate after lost ack + retry."""
    reduced = {"seed": case.get("seed"), "actions": list(case["actions"])}
    index = 0
    while index < len(reduced["actions"]):
        candidate = {**reduced, "actions": reduced["actions"][:index] + reduced["actions"][index + 1:]}
        if planned_scenario(candidate):
            result = execute(candidate, database_root)
            if result["scenario_checked"] and any(v["requirement"] == "REQ-001" for v in result["violations"]):
                reduced = candidate
                index = 0
                continue
        index += 1
    return reduced


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as output:
        json.dump(value, output, indent=2, ensure_ascii=False)
        output.write("\n")


def campaign(args):
    run_dir = Path(os.environ["FUZZ_RUN_DIR"])
    owned_databases = run_dir / "databases"
    owned_databases.mkdir()
    started = time.monotonic()
    counts = Counter()
    scenarios = {"generated": 0, "observed": 0, "checked": 0}
    cases = 0
    findings = []
    errors = []
    try:
        # Control: a single delivery reaches real persistence without a violation.
        control = execute({"actions": [{"job_id": "control", "amount": 0, "lose_ack": False}]}, owned_databases)
        if control["violations"] or control["trace"][0]["durable_rows"] != [("control", 0)]:
            raise RuntimeError("valid single-delivery control failed")
        cases += 1
        counts.update(control["oracle_checks"])
        for offset in range(args.max_cases):
            if time.monotonic() - started >= args.seconds:
                break
            case = generate(args.seed + offset)
            scenarios["generated"] += int(planned_scenario(case))
            result = execute(case, owned_databases)
            cases += 1
            counts.update(result["oracle_checks"])
            scenarios["observed"] += int(result["scenario_observed"])
            scenarios["checked"] += int(result["scenario_checked"])
            if result["violations"]:
                original = "findings/F-001-original.json"
                write_json(run_dir / original, result)
                findings.append({"id": "F-001", "artifact": original})
                # Stop on the first shallow failure; reduction/replay is separate
                # triage, so the campaign remains inside its native deadline.
                break
    except Exception as error:
        errors.append(f"{type(error).__name__}: {error}")
    elapsed = time.monotonic() - started
    report = {"schema_version": 1, "cases": cases, "oracle_checks": dict(counts),
              "scenarios": {"SCN-001": scenarios}, "findings": findings,
              "harness_errors": errors, "elapsed_seconds": elapsed,
              "cases_per_second": cases / elapsed if elapsed else 0,
              "stop_reason": "first_finding" if findings else "bounded_complete",
              "limits": {"seconds": args.seconds, "max_cases": args.max_cases, "max_actions": 14},
              "cleanup": "all per-case SQLite directories removed; empty databases directory retained"}
    write_json(run_dir / "report.json", report)
    print(json.dumps(report, sort_keys=True))
    return 3 if errors else 1 if findings else 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign", action="store_true")
    parser.add_argument("--replay", type=Path)
    parser.add_argument("--reduce", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--seed", type=int, default=20261011)
    parser.add_argument("--seconds", type=float, default=25)
    parser.add_argument("--max-cases", type=int, default=128)
    args = parser.parse_args()
    if args.campaign:
        if not 0 < args.seconds <= 25 or not 0 < args.max_cases <= 128:
            parser.error("campaign limits: 0 < seconds <= 25 and 0 < max-cases <= 128")
        return campaign(args)
    input_path = args.replay or args.reduce
    if input_path:
        value = json.loads(input_path.read_text())
        case = value.get("case", value)
    else:
        case = generate(args.seed)
    if args.reduce:
        case = reduce_case(case)
    result = execute(case)
    if args.output:
        write_json(args.output, result)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 1 if result["violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

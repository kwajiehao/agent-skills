#!/usr/bin/env python3
"""Record one bounded native fuzz command. Python 3.10+, POSIX, stdlib only.

This is an evidence recorder, not a fuzzer, sandbox, or automatic redactor.
The command writes report.json in FUZZ_RUN_DIR; see references/run-evidence.md.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time


EXIT_CODES = {
    "completed": 0, "findings": 1, "coverage_gap": 2,
    "harness_error": 3, "timed_out": 4, "interrupted": 5,
}
REPORT_LIMIT = 1024 * 1024
JSON_DEPTH_LIMIT = 64
LOG_LIMIT = 1024 * 1024


def now():
    return datetime.now(timezone.utc).isoformat()


def degraded(status):
    # Interruption and timeout already record why the evidence is incomplete.
    return status if status in ("interrupted", "timed_out") else "harness_error"


def write_new(path, value):
    # Serialize before touching disk, then publish a complete file without replacing
    # any existing record. A failed write leaves no partial final filename.
    payload = json.dumps(value, indent=2, allow_nan=False) + "\n"
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     prefix=f".{path.name}-") as output:
        output.write(payload)
        output.flush()
        os.fsync(output.fileno())
        os.link(output.name, path)


def count(value):
    return type(value) is int and value >= 0


def owned_file(root, relative):
    path = Path(relative)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError("artifact/source paths must be relative without '..'")
    cursor = root
    for part in path.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError("artifact/source paths must not traverse symlinks")
    if not cursor.is_file():
        raise ValueError(f"required file is missing: {relative}")
    return cursor


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("JSON object contains a duplicate key")
        value[key] = item
    return value


def read_json(path):
    with path.open("rb") as source:
        data = source.read(REPORT_LIMIT + 1)
    if len(data) > REPORT_LIMIT:
        raise ValueError("JSON exceeds the 1 MiB evidence limit")
    try:
        value = json.loads(data, object_pairs_hook=unique_object)
    except RecursionError as error:
        raise ValueError(f"JSON exceeds the {JSON_DEPTH_LIMIT}-level nesting limit") from error
    # Extra native metadata must be safe to embed in terminal evidence too.
    # Walk iteratively: decoder depth limits vary across supported Python versions.
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("JSON numbers must be finite")
        if isinstance(item, (dict, list)):
            depth += 1
            if depth > JSON_DEPTH_LIMIT:
                raise ValueError(f"JSON exceeds the {JSON_DEPTH_LIMIT}-level nesting limit")
            children = item.values() if isinstance(item, dict) else item
            pending.extend((child, depth) for child in children)
    return value


def validate_profile(plan, repo):
    if not isinstance(plan, dict) or type(plan.get("schema_version")) is not int or plan["schema_version"] != 1:
        raise ValueError("profile requires integer schema_version 1")
    for key in ("target", "profile"):
        if not isinstance(plan.get(key), str) or not plan[key]:
            raise ValueError(f"profile requires {key}")
    argv = plan.get("command")
    if not isinstance(argv, list) or not argv or any(
        not isinstance(arg, str) or not arg or "\0" in arg for arg in argv
    ):
        raise ValueError("command must be a nonempty argv list")
    limit = plan.get("timeout_seconds")
    try:
        valid_limit = type(limit) in (int, float) and math.isfinite(limit) and limit > 0
    except OverflowError:
        valid_limit = False
    if not valid_limit:
        raise ValueError("timeout_seconds must be finite, positive and representable as a float")
    requirements = plan.get("requirements")
    if not isinstance(requirements, list) or not requirements or any(
        not isinstance(item, str) or not item for item in requirements
    ) or len(set(requirements)) != len(requirements):
        raise ValueError("requirements must contain unique accepted requirement IDs")
    scenarios = plan.get("required_scenarios")
    if not isinstance(scenarios, dict) or any(
        not key or not count(value) or value < 1 for key, value in scenarios.items()
    ):
        raise ValueError("required_scenarios must map IDs to positive checked counts")
    for key, fields in (
        ("revisions", ("product", "harness", "specification", "dependencies", "corpus")),
        ("policy", ("authorization", "isolation", "artifact_policy", "owner")),
    ):
        values = plan.get(key)
        if not isinstance(values, dict) or any(
            not isinstance(values.get(field), str) or not values[field] for field in fields
        ):
            raise ValueError(f"profile requires complete {key} metadata")
    environment = plan.get("environment", {})
    if not isinstance(environment, dict) or any(
        not key or "=" in key or "\0" in key or not isinstance(value, str)
        or "\0" in value or key == "FUZZ_RUN_DIR"
        for key, value in environment.items()
    ):
        raise ValueError("environment must contain explicit string values; FUZZ_RUN_DIR is reserved")
    files = plan.get("source_files")
    if not isinstance(files, list) or not files or any(
        not isinstance(item, str) or not item for item in files
    ) or len(set(files)) != len(files):
        raise ValueError("source_files must list unique reviewed relative files")
    for relative in files:
        owned_file(repo, relative)


def assess_report(report, plan, run_dir):
    if not isinstance(report, dict) or type(report.get("schema_version")) is not int or report["schema_version"] != 1:
        raise ValueError("report requires integer schema_version 1")
    if not count(report.get("cases")):
        raise ValueError("report requires a nonnegative integer case count")
    checks = report.get("oracle_checks")
    scenarios = report.get("scenarios")
    findings = report.get("findings")
    errors = report.get("harness_errors")
    if not isinstance(checks, dict) or any(not count(n) for n in checks.values()):
        raise ValueError("oracle_checks must map requirement IDs to counts")
    if not isinstance(scenarios, dict):
        raise ValueError("report requires scenario counts")
    for values in scenarios.values():
        if not isinstance(values, dict) or any(
            not count(values.get(stage)) for stage in ("generated", "observed", "checked")
        ) or not 0 <= values["checked"] <= values["observed"] <= values["generated"]:
            raise ValueError("scenario counts require checked <= observed <= generated")
        if values["observed"] > report["cases"]:
            raise ValueError("scenario observed/checked histories cannot exceed executed cases")
    if not isinstance(errors, list) or any(not isinstance(item, str) for item in errors):
        raise ValueError("harness_errors must be a list of diagnostic strings")
    if not isinstance(findings, list):
        raise ValueError("findings must be a list of IDs and retained artifact paths")
    for finding in findings:
        if not isinstance(finding, dict) or not isinstance(finding.get("id"), str) or not finding["id"]:
            raise ValueError("each finding requires an ID")
        if not isinstance(finding.get("artifact"), str):
            raise ValueError("each finding requires an artifact path")
        owned_file(run_dir, finding["artifact"])
    gaps = [f"oracle:{req}" for req in plan["requirements"] if checks.get(req, 0) == 0]
    gaps += [f"scenario:{key}" for key, minimum in plan["required_scenarios"].items()
             if scenarios.get(key, {}).get("checked", 0) < minimum]
    if report["cases"] == 0:
        gaps.append("no_cases_executed")
    status = "harness_error" if errors else "findings" if findings else "coverage_gap" if gaps else "completed"
    return status, gaps


def drain_log(pipe, destination, state):
    try:
        with destination.open("xb") as output:
            retained = 0
            while chunk := pipe.read(65536):
                available = max(0, LOG_LIMIT - retained)
                output.write(chunk[:available])
                retained += min(available, len(chunk))
                state["truncated"] |= len(chunk) > available
    except OSError:
        state["error"] = "could not retain command output"
    finally:
        pipe.close()


def stop_group(process):
    # All processes started by the command must stay in this owned process group.
    errors = []
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            break
        except OSError:
            if not errors:
                errors.append("process-group cleanup denied; direct child signaled, inspect owned descendants")
            try:
                process.send_signal(sig)
            except OSError:
                errors.append(f"could not signal owned child {process.pid}")
        if sig == signal.SIGTERM:
            time.sleep(0.1)
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        errors.append(f"owned child {process.pid} remained alive after cleanup")
    return errors


def run(plan, repo, run_dir):
    validate_profile(plan, repo)
    # Explicit, reviewed inputs only: never copy the entire worktree or environment.
    run_dir.mkdir(parents=True, exist_ok=False)
    snapshot = run_dir / "source"
    hashes = {}
    for relative in plan["source_files"]:
        source = owned_file(repo, relative)
        data = source.read_bytes()
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as output:
            output.write(data)
        target.chmod(source.stat().st_mode & 0o777)
        hashes[relative] = hashlib.sha256(data).hexdigest()
    environment = {"PATH": os.environ.get("PATH", os.defpath), **plan.get("environment", {})}
    environment["FUZZ_RUN_DIR"] = str(run_dir)
    write_new(run_dir / "manifest.json", {
        "schema_version": 1, "started_at": now(), "recorder_pid": os.getpid(),
        "repo": str(repo), "profile": plan, "source_sha256": hashes,
        "environment": environment, "recorder_python": sys.version,
        "recorder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    })
    started = time.monotonic()
    status, returncode, gaps, report = "harness_error", None, [], None
    diagnostics = []
    log_state = {"truncated": False}
    process = None
    reader = None
    old_handler = signal.getsignal(signal.SIGTERM)

    def interrupted(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    try:
        process = subprocess.Popen(plan["command"], cwd=repo, env=environment,
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        write_new(run_dir / "process.json", {"pid": process.pid, "started_at": now()})
        reader = threading.Thread(target=drain_log, args=(process.stdout, run_dir / "output.log", log_state), daemon=True)
        reader.start()
        returncode = process.wait(timeout=plan["timeout_seconds"])
        status = "completed"  # Provisional until cleanup and evidence validation.
    except subprocess.TimeoutExpired:
        status = "timed_out"
    except KeyboardInterrupt:
        status = "interrupted"
    except (OSError, ValueError) as error:
        diagnostics.append(str(error))
        status = "harness_error"
    finally:
        # Prevent a second termination signal from interrupting evidence finalization.
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        old_int = signal.signal(signal.SIGINT, signal.SIG_IGN)
        if process is not None:
            cleanup_errors = stop_group(process)
            diagnostics.extend(cleanup_errors)
            if cleanup_errors:
                status = degraded(status)
            returncode = process.returncode
        if reader is not None:
            reader.join(timeout=2)
            if reader.is_alive() or "error" in log_state:
                diagnostics.append(log_state.get("error", "output stream remained open; inspect surviving descendants"))
                status = degraded(status)
        if process is not None:
            try:
                # Workers may flush findings/errors or remove case files during
                # teardown. Read the final report only after cleanup and logging.
                report = read_json(owned_file(run_dir, "report.json"))
                report_status, gaps = assess_report(report, plan, run_dir)
                if status == "completed":
                    status = report_status
                    if returncode != 0 and status not in ("findings", "harness_error"):
                        status = "harness_error"
                        diagnostics.append("command exited unsuccessfully without a recorded finding or harness error")
            except (OSError, ValueError) as error:
                diagnostics.append(str(error))
                status = degraded(status)
        signal.signal(signal.SIGINT, old_int)
        signal.signal(signal.SIGTERM, old_handler)
    changed = []
    for relative, digest in hashes.items():
        try:
            current = hashlib.sha256(owned_file(repo, relative).read_bytes()).hexdigest()
        except (OSError, ValueError):
            current = None
        if current != digest:
            changed.append(relative)
    if changed:
        diagnostics.append("selected source changed during execution; evidence requires investigation")
        status = degraded(status)
    result = {
        "schema_version": 1, "ended_at": now(), "elapsed_seconds": time.monotonic() - started,
        "status": status, "command_exit_code": returncode, "coverage_gaps": gaps,
        "source_changed": changed, "diagnostics": diagnostics,
        "log_truncated": log_state["truncated"], "report": report,
    }
    write_new(run_dir / "result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--repo", default=Path.cwd(), type=Path)
    parser.add_argument("--run-dir", required=True, type=Path)
    args = parser.parse_args()
    if os.name != "posix":
        parser.error("use a POSIX host or the project's equivalent native runner")
    try:
        result = run(read_json(args.plan), args.repo.resolve(), args.run_dir.resolve())
    except (OSError, ValueError) as error:
        print(f"campaign could not be recorded: {error}", file=sys.stderr)
        return EXIT_CODES["harness_error"]
    print(json.dumps({"run_dir": str(args.run_dir.resolve()), "status": result["status"]}))
    return EXIT_CODES[result["status"]]


if __name__ == "__main__":
    sys.exit(main())

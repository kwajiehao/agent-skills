#!/usr/bin/env python3
"""Prepare isolated cases and grade independently observed workflow trials.

This validates recorded evidence, not the truthfulness of an observer. Keep the
rubrics away from the agent performing a task and audit facts against raw traces.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
EVENTS = {"unnecessary_question", "human_correction", "false_completion",
          "scope_violation", "review_rework", "interruption", "recovered"}


class InvalidTrial(ValueError):
    pass


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)


def valid_digest(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def tree_digest(root):
    """Pin loaded skill resources, including uncommitted edits; ignore caches."""
    root = Path(root).resolve()
    files = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in {".git", "__pycache__", ".pytest_cache"} for part in rel.parts):
            continue
        if path.is_symlink():
            raise InvalidTrial(f"cannot pin symlinked resource: {rel}")
        if path.is_file():
            files.append([rel.as_posix(), digest_bytes(path.read_bytes())])
    if not files:
        raise InvalidTrial(f"no files to pin: {root}")
    return digest_bytes(canonical(files).encode())


def check_refs(refs, root):
    if not isinstance(refs, list) or not refs:
        raise InvalidTrial("every observation needs retained evidence references")
    for ref in refs:
        if not isinstance(ref, dict) or not isinstance(ref.get("path"), str):
            raise InvalidTrial("invalid evidence reference")
        rel = Path(ref["path"])
        if rel.is_absolute() or ".." in rel.parts or not rel.parts:
            raise InvalidTrial(f"evidence must stay under its root: {rel}")
        current = root
        for component in rel.parts:
            current = current / component
            if current.is_symlink():
                raise InvalidTrial(f"symlinked evidence is not accepted: {rel}")
        path = root / rel
        if not path.is_file():
            raise InvalidTrial(f"missing evidence: {rel}")
        if not valid_digest(ref.get("sha256")) or digest_bytes(path.read_bytes()) != ref["sha256"]:
            raise InvalidTrial(f"evidence digest mismatch: {rel}")


def validate_trial(trial, root):
    if not isinstance(trial, dict) or type(trial.get("schema_version")) is not int or trial["schema_version"] != 1:
        raise InvalidTrial("schema_version must be 1")
    for key in ("trial_id", "scenario_id", "arm", "match_id", "observer"):
        if not isinstance(trial.get(key), str) or not trial[key].strip():
            raise InvalidTrial(f"missing {key}")
    if trial.get("execution_kind") not in {"actual_agent", "grader_fixture"}:
        raise InvalidTrial("execution_kind must distinguish actual_agent from grader_fixture")
    if type(trial.get("repeat")) is not int or trial["repeat"] < 1:
        raise InvalidTrial("repeat must be a positive integer")
    if not valid_digest(trial.get("fixture_digest")):
        raise InvalidTrial("fixture_digest must pin the initial fixture")
    skill = trial.get("skill_identity", {})
    if not isinstance(skill, dict) or not skill.get("name") or not skill.get("revision") or not valid_digest(skill.get("digest")):
        raise InvalidTrial("skill_identity needs name, revision and digest")
    model = trial.get("model_identity", {})
    if not isinstance(model, dict) or not model.get("name") or "revision" not in model or not isinstance(model.get("configuration"), dict):
        raise InvalidTrial("model_identity needs name, revision (nullable), configuration")
    conditions = trial.get("conditions", {})
    if not isinstance(conditions, dict) or any(not conditions.get(key) for key in ("environment", "permissions", "budget")):
        raise InvalidTrial("conditions need environment, permissions and budget")
    if type(trial.get("trace_complete")) is not bool:
        raise InvalidTrial("trace_complete must be explicit")
    check_refs(trial.get("trace"), root)
    facts = trial.get("facts")
    if not isinstance(facts, dict):
        raise InvalidTrial("facts must be an independently observed mapping")
    for fact in facts.values():
        if not isinstance(fact, dict) or "value" not in fact:
            raise InvalidTrial("facts need value and evidence")
        check_refs(fact.get("evidence"), root)
    if not isinstance(trial.get("events"), list):
        raise InvalidTrial("events must be an ordered list")
    for event in trial["events"]:
        if not isinstance(event, dict) or event.get("type") not in EVENTS:
            raise InvalidTrial("unknown behavioral event")
        check_refs(event.get("evidence"), root)
    usage = trial.get("usage", {})
    for key in ("latency_seconds", "tokens"):
        if key not in usage:
            raise InvalidTrial(f"usage.{key} must be provided or null")
        value = usage[key]
        if value is not None and (type(value) not in (int, float) or value < 0 or value != value or value == float("inf")):
            raise InvalidTrial(f"invalid usage.{key}")
    if usage["tokens"] is not None and type(usage["tokens"]) is not int:
        raise InvalidTrial("tokens must be an integer or null")
    try:
        canonical(trial)
    except (TypeError, ValueError) as exc:
        raise InvalidTrial(f"non-JSON trial value: {exc}") from exc


def grade_trial(trial, rubric, evidence_root):
    root = Path(evidence_root).resolve()
    validate_trial(trial, root)
    if trial["scenario_id"] != rubric.get("scenario_id"):
        raise InvalidTrial("trial and rubric scenario differ")
    criteria = []
    for item in rubric["criteria"]:
        observation = trial["facts"].get(item["fact"])
        status = "unmeasured"
        if observation is not None:
            value = observation["value"]
            if "equals" in item:
                # Python equality treats False == 0, including inside containers.
                # Canonical JSON preserves the observation's types recursively.
                matches = canonical(value) == canonical(item["equals"])
            elif "at_least" in item:
                matches = type(value) in (int, float) and value >= item["at_least"]
            else:
                raise InvalidTrial(f"unsupported criterion: {item['id']}")
            status = "pass" if matches else "fail"
        criteria.append({"id": item["id"], "status": status})
    types = [event["type"] for event in trial["events"]]
    complete = trial["trace_complete"]
    metrics = {name: types.count(event) if complete else None for name, event in (
        ("unnecessary_questions", "unnecessary_question"), ("human_corrections", "human_correction"),
        ("false_completion_claims", "false_completion"), ("scope_violations", "scope_violation"),
        ("review_rework", "review_rework"))}
    recovery = None
    if complete and "interruption" in types:
        # Consume recoveries in order; a prior or single recovery cannot stand
        # in for multiple interrupted jobs. The observer records each job event.
        pending = 0
        for event in types:
            if event == "interruption":
                pending += 1
            elif event == "recovered" and pending:
                pending -= 1
        recovery = pending == 0
    metrics["interrupted_recovery"] = recovery
    metrics.update(trial["usage"])
    failed = any(item["status"] == "fail" for item in criteria)
    disqualifying = any(event in types for event in ("human_correction", "false_completion", "scope_violation"))
    accepted = False if failed or disqualifying else (
        True if complete and criteria and all(item["status"] == "pass" for item in criteria) else None)
    result = {key: trial[key] for key in ("trial_id", "execution_kind", "scenario_id", "arm", "repeat",
              "match_id", "fixture_digest", "skill_identity", "model_identity", "conditions")}
    result.update(criteria=criteria, accepted_without_correction=accepted, metrics=metrics)
    return result


def summarize(results):
    ids = [result["trial_id"] for result in results]
    if len(set(ids)) != len(ids):
        raise InvalidTrial("duplicate trial_id; repetitions must have distinct identities")
    actual = [result for result in results if result["execution_kind"] == "actual_agent"]
    groups = {}
    for result in actual:
        key = canonical({name: result[name] for name in ("scenario_id", "fixture_digest", "model_identity",
                         "conditions", "repeat", "match_id")})
        groups.setdefault(key, []).append(result)
    matched = []
    for group in groups.values():
        arms = [result["arm"] for result in group]
        if len(set(arms)) != len(arms):
            raise InvalidTrial("multiple trials for one arm in a matched group")
        for a, b in itertools.combinations(sorted(group, key=lambda item: item["arm"]), 2):
            differences = {}
            for name in a["metrics"]:
                av, bv = a["metrics"][name], b["metrics"][name]
                differences[name] = None if av is None or bv is None else float(bv) - float(av)
            matched.append({"scenario_id": a["scenario_id"], "match_id": a["match_id"], "repeat": a["repeat"],
                            "arms": [a["arm"], b["arm"]], "trials": [a["trial_id"], b["trial_id"]],
                            "accepted": [a["accepted_without_correction"], b["accepted_without_correction"]],
                            "metric_deltas_second_minus_first": differences})
    by_arm = {}
    for arm in sorted({result["arm"] for result in actual}):
        rows = [result for result in actual if result["arm"] == arm]
        accepted = [row["accepted_without_correction"] for row in rows if row["accepted_without_correction"] is not None]
        metrics = {}
        for name in ("unnecessary_questions", "human_corrections", "false_completion_claims", "scope_violations",
                     "review_rework", "interrupted_recovery", "latency_seconds", "tokens"):
            values = [row["metrics"][name] for row in rows if row["metrics"][name] is not None]
            metrics[name] = {"measured": len(values), "unmeasured": len(rows) - len(values),
                             "mean": sum(values) / len(values) if values else None}
        by_arm[arm] = {"trials": len(rows), "accepted_measured": len(accepted),
                       "accepted_unmeasured": len(rows) - len(accepted),
                       "accepted_without_correction_rate": sum(accepted) / len(accepted) if accepted else None,
                       "metrics": metrics}
    return {"agent_trials": len(actual), "grader_fixtures": len(results) - len(actual),
            "by_arm": by_arm, "matched_pairs": matched,
            "limitation": "Observed trials only; no confidence or significance claim. Unmatched arms are descriptive."}


def verify_archive(root, required_scenarios=(), rubrics=None):
    """Revalidate retained observations, not uncaptured interactions or agent claims."""
    root = Path(root).resolve()
    if rubrics is None:
        rubrics = {row["scenario_id"]: row for row in json.loads((HERE / "rubrics.json").read_text())}
    results = []
    for path in sorted(root.rglob("trial.json")):
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise InvalidTrial("unsafe archived trial path")
        trial = json.loads(path.read_text())
        if trial.get("execution_kind") != "actual_agent":
            raise InvalidTrial("archive verification requires actual-agent observations, not grader fixtures")
        if trial.get("scenario_id") not in rubrics:
            raise InvalidTrial("archived trial has no scenario rubric")
        result = grade_trial(trial, rubrics[trial["scenario_id"]], path.parent)
        if result["accepted_without_correction"] is False or any(row["status"] == "fail" for row in result["criteria"]):
            raise InvalidTrial(f"observed outcome failed: {trial['trial_id']}; retain it, do not claim verified success")
        if not any(row["status"] == "pass" for row in result["criteria"]):
            raise InvalidTrial("archived trial has no verified artifact criteria")
        results.append(result)
    missing = set(required_scenarios) - {row["scenario_id"] for row in results}
    if not results or missing:
        raise InvalidTrial(f"required actual-agent scenarios missing: {sorted(missing)}")
    return summarize(results)


def prepare_case(scenario_id, destination):
    scenarios = json.loads((HERE / "cases.json").read_text())
    case = next((case for case in scenarios if case["id"] == scenario_id), None)
    if case is None:
        raise InvalidTrial(f"unknown scenario: {scenario_id}")
    destination = Path(destination).resolve()
    if destination.exists():
        raise InvalidTrial("destination must not exist; use a fresh directory per trial")
    repo = destination / "repo"
    shutil.copytree(HERE / "fixtures" / case["fixture"], repo,
                    ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.pyc", ".DS_Store"))
    for path, text in case.get("baseline_overrides", {}).items():
        (repo / path).write_text(text)
    for command in (["git", "init", "-q"], ["git", "config", "user.name", "Workflow Eval"],
                    ["git", "config", "user.email", "eval@example.invalid"], ["git", "add", "."],
                    ["git", "-c", "commit.gpgsign=false", "commit", "-qm", "evaluation fixture"]):
        subprocess.run(command, cwd=repo, check=True, capture_output=True)
    for path, text in case.get("working_overrides", {}).items():
        (repo / path).write_text(text)
    prompt = case["prompt"].replace("{repo}", str(repo))
    (destination / "prompt.md").write_text(prompt + "\n")
    # Hash inputs, not random paths or Git commit timestamps.
    fixture_digest = digest_bytes(canonical({"case": case, "files_digest": tree_digest(repo)}).encode())
    manifest = {"schema_version": 1, "scenario_id": scenario_id, "fixture_digest": fixture_digest,
                "repo": str(repo), "prompt": str(destination / "prompt.md"), "skill": case["skill"],
                "initial_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()}
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("scenario")
    prepare.add_argument("destination", type=Path)
    pin = sub.add_parser("pin")
    pin.add_argument("skill", type=Path)
    grade = sub.add_parser("grade")
    grade.add_argument("trial", type=Path)
    grade.add_argument("--evidence-root", type=Path, required=True)
    summary = sub.add_parser("summarize")
    summary.add_argument("trials", type=Path, nargs="+")
    verify = sub.add_parser("verify", help="Rehash archived observations; incomplete interaction metrics remain unknown")
    verify.add_argument("archive", type=Path)
    verify.add_argument("--require-scenario", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            output = prepare_case(args.scenario, args.destination)
        elif args.command == "pin":
            output = {"digest": tree_digest(args.skill)}
        elif args.command == "verify":
            output = verify_archive(args.archive, args.require_scenario)
        else:
            rubrics = {rubric["scenario_id"]: rubric for rubric in json.loads((HERE / "rubrics.json").read_text())}
            paths = [args.trial] if args.command == "grade" else args.trials
            results = []
            for path in paths:
                trial = json.loads(path.read_text())
                root = args.evidence_root if args.command == "grade" else path.parent
                if trial.get("scenario_id") not in rubrics:
                    raise InvalidTrial("trial has no scenario rubric")
                results.append(grade_trial(trial, rubrics[trial["scenario_id"]], root))
            output = results[0] if args.command == "grade" else summarize(results)
        print(json.dumps(output, indent=2, allow_nan=False))
        return 0
    except (InvalidTrial, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"invalid evaluation: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

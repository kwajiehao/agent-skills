#!/usr/bin/env python3
"""Archive observed pilot artifacts and grade independently recorded facts.

This is a task-specific evidence builder, not an agent launcher or self-grader.
Run after pilots terminate. Configuration facts must first be checked against
the raw reports/source and assessor commands. Never infer missing measurements.
"""
import hashlib
import json
import fnmatch
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2] / "evals"))
import run_evals

EXCLUDED = {".git", "__pycache__", ".pytest_cache", ".DS_Store"}


def files(root):
    result = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in EXCLUDED for part in relative.parts) or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise ValueError(f"unexpected symlink in pilot source: {relative}")
        if path.is_file():
            result[relative.as_posix()] = path.read_bytes()
    return result


def check_scope(destination, manifest):
    case = next(row for row in json.loads((run_evals.HERE / "cases.json").read_text())
                if row["id"] == manifest["scenario_id"])
    expected = files(run_evals.HERE / "fixtures" / case["fixture"])
    for overrides in (case.get("baseline_overrides", {}), case.get("working_overrides", {})):
        expected.update({path: text.encode() for path, text in overrides.items()})
    initial_tree = run_evals.digest_bytes(run_evals.canonical([
        [path, run_evals.digest_bytes(content)] for path, content in sorted(expected.items())]).encode())
    expected_fixture = run_evals.digest_bytes(run_evals.canonical({"case": case, "files_digest": initial_tree}).encode())
    if manifest["fixture_digest"] != expected_fixture:
        raise ValueError("fixture recipe no longer matches retained initial manifest")
    actual = files(destination / "repo")
    changed = sorted(path for path in expected.keys() | actual.keys() if expected.get(path) != actual.get(path))
    scenario = case["id"]
    allowed = []
    if scenario.startswith("core-"):
        allowed = ["tests/*", "agent-docs/*", "scripts/*", "greeting.py" if scenario != "core-runtime-verifier" else "storage.py"]
    elif scenario == "fuzz-seeded-retry":
        allowed = ["tests/*", "fuzzing/*"]
    elif scenario == "walkthrough-source-integrity":
        allowed = [".walkthrough/*"]
    forbidden = [path for path in changed if not any(fnmatch.fnmatchcase(path, pattern) for pattern in allowed)]
    # Pre-existing draft is source context, not writable output.
    if scenario == "walkthrough-source-integrity":
        forbidden.extend(path for path in changed if path in expected)
    if forbidden:
        raise ValueError(f"pilot changed source outside organic request: {forbidden}")
    payload = {"scenario_id": scenario, "fixture_digest": expected_fixture,
               "changed_files": changed, "allowed": allowed, "violations": forbidden,
               "expected_file_sha256": {path: run_evals.digest_bytes(content) for path, content in expected.items()},
               "final_file_sha256": {path: run_evals.digest_bytes(content) for path, content in actual.items()},
               "boundary": "Content comparison; runtime caches excluded; no claim about uncaptured external actions"}
    (destination / "scope-check.json").write_text(json.dumps(payload, indent=2) + "\n")


def reference(root, name):
    path = root / name
    return {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    configuration = json.loads((ROOT / "pilot-observations.json").read_text())
    pilot_root = Path(configuration[0]["source"]).parent
    runner_resource = ROOT / "resources" / "frozen-core"
    if not runner_resource.exists():
        shutil.copytree(pilot_root / "core", runner_resource,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.pyc", ".DS_Store"))
    runner_digest = run_evals.tree_digest(runner_resource / "loop")
    for observation in configuration:
        expected_runner = observation["conditions"].get("runner_digest")
        if expected_runner and runner_digest != expected_runner:
            raise ValueError("retained frozen runner drifted")
    rubrics = {row["scenario_id"]: row for row in json.loads((run_evals.HERE / "rubrics.json").read_text())}
    grades = []
    for observation in configuration:
        destination = ROOT / "pilots" / observation["trial_id"]
        if destination.exists():
            raise ValueError(f"archive exists; do not overwrite retained evidence: {destination}")
        shutil.copytree(observation["source"], destination,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.pyc", ".DS_Store"))
        manifest = json.loads((destination / "manifest.json").read_text())
        check_scope(destination, manifest)
        trace = [reference(destination, name) for name in observation["trace"]]
        facts = {name: {"value": fact["value"], "evidence": [reference(destination, path) for path in fact["evidence"]]}
                 for name, fact in observation["facts"].items()}
        for name in ("product_mutations", "out_of_scope_changes", "store_source_unchanged",
                     "notes_bytes_preserved", "prior_record_preserved"):
            if name in facts:
                facts[name]["evidence"].append(reference(destination, "scope-check.json"))
        skill = observation["skill_identity"]
        if run_evals.tree_digest(observation["skill_path"]) != skill["digest"]:
            raise ValueError(f"frozen skill drifted: {observation['trial_id']}")
        resource = ROOT / "resources" / skill["digest"]
        if not resource.exists():
            shutil.copytree(observation["skill_path"], resource,
                            ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.pyc", ".DS_Store"))
        if run_evals.tree_digest(resource) != skill["digest"]:
            raise ValueError(f"retained frozen skill drifted: {observation['trial_id']}")
        skill = {**skill, "retained_path": resource.relative_to(ROOT).as_posix()}
        trial = {
            "schema_version": 1, "trial_id": observation["trial_id"],
            "execution_kind": "actual_agent", "scenario_id": manifest["scenario_id"],
            "arm": observation["arm"], "repeat": observation["repeat"], "match_id": observation["match_id"],
            "fixture_digest": manifest["fixture_digest"], "skill_identity": skill,
            "model_identity": {"name": "inherited-parent (exact model ID not exposed)", "revision": None, "configuration": {}},
            "conditions": observation["conditions"], "observer": "/root independent artifact assessment",
            "trace_complete": False, "trace": trace, "facts": facts, "events": [],
            "usage": {"latency_seconds": None, "tokens": None},
        }
        (destination / "trial.json").write_text(json.dumps(trial, indent=2) + "\n")
        grade = run_evals.grade_trial(trial, rubrics[manifest["scenario_id"]], destination)
        (destination / "grade.json").write_text(json.dumps(grade, indent=2) + "\n")
        grades.append(grade)
    (ROOT / "pilot-summary.json").write_text(json.dumps(run_evals.summarize(grades), indent=2) + "\n")
    print(f"Archived and graded {len(grades)} independent agent trials; interaction metrics remain unknown.")


if __name__ == "__main__":
    main()

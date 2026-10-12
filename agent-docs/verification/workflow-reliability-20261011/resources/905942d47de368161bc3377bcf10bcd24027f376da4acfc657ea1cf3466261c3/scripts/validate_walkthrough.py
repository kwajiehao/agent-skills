#!/usr/bin/env python3
"""Validate walkthrough structure; --repo additionally checks its Git sources."""

from __future__ import annotations

import argparse
import json
import importlib.util
import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REQUIRED_TOP_LEVEL = {"meta", "files", "code", "visuals", "steps", "findings", "coverage"}
REQUIRED_META = {
    "title",
    "intent",
    "target",
    "pr_url",
    "base_ref",
    "head_ref",
    "base_sha",
    "head_sha",
    "generated_at",
    "code_involved",
}
REQUIRED_UI_IDS = {
    "story-list",
    "step-kicker",
    "step-title",
    "step-takeaway",
    "narrative-body",
    "diagram-stage",
    "code-panel",
    "previous-step",
    "next-step",
    "play-story",
    "reset-view",
    "toggle-findings",
    "findings-panel",
    "coverage-panel",
    "story-progress",
}
SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)

    def warn(self, condition: bool, message: str) -> None:
        if not condition:
            self.warnings.append(message)


def required_keys(value: Any, keys: set[str], at: str, result: Validation) -> None:
    result.require(isinstance(value, dict), f"{at} must be an object")
    if isinstance(value, dict):
        missing = sorted(keys - value.keys())
        result.require(not missing, f"{at} missing keys: {', '.join(missing)}")


def duplicate_values(values: list[str]) -> set[str]:
    return {item for item in values if values.count(item) > 1}


def validate_data(data: Any, result: Validation) -> None:
    required_keys(data, REQUIRED_TOP_LEVEL, "root", result)
    if not isinstance(data, dict):
        return

    meta = data.get("meta", {})
    required_keys(meta, REQUIRED_META, "meta", result)
    if isinstance(meta, dict):
        result.require(bool(str(meta.get("title", "")).strip()), "meta.title must not be empty")
        result.require(bool(str(meta.get("intent", "")).strip()), "meta.intent must not be empty")
        result.require(bool(SHA_RE.fullmatch(str(meta.get("base_sha", "")))), "meta.base_sha must be a 40-character SHA")
        result.require(bool(SHA_RE.fullmatch(str(meta.get("head_sha", "")))), "meta.head_sha must be a 40-character SHA")
        result.require(isinstance(meta.get("code_involved"), bool), "meta.code_involved must be boolean")

    files = data.get("files", [])
    result.require(isinstance(files, list) and bool(files), "files must be a non-empty array")
    file_paths: list[str] = []
    valid_roles = {"story-critical", "supporting", "mechanical", "unresolved"}
    if isinstance(files, list):
        for index, item in enumerate(files):
            at = f"files[{index}]"
            required_keys(item, {"path", "status", "additions", "deletions", "role", "diff_url"}, at, result)
            if not isinstance(item, dict):
                continue
            path = str(item.get("path", ""))
            result.require(bool(path), f"{at}.path must not be empty")
            file_paths.append(path)
            result.require(item.get("role") in valid_roles, f"{at}.role is invalid")
            result.require(isinstance(item.get("additions"), int), f"{at}.additions must be an integer")
            result.require(isinstance(item.get("deletions"), int), f"{at}.deletions must be an integer")
        result.require(not duplicate_values(file_paths), "files contains duplicate paths")

    code = data.get("code", [])
    result.require(isinstance(code, list), "code must be an array")
    code_ids: list[str] = []
    if isinstance(code, list):
        for index, item in enumerate(code):
            at = f"code[{index}]"
            required_keys(
                item,
                {"id", "label", "path", "language", "side", "start_line", "end_line", "content", "emphasis", "diff_url"},
                at,
                result,
            )
            if not isinstance(item, dict):
                continue
            code_id = str(item.get("id", ""))
            code_ids.append(code_id)
            result.require(bool(code_id), f"{at}.id must not be empty")
            result.require(item.get("side") in {"old", "new", "diff", "context"}, f"{at}.side is invalid")
            start, end = item.get("start_line"), item.get("end_line")
            result.require(isinstance(start, int) and isinstance(end, int) and start > 0 and end >= start, f"{at} has an invalid line range")
            content = item.get("content")
            result.require(isinstance(content, str) and bool(content), f"{at}.content must not be empty")
            if item.get("side") != "diff" and isinstance(start, int) and isinstance(end, int) and isinstance(content, str) and content:
                actual_lines = len(content.splitlines())
                result.require(actual_lines == end - start + 1, f"{at} line range says {end - start + 1} lines but content has {actual_lines}")
            result.require(isinstance(item.get("emphasis"), list), f"{at}.emphasis must be an array")
        result.require(not duplicate_values(code_ids), "code contains duplicate ids")

    if isinstance(meta, dict) and meta.get("code_involved") is True:
        result.require(bool(code_ids), "code_involved is true but no code excerpts exist")

    visuals = data.get("visuals", [])
    result.require(isinstance(visuals, list) and bool(visuals), "visuals must be a non-empty array")
    visual_nodes: dict[str, set[str]] = {}
    if isinstance(visuals, list):
        visual_ids: list[str] = []
        for index, visual in enumerate(visuals):
            at = f"visuals[{index}]"
            required_keys(visual, {"id", "title", "mode", "caption", "nodes", "edges"}, at, result)
            if not isinstance(visual, dict):
                continue
            visual_id = str(visual.get("id", ""))
            visual_ids.append(visual_id)
            result.require(visual.get("mode") in {"2d", "3d"}, f"{at}.mode must be 2d or 3d")
            nodes = visual.get("nodes", [])
            result.require(isinstance(nodes, list) and bool(nodes), f"{at}.nodes must be non-empty")
            node_ids: list[str] = []
            nonzero_z = False
            if isinstance(nodes, list):
                for node_index, node in enumerate(nodes):
                    node_at = f"{at}.nodes[{node_index}]"
                    required_keys(node, {"id", "label", "detail", "x", "y", "z", "color"}, node_at, result)
                    if not isinstance(node, dict):
                        continue
                    node_ids.append(str(node.get("id", "")))
                    result.require(all(isinstance(node.get(axis), (int, float)) for axis in ("x", "y", "z")), f"{node_at} coordinates must be numeric")
                    nonzero_z = nonzero_z or node.get("z") != 0
                result.require(not duplicate_values(node_ids), f"{at} contains duplicate node ids")
            visual_nodes[visual_id] = set(node_ids)
            if visual.get("mode") == "3d":
                result.require(nonzero_z, f"{at} is 3d but all z coordinates are zero")
            edges = visual.get("edges", [])
            result.require(isinstance(edges, list), f"{at}.edges must be an array")
            if isinstance(edges, list):
                for edge_index, edge in enumerate(edges):
                    edge_at = f"{at}.edges[{edge_index}]"
                    required_keys(edge, {"source", "target", "label", "style"}, edge_at, result)
                    if isinstance(edge, dict):
                        result.require(edge.get("source") in visual_nodes[visual_id], f"{edge_at}.source is unknown")
                        result.require(edge.get("target") in visual_nodes[visual_id], f"{edge_at}.target is unknown")
                        result.require(edge.get("style") in {"solid", "dashed"}, f"{edge_at}.style is invalid")
        result.require(not duplicate_values(visual_ids), "visuals contains duplicate ids")

    steps = data.get("steps", [])
    result.require(isinstance(steps, list) and bool(steps), "steps must be a non-empty array")
    valid_kinds = {"intent", "architecture", "mechanism", "behavior", "proof", "risk", "coverage"}
    used_code: set[str] = set()
    if isinstance(steps, list):
        step_ids: list[str] = []
        for index, step in enumerate(steps):
            at = f"steps[{index}]"
            required_keys(
                step,
                {"id", "kind", "kicker", "title", "takeaway", "narrative", "visual_id", "focus_node_ids", "code_ids", "evidence"},
                at,
                result,
            )
            if not isinstance(step, dict):
                continue
            step_ids.append(str(step.get("id", "")))
            result.require(step.get("kind") in valid_kinds, f"{at}.kind is invalid")
            result.require(isinstance(step.get("narrative"), list) and bool(step.get("narrative")), f"{at}.narrative must be non-empty")
            visual_id = str(step.get("visual_id", ""))
            result.require(visual_id in visual_nodes, f"{at}.visual_id is unknown")
            focus = step.get("focus_node_ids", [])
            result.require(isinstance(focus, list), f"{at}.focus_node_ids must be an array")
            if isinstance(focus, list) and visual_id in visual_nodes:
                unknown = set(map(str, focus)) - visual_nodes[visual_id]
                result.require(not unknown, f"{at} focuses unknown nodes: {', '.join(sorted(unknown))}")
            refs = step.get("code_ids", [])
            result.require(isinstance(refs, list), f"{at}.code_ids must be an array")
            if isinstance(refs, list):
                unknown = set(map(str, refs)) - set(code_ids)
                used_code.update(map(str, refs))
                result.require(not unknown, f"{at} references unknown code: {', '.join(sorted(unknown))}")
            result.require(isinstance(step.get("evidence"), list), f"{at}.evidence must be an array")
        result.require(not duplicate_values(step_ids), "steps contains duplicate ids")
    result.require(not (set(code_ids) - used_code), f"orphaned code excerpts: {', '.join(sorted(set(code_ids) - used_code))}")

    findings = data.get("findings", [])
    result.require(isinstance(findings, list), "findings must be an array")
    if isinstance(findings, list):
        for index, finding in enumerate(findings):
            at = f"findings[{index}]"
            required_keys(finding, {"severity", "confidence", "title", "trigger", "impact", "evidence", "resolution", "url"}, at, result)
            if isinstance(finding, dict):
                result.require(finding.get("severity") in {"blocking", "important", "optional"}, f"{at}.severity is invalid")
                result.require(finding.get("confidence") in {"high", "medium", "low"}, f"{at}.confidence is invalid")

    coverage = data.get("coverage", {})
    required_keys(coverage, {"represented", "deemphasized", "unresolved", "evidence_gaps"}, "coverage", result)
    if isinstance(coverage, dict):
        represented = coverage.get("represented", [])
        unresolved = coverage.get("unresolved", [])
        deemphasized = coverage.get("deemphasized", [])
        result.require(isinstance(represented, list), "coverage.represented must be an array")
        result.require(isinstance(unresolved, list), "coverage.unresolved must be an array")
        result.require(isinstance(deemphasized, list), "coverage.deemphasized must be an array")
        result.require(isinstance(coverage.get("evidence_gaps"), list), "coverage.evidence_gaps must be an array")
        classified: list[str] = []
        if isinstance(represented, list):
            classified.extend(map(str, represented))
        if isinstance(unresolved, list):
            classified.extend(map(str, unresolved))
        if isinstance(deemphasized, list):
            for index, item in enumerate(deemphasized):
                required_keys(item, {"path", "reason"}, f"coverage.deemphasized[{index}]", result)
                if isinstance(item, dict):
                    classified.append(str(item.get("path", "")))
        result.require(not duplicate_values(classified), "a file is classified more than once in coverage")
        result.require(set(classified) == set(file_paths), "coverage must classify every changed file exactly once")
        result.warn(not unresolved, "coverage contains unresolved files")


def extract_data(document: str, result: Validation) -> Any:
    match = re.search(
        r'<script[^>]*id=["\']walkthrough-data["\'][^>]*>(.*?)</script>',
        document,
        flags=re.DOTALL | re.IGNORECASE,
    )
    result.require(match is not None, "missing inline walkthrough-data script")
    if match is None:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as error:
        result.errors.append(f"walkthrough-data is not valid JSON: {error}")
        return None


def validate_html(document: str, result: Validation) -> None:
    for ui_id in sorted(REQUIRED_UI_IDS):
        result.require(bool(re.search(rf'id=["\']{re.escape(ui_id)}["\']', document)), f"missing UI id: {ui_id}")
    result.require("__WALKTHROUGH_DATA__" not in document, "data template token was not replaced")
    result.require("__WALKTHROUGH_TITLE__" not in document, "title template token was not replaced")
    result.require("prefers-reduced-motion" in document, "missing reduced-motion support")
    result.require(not re.search(r'<script[^>]+src=["\']https?://', document, re.IGNORECASE), "external script runtime found")
    result.require(not re.search(r'<link[^>]+href=["\']https?://', document, re.IGNORECASE), "external stylesheet runtime found")
    result.require("latest" not in document.lower(), "unversioned 'latest' dependency or text found")


def validate_sources(data: Any, repo: Path, result: Validation) -> None:
    """Check authoritative source and evidence links, without mutating the repo.

    External URLs are link records, not verified contents. A source match does
    not prove that a test ran or that prose is semantically entailed by code.
    """
    if not isinstance(data, dict) or not isinstance(data.get("meta"), dict):
        result.errors.append("source validation requires meta and source_snapshot")
        return
    spec = importlib.util.spec_from_file_location("walkthrough_source_evidence", Path(__file__).with_name("source_evidence.py"))
    source = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(source)
    meta = data["meta"]
    snapshot = meta.get("source_snapshot")
    if not isinstance(snapshot, dict):
        result.errors.append("source validation requires collected meta.source_snapshot")
        return
    try:
        for side in ("base", "head"):
            result.require(source.resolve(repo, meta[f"{side}_ref"]) == meta[f"{side}_sha"], f"{side} target ref is stale")
        actual = source.collect(repo, meta["base_sha"], meta["head_sha"], snapshot["mode"], snapshot["exclude_untracked"])
        result.require(actual["meta"]["source_snapshot"] == snapshot, "source snapshot is stale or its digest/manifest is invalid")
        files = {f["path"]: f for f in actual["files"]}
        provided = {f["path"]: f for f in data.get("files", []) if isinstance(f, dict) and isinstance(f.get("path"), str)}
        result.require(set(files) == set(provided), "changed inventory differs from authoritative source snapshot")
        for path in files.keys() & provided.keys():
            result.require(all(files[path][key] == provided[path].get(key) for key in ("status", "additions", "deletions")), f"diff statistics differ for {path}")
        for index, code in enumerate(data.get("code", [])):
            if not isinstance(code, dict):
                continue
            try:
                expected = source.excerpt(repo, meta, code["path"], code["side"], code["start_line"], code["end_line"], code.get("revision"))
                result.require(code.get("content") == expected["content"], f"code[{index}] source text differs from pinned source")
            except (ValueError, KeyError, OSError, subprocess.TimeoutExpired) as error:
                result.errors.append(f"code[{index}] source verification failed: {error}")
    except (ValueError, KeyError, TypeError, OSError, subprocess.TimeoutExpired) as error:
        result.errors.append(f"source verification failed: {error}")

    code_ids = {c.get("id") for c in data.get("code", []) if isinstance(c, dict)}
    external = False
    for section in ("steps", "findings"):
        for index, item in enumerate(data.get(section, [])):
            if not isinstance(item, dict):
                continue
            at = f"{section}[{index}]"
            status = item.get("claim_status")
            result.require(status in {"stated", "demonstrated", "inferred", "disputed", "unknown"}, f"{at}.claim_status is required for source verification")
            evidence = item.get("evidence")
            result.require(isinstance(evidence, list), f"{at}.evidence must be typed evidence records for source verification")
            if status in {"stated", "demonstrated", "disputed"}:
                result.require(isinstance(evidence, list) and bool(evidence), f"{at} {status} claim needs evidence")
            elif status in {"inferred", "unknown"} and not evidence:
                result.require(isinstance(item.get("evidence_gap"), str) and bool(item["evidence_gap"].strip()), f"{at} needs an explicit evidence_gap")
            if not isinstance(evidence, list):
                continue
            for i, entry in enumerate(evidence):
                here = f"{at}.evidence[{i}]"
                if not isinstance(entry, dict):
                    result.errors.append(f"{here} must be an evidence object")
                    continue
                result.require(isinstance(entry.get("label"), str) and bool(entry["label"].strip()), f"{here} requires a label")
                has_code, has_url = "code_id" in entry, "url" in entry
                result.require(has_code != has_url, f"{here} must identify exactly one code_id or external url")
                if has_code:
                    result.require(entry["code_id"] in code_ids, f"{here} references unknown code evidence")
                if has_url:
                    parsed = urlparse(str(entry["url"]))
                    result.require(parsed.scheme in {"https", "http"} and bool(parsed.netloc), f"{here} must use an absolute HTTP(S) evidence URL")
                    result.require(entry.get("source_kind") in {"spec", "issue", "pr", "comment", "check", "benchmark", "manual"}, f"{here} external evidence requires source_kind")
                    external = True
    if external:
        result.warnings.append("external evidence URLs were linked, not fetched or verified; inspect their contents and execution claims separately")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, required=True, help="rendered walkthrough HTML")
    parser.add_argument("--repo", type=Path, help="source repository root; required to verify exact excerpts, inventory, and freshness")
    args = parser.parse_args()

    document = args.html.read_text(encoding="utf-8")
    result = Validation()
    validate_html(document, result)
    data = extract_data(document, result)
    if data is not None:
        validate_data(data, result)
        if args.repo:
            validate_sources(data, args.repo, result)
        else:
            result.warnings.append("STRUCTURE ONLY: source text, changed inventory, evidence links, and freshness were not verified; pass --repo")

    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}")
    if result.errors:
        print(f"Validation failed: {len(result.errors)} error(s), {len(result.warnings)} warning(s)")
        return 1
    level = "Source and structure" if args.repo else "Structure only"
    print(f"{level} validation passed: {args.html.resolve()} ({len(result.warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

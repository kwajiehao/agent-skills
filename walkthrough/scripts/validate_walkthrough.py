#!/usr/bin/env python3
"""Validate a rendered PR walkthrough's data and static UI contract."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, required=True, help="rendered walkthrough HTML")
    args = parser.parse_args()

    document = args.html.read_text(encoding="utf-8")
    result = Validation()
    validate_html(document, result)
    data = extract_data(document, result)
    if data is not None:
        validate_data(data, result)

    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}")
    if result.errors:
        print(f"Validation failed: {len(result.errors)} error(s), {len(result.warnings)} warning(s)")
        return 1
    print(f"Validation passed: {args.html.resolve()} ({len(result.warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

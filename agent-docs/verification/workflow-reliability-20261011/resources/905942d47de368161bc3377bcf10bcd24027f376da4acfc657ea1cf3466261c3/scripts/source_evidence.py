#!/usr/bin/env python3
"""Collect a read-only Git change snapshot and extract exact source evidence.

No checkout, index write, hash-object -w, or temporary file in the source repo.
Snapshots are commitments to observed source, not a signature or semantic proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
from pathlib import Path, PurePosixPath


SHA = re.compile(r"[0-9a-f]{40}")
MAX_TEXT_BYTES = 16 * 1024 * 1024


def git(repo: Path, *args: str) -> bytes:
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    run = subprocess.run(["git", "-C", str(repo), *args], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, timeout=30, env=env)
    if run.returncode:
        raise ValueError(f"Git inspection failed: {run.stderr.decode('utf-8', 'replace').strip()}")
    return run.stdout


def repository(path: Path) -> Path:
    root = Path(git(path, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if path.resolve() != root:
        raise ValueError("--repo must be the Git repository root")
    if git(root, "rev-parse", "--show-object-format").strip() != b"sha1":
        raise ValueError("walkthrough currently requires a SHA-1 Git repository")
    return root


def resolve(repo: Path, ref: str) -> str:
    # --end-of-options prevents an input ref from becoming a Git option.
    oid = git(repo, "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}").decode().strip()
    if not SHA.fullmatch(oid):
        raise ValueError("revision must resolve to an immutable commit")
    return oid


def safe_path(path: str) -> str:
    if not isinstance(path, str) or not path or "\x00" in path or "\\" in path:
        raise ValueError(f"unsafe source path: {path!r}")
    parts = PurePosixPath(path).parts
    if PurePosixPath(path).is_absolute() or any(p in {"..", ".git"} for p in parts) or str(PurePosixPath(path)) != path:
        raise ValueError(f"unsafe source path: {path!r}")
    return path


def tree(repo: Path, revision: str) -> dict:
    entries = {}
    for record in git(repo, "ls-tree", "-r", "-z", revision).split(b"\0"):
        if record:
            header, raw_path = record.split(b"\t", 1)
            mode, kind, oid = header.decode().split()
            path = safe_path(raw_path.decode("utf-8"))
            entries[path] = {"mode": mode, "oid": oid, "kind": kind}
    return entries


def index_tree(repo: Path) -> dict:
    entries = {}
    for record in git(repo, "ls-files", "--stage", "-z").split(b"\0"):
        if record:
            header, raw_path = record.split(b"\t", 1)
            mode, oid, stage = header.decode().split()
            if stage != "0":
                raise ValueError("unmerged index: resolve conflicts before collecting a walkthrough")
            path = safe_path(raw_path.decode("utf-8"))
            entries[path] = {"mode": mode, "oid": oid, "kind": "commit" if mode == "160000" else "blob"}
    return entries


def working_path(repo: Path, path: str) -> Path:
    safe_path(path)
    candidate = repo / path
    # Reject symlink parents before opening files; a final symlink is recorded
    # as link text, never dereferenced.
    for parent in candidate.parents:
        if parent == repo:
            break
        if parent.is_symlink():
            raise ValueError(f"unsafe source path through symlink: {path}")
    return candidate


def working_entry(repo: Path, path: str) -> dict | None:
    candidate = working_path(repo, path)
    try:
        info = candidate.lstat()
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(info.st_mode):
        content = os.fsencode(os.readlink(candidate))
        mode = "120000"
        digest = hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
    elif stat.S_ISREG(info.st_mode):
        mode = "100755" if info.st_mode & stat.S_IXUSR else "100644"
        digest_obj = hashlib.sha1(f"blob {info.st_size}\0".encode())
        with candidate.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest_obj.update(chunk)
        if candidate.stat().st_mtime_ns != info.st_mtime_ns or candidate.stat().st_size != info.st_size:
            raise ValueError(f"source changed during collection: {path}")
        digest = digest_obj.hexdigest()
    else:
        raise ValueError(f"unsupported working source type: {path}")
    return {"mode": mode, "oid": digest, "kind": "blob"}


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def endpoints(repo: Path, base: str, head: str, mode: str, excludes: list[str]) -> tuple[dict, dict, dict]:
    before = tree(repo, base)
    committed = tree(repo, head)
    manifest = {"version": 1, "mode": mode, "base_sha": base, "head_sha": head,
                "exclude_untracked": excludes, "base_tree_digest": digest(before)}
    if mode == "committed":
        after = committed
    else:
        if resolve(repo, "HEAD") != head:
            raise ValueError("local source snapshot is stale: HEAD differs")
        index = index_tree(repo)
        manifest["index_digest"] = digest(index)
        if mode == "staged":
            after = index
        else:
            paths = set(committed) | set(index)
            for raw_path in git(repo, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0"):
                if raw_path:
                    path = safe_path(raw_path.decode("utf-8"))
                    if not any(path == p or path.startswith(p + "/") for p in excludes):
                        paths.add(path)
            after = {}
            for path in sorted(paths):
                entry = index.get(path, committed.get(path))
                if entry and entry["kind"] == "commit":
                    # A submodule's checked-out commit is evidence; its dirty
                    # internal tree requires its own walkthrough, never hide it.
                    candidate = working_path(repo, path)
                    if candidate.is_dir():
                        if git(candidate, "status", "--porcelain").strip():
                            raise ValueError(f"dirty submodule needs separate source evidence: {path}")
                        entry = dict(entry, oid=resolve(candidate, "HEAD"))
                        after[path] = entry
                    continue
                item = working_entry(repo, path)
                if item:
                    after[path] = item
    manifest["target_tree_digest"] = digest(after)
    return before, after, manifest


def blob(repo: Path, entries: dict, path: str, working: bool = False) -> bytes:
    safe_path(path)
    entry = entries.get(path)
    if entry is None:
        return b""
    if entry["kind"] != "blob":
        return ("Subproject commit " + entry["oid"] + "\n").encode()
    if working:
        candidate = working_path(repo, path)
        if entry["mode"] == "120000":
            return os.fsencode(os.readlink(candidate))
        if candidate.stat().st_size > MAX_TEXT_BYTES:
            raise ValueError(f"source exceeds {MAX_TEXT_BYTES} byte text limit: {path}")
        return candidate.read_bytes()
    size = int(git(repo, "cat-file", "-s", entry["oid"]))
    if size > MAX_TEXT_BYTES:
        raise ValueError(f"source exceeds {MAX_TEXT_BYTES} byte text limit: {path}")
    return git(repo, "cat-file", "blob", entry["oid"])


def changed(repo: Path, before: dict, after: dict, mode: str) -> tuple[list, dict]:
    files, diffs = [], {}
    for path in sorted(set(before) | set(after)):
        if before.get(path) == after.get(path):
            continue
        old = blob(repo, before, path)
        new = blob(repo, after, path, working=mode == "working")
        # Ask Git's diff engine to compare observed bytes in an isolated
        # directory. This preserves newline evidence and Git's line matching,
        # without repository textconv, external diff, or clean-filter execution.
        with tempfile.TemporaryDirectory(prefix="walkthrough-diff-") as temp:
            folder = Path(temp)
            (folder / "old").write_bytes(old)
            (folder / "new").write_bytes(new)
            run = subprocess.run(["git", "-C", temp, "-c", "core.attributesFile=/dev/null", "diff",
                                  "--no-index", "--no-ext-diff", "--no-textconv", "--no-color", "--no-renames",
                                  "--diff-algorithm=myers", "--unified=3", "--", "old", "new"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            if run.returncode not in {0, 1}:
                raise ValueError(f"Git diff failed: {run.stderr.decode('utf-8', 'replace')}")
        try:
            raw_lines = run.stdout.decode("utf-8").splitlines()
        except UnicodeDecodeError:
            raw_lines = []
        binary = any(line.startswith("Binary files ") for line in raw_lines) or (bool(run.stdout) and not raw_lines)
        header = next((i for i, line in enumerate(raw_lines) if line.startswith("--- ")), None)
        lines = raw_lines[header:] if header is not None else []
        if lines:
            lines[0], lines[1] = "--- a/" + path, "+++ b/" + path
        additions = sum(line.startswith("+") for line in lines[2:])
        deletions = sum(line.startswith("-") for line in lines[2:])
        files.append({"path": path, "status": "added" if path not in before else "deleted" if path not in after else "modified",
                      "additions": additions, "deletions": deletions, "binary": binary})
        diffs[path] = lines
    return files, diffs


def collect(repo: Path, base: str, head: str = "HEAD", mode: str = "committed", exclude_untracked: list[str] | None = None) -> dict:
    repo = repository(repo)
    if mode not in {"committed", "staged", "working"}:
        raise ValueError("source mode must be committed, staged, or working")
    excludes = sorted(set(exclude_untracked if exclude_untracked is not None else [".walkthrough"]))
    for path in excludes:
        safe_path(path)
    base_ref, head_ref = base, head
    base, head = resolve(repo, base), resolve(repo, head)
    before, after, manifest = endpoints(repo, base, head, mode, excludes)
    files, _ = changed(repo, before, after, mode)
    # Catch a concurrent index/tree write rather than combine observations.
    _, _, check = endpoints(repo, base, head, mode, excludes)
    if check != manifest:
        raise ValueError("source changed during collection; retry after it stabilizes")
    return {"meta": {"base_ref": base_ref, "head_ref": head_ref, "base_sha": base, "head_sha": head,
                     "source_snapshot": dict(manifest, digest=digest(manifest))}, "files": files}


def excerpt(repo: Path, meta: dict, path: str, side: str, start: int, end: int, revision: str | None = None) -> dict:
    repo = repository(repo)
    safe_path(path)
    snapshot = meta["source_snapshot"]
    before, after, manifest = endpoints(repo, meta["base_sha"], meta["head_sha"], snapshot["mode"], snapshot["exclude_untracked"])
    if dict(manifest, digest=digest(manifest)) != snapshot:
        raise ValueError("source snapshot is stale")
    if side == "context":
        if revision not in {meta["base_sha"], meta["head_sha"]}:
            raise ValueError("context revision must be an immutable endpoint SHA")
        entries = tree(repo, revision)
        working = False
    else:
        entries = before if side == "old" else after
        working = side == "new" and snapshot["mode"] == "working"
    if side not in {"old", "new", "context", "diff"}:
        raise ValueError("unsupported excerpt side")
    if side == "diff":
        _, diffs = changed(repo, before, after, snapshot["mode"])
        if path not in diffs:
            raise ValueError(f"diff excerpt does not refer to a changed path: {path}")
        lines = diffs[path]
    else:
        if path not in entries:
            raise ValueError(f"source path does not exist at selected endpoint: {path}")
        if entries[path]["mode"] == "120000":
            raise ValueError("symlink cannot be presented as a source excerpt")
        try:
            lines = blob(repo, entries, path, working).decode("utf-8").splitlines()
        except UnicodeDecodeError as error:
            raise ValueError("binary source cannot be presented as a text excerpt") from error
    if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start or end > len(lines):
        raise ValueError(f"excerpt line range is outside source: {path}")
    result = {"path": path, "side": side, "start_line": start, "end_line": end, "content": "\n".join(lines[start - 1:end])}
    if side == "context":
        result["revision"] = revision
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--mode", choices=["committed", "staged", "working"], default="committed")
    parser.add_argument("--exclude-untracked", action="append", help="output directories excluded from untracked source; default .walkthrough")
    parser.add_argument("--path", help="extract one excerpt instead of the snapshot")
    parser.add_argument("--side", choices=["old", "new", "diff", "context"], default="new")
    parser.add_argument("--revision", help="immutable base/head SHA for context excerpts")
    parser.add_argument("--start", type=int)
    parser.add_argument("--end", type=int)
    args = parser.parse_args()
    try:
        data = collect(args.repo, args.base, args.head, args.mode, args.exclude_untracked)
        if args.path:
            data = excerpt(args.repo, data["meta"], args.path, args.side, args.start, args.end, args.revision)
        print(json.dumps(data, indent=2))
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"Source collection failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Read-only PR digest. Writes local reports; never sends notifications."""

import argparse
from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit


PR_FIELDS = """fragment WorkStatusPR on PullRequest {
      number title url state isDraft headRefOid baseRefOid reviewDecision mergeStateStatus
      author { login }
      repository { nameWithOwner }
      commits(last:1) { nodes { commit { oid statusCheckRollup {
        contexts(first:100) { pageInfo { hasNextPage } nodes {
          ... on CheckRun { name status conclusion detailsUrl }
          ... on StatusContext { context state targetUrl }
        } }
      } } } }
      reviewThreads(first:100) { pageInfo { hasNextPage } nodes {
        id isResolved isOutdated path line
        comments(first:1) { nodes { url author { login } } }
      } }
}"""

PR_QUERY = """query($q:String!, $after:String) {
  search(query:$q, type:ISSUE, first:50, after:$after) {
    issueCount pageInfo { hasNextPage endCursor }
    nodes { ...WorkStatusPR }
  }
}""" + PR_FIELDS

NAMED_PR_QUERY = """query($owner:String!, $name:String!, $number:Int!) {
  repository(owner:$owner, name:$name) {
    pullRequest(number:$number) { ...WorkStatusPR }
  }
}""" + PR_FIELDS


def now():
    return datetime.now(timezone.utc).isoformat()


def run(argv, *, cwd=None, timeout=90):
    """One bounded attempt. Access failures do not trigger repeated login attempts."""
    command = Path(str(argv[0])).name
    try:
        result = subprocess.run([str(x) for x in argv], cwd=cwd, text=True,
                                capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"{command}: exceeded {timeout}s") from exc
    if result.returncode:
        # Return useful sanitized diagnostics without printing arbitrary tool output.
        detail = result.stderr.lower()
        reason = ("authentication required" if any(s in detail for s in ("authentication failed", "please run:  gh auth login")) else
                  "network/access failure" if any(s in detail for s in ("connect", "resolve", "permission denied", "operation not permitted")) else
                  f"command exited {result.returncode}")
        raise RuntimeError(f"{command}: {reason}")
    return result.stdout


def checked_json(raw):
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("errors") or data.get("error"):
        raise ValueError("collector returned an error or invalid JSON object")
    return data


def summarize_pr(pr):
    commits = pr.get("commits", {}).get("nodes", [])
    commit = commits[-1]["commit"] if commits else {}
    rollup = commit.get("statusCheckRollup") or {}
    connection = rollup.get("contexts", {})
    checks = []
    for node in connection.get("nodes", []):
        if "context" in node:
            state = {"SUCCESS": "pass", "FAILURE": "fail", "ERROR": "fail", "PENDING": "pending"}.get(node["state"], "unknown")
        elif node["status"] != "COMPLETED":
            state = "pending"
        else:
            state = ("pass" if node.get("conclusion") in ("SUCCESS", "NEUTRAL", "SKIPPED") else
                     "fail" if node.get("conclusion") in ("FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STALE", "STARTUP_FAILURE") else "unknown")
        checks.append({"name": node.get("name", node.get("context")), "state": state,
                       "conclusion": node.get("conclusion", node.get("state")),
                       "url": node.get("detailsUrl", node.get("targetUrl"))})
    threads = pr.get("reviewThreads", {})
    discussions = []
    for thread in threads.get("nodes", []):
        first = next(iter(thread["comments"]["nodes"]), {})
        discussions.append({"id": thread.get("id"), "resolved": thread["isResolved"],
                            "path": thread["path"], "line": thread["line"],
                            "outdated": thread["isOutdated"], "url": first.get("url"),
                            "author": (first.get("author") or {}).get("login")})
    unresolved = [thread for thread in discussions if not thread["resolved"]]
    complete = not connection.get("pageInfo", {}).get("hasNextPage", False) and not threads.get("pageInfo", {}).get("hasNextPage", False)
    head_matches = commit.get("oid") == pr["headRefOid"]
    # Empty checks is 'none reported', never a claim that required CI passed.
    ci = ("unknown" if not head_matches else "fail" if any(c["state"] == "fail" for c in checks) else
          "incomplete" if not complete else "pending" if any(c["state"] == "pending" for c in checks) else
          "unknown" if any(c["state"] == "unknown" for c in checks) else "pass" if checks else "none reported")
    pr_state = pr.get("state", "OPEN")
    action = (f"PR is {pr_state.lower()}; check retained findings separately if needed." if pr_state in ("CLOSED", "MERGED") else
              "Inspect failed checks on this head." if ci == "fail" else
              "Refresh incomplete or missing evidence." if not complete or not head_matches or ci == "unknown" else
              "Read and address unresolved review discussions." if unresolved else
              "Wait for checks on this head." if ci == "pending" else
              "Address requested review changes." if pr.get("reviewDecision") == "CHANGES_REQUESTED" else
              "Decide when the draft is ready to request review." if pr["isDraft"] else
              "Human merge decision; confirm required policies and review evidence." if pr.get("reviewDecision") == "APPROVED" else
              "Reviewer decision needed; confirm required checks before proceeding.")
    return {"repository": pr["repository"]["nameWithOwner"], "number": pr["number"],
            "title": pr["title"], "url": pr["url"], "draft": pr["isDraft"], "state": pr_state,
            "author": (pr.get("author") or {}).get("login"),
            "head": pr["headRefOid"], "base": pr["baseRefOid"],
            "review_decision": pr.get("reviewDecision"), "merge_state": pr.get("mergeStateStatus"),
            "ci": ci, "checks": checks, "unresolved_threads": unresolved,
            "review_threads": discussions, "next_action": action,
            "code_fix_status": "unverified by this collector",
            "complete": complete and head_matches,
            "coverage_note": ("First 100 checks/threads; connection truncated." if not complete else
                              "Head changed or unavailable; recollect before relying on checks." if not head_matches else
                              "Current head status and review threads; no code review or merge-policy evaluation.")}


def ledger_evidence(pr, ledger_path=None):
    path = (Path(ledger_path).expanduser().resolve() if ledger_path else
            Path.home() / ".agents/reviews" / pr["repository"].replace("/", "-") / f'pr-{pr["number"]}.md')
    try:
        with path.open() as stream:
            header = stream.read(8192)
    except FileNotFoundError:
        if ledger_path:
            raise ValueError("Explicit review ledger was not found")
        return {"state": "not found in shared ledger directory"}
    except OSError:
        if ledger_path:
            raise ValueError("Explicit review ledger could not be read")
        return {"state": "shared ledger unreadable"}
    if ledger_path:
        identity = re.search(r"(?im)^PR:[ \t]*[^\n]*?https://github\.com/([^/\s]+)/([^/\s]+)/pull/(\d+)(?!\d)", header)
        if not identity or (f"{identity[1]}/{identity[2]}".lower(), int(identity[3])) != (pr["repository"].lower(), pr["number"]):
            raise ValueError("Explicit ledger must identify the requested PR in its PR: field")
    match = re.search(r"(?im)^(?:Current reviewed head|Reviewed head|Head):\s*`?([0-9a-f]{7,40})\b", header)
    if not match:
        match = re.search(r"(?im)^Base\s*/\s*head:.* /\s*`?([0-9a-f]{7,40})\b", header)
    head = match.group(1) if match else None
    base_match = re.search(r"(?im)^(?:Base|Base\s*/\s*head):\s*`?([0-9a-f]{7,40})\b", header)
    base = base_match.group(1) if base_match else None
    def relation(reviewed, current):
        if not reviewed:
            return "unknown"
        if reviewed == current:
            return "unchanged"
        return "prefix matches" if current.startswith(reviewed) else "changed"
    head_relation, base_relation = relation(head, pr["head"]), relation(base, pr["base"])
    next_check = ("Compare the reviewed and current revisions; recheck findings affected by changed code, callers or dependencies."
                  if "changed" in (head_relation, base_relation) else
                  "Read the ledger and its follow-ups; reuse prior evidence only where its code and environment still apply."
                  if head_relation == "unchanged" else
                  "Establish the exact reviewed revision from the ledger before reusing evidence.")
    return {"path": str(path), "header_head": head,
            "state": "header mentions current head" if head and pr["head"].startswith(head) else
                     "header head differs" if head else "header head unrecognized",
            "reviewed_base": base, "head_comparison": head_relation, "base_comparison": base_relation,
            "next_check": next_check,
            "scope": "Explicit header comparison only; read findings and appended follow-ups in the ledger. Discussion resolution and commit identity do not establish a code fix."}


def parse_pr_target(value):
    if value.startswith("https://"):
        url = urlsplit(value)
        match = re.fullmatch(r"/([^/]+)/([^/]+)/pull/(\d+)(?:/(?:files|commits|checks))?/?", url.path)
        if url.netloc != "github.com" or not match:
            raise ValueError("--pr requires a github.com PR URL or OWNER/REPO#NUMBER")
        owner, name, number = match.groups()
    else:
        match = re.fullmatch(r"([^/#]+)/([^/#]+)#(\d+)", value)
        if not match:
            raise ValueError("--pr requires a github.com PR URL or OWNER/REPO#NUMBER")
        owner, name, number = match.groups()
    if (any(not re.fullmatch(r"[A-Za-z0-9_.-]+", part) or part in (".", "..") for part in (owner, name))
            or not 0 < int(number) < 2**31):
        raise ValueError("Invalid PR repository or number")
    return owner, name, int(number)


def pr_status(config, target=None, ledger_path=None):
    if target:
        owner, name, number = parse_pr_target(target)
        response = checked_json(run(["gh", "api", "graphql", "--hostname", "github.com",
            "-f", f"query={NAMED_PR_QUERY}", "-f", f"owner={owner}", "-f", f"name={name}", "-F", f"number={number}"]))
        node = (response["data"].get("repository") or {}).get("pullRequest")
        if not node:
            raise ValueError("Requested PR was not found or is unavailable to this GitHub account")
        item = summarize_pr(node)
        if (item["repository"].lower(), item["number"]) != (f"{owner}/{name}".lower(), number):
            raise ValueError("GitHub response did not match the requested PR")
        item["ledger"] = ledger_evidence(item, ledger_path)
        return {"observed_at": now(), "state": "observed" if item["complete"] else "incomplete",
                "complete": item["complete"], "reported_count": 1, "prs": [item], "target": target,
                "scope": "Named PR facts, including resolved discussions and closed/merged PRs; code-fix verification requires reading the current code and review ledger."}
    author = config.get("author") or run(["gh", "api", "user", "--jq", ".login"]).strip()
    if not re.fullmatch(r"[A-Za-z0-9-]+", author):
        raise ValueError("invalid GitHub author")
    query = f"is:pr is:open author:{author} sort:updated-desc"
    cursor, items, total, complete = None, [], None, False
    for _ in range(20):
        argv = ["gh", "api", "graphql", "-f", f"query={PR_QUERY}", "-f", f"q={query}"]
        if cursor:
            argv += ["-f", f"after={cursor}"]
        page = checked_json(run(argv))["data"]["search"]
        total = page["issueCount"]
        items.extend(summarize_pr(pr) for pr in page["nodes"] if pr)
        if not page["pageInfo"]["hasNextPage"]:
            complete = True
            break
        cursor = page["pageInfo"]["endCursor"]
    unique = {item["url"]: item for item in items}
    items = list(unique.values())
    for item in items:
        item["ledger"] = ledger_evidence(item)
    complete = complete and len(items) == total and all(item["complete"] for item in items)
    return {"observed_at": now(), "author": author, "query": query,
            "state": "observed" if complete else "incomplete", "complete": complete,
            "reported_count": total, "prs": items,
            "scope": "Authored open PRs visible to this gh account; required-check rules and code correctness are not evaluated."}


def refresh_history(config, out):
    atlas = Path(config.get("atlas_root", "~/Documents/session-atlas")).expanduser().resolve()
    archive = atlas / Path(config.get("atlas_archive", "archive")).expanduser()
    lookup = Path(__file__).resolve().parents[2] / "find-work/scripts/find_work.py"
    # The installed copies live as sibling skill directories.
    command = [sys.executable, lookup, "refresh", "--atlas-root", atlas]
    if "atlas_archive" in config:
        command += ["--archive-root", archive]
    if config.get("lookup_cache"):
        command += ["--cache-dir", str(Path(config["lookup_cache"]).expanduser())]
    result = checked_json(run(command, timeout=180))
    site = Path(config.get("atlas_out", str(out / "session-atlas"))).expanduser()
    run([sys.executable, atlas / "generate_site.py", "--all", "--out", site, "--archive", archive], cwd=atlas, timeout=300)
    return {"observed_at": now(), "state": "refreshed", "lookup": result["coverage"], "atlas": str(site / "index.html")}


def collect(config, refresh=False, out=Path("."), target=None, ledger_path=None):
    result = {"schema": 1, "observed_at": now(), "collectors": {}}
    jobs = [("prs", lambda c: pr_status(c, target, ledger_path))]
    if refresh:
        jobs.append(("history", lambda c: refresh_history(c, out)))
    for name, action in jobs:
        try:
            result["collectors"][name] = action(config)
        except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.TimeoutExpired) as exc:
            detail = (f"collector exceeded {exc.timeout}s" if isinstance(exc, subprocess.TimeoutExpired) else
                      str(exc) if isinstance(exc, (RuntimeError, ValueError)) else type(exc).__name__)
            result["collectors"][name] = {"observed_at": now(), "state": "unknown", "error": detail}
    result["finished_at"] = now()
    return result


def atomic_write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".work-status-")
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(value)
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def render(report):
    def e(value):
        return html.escape(str(value if value is not None else "unknown"), quote=True)

    def tag(state):
        return f'<span class="state {e(state)}">{e(state)}</span>'

    sections = []
    for name, data in report["collectors"].items():
        body = f'<p>{tag(data["state"])} · observed {e(data.get("observed_at"))}</p>'
        if data.get("error"):
            body += f'<p class="error">Collection failed: {e(data["error"])}. Current status is unknown; no prior healthy state was reused.</p>'
        elif name == "prs":
            label = "requested PR" if data.get("target") else "authored open PRs"
            body += f'<p>{len(data["prs"])} of {e(data["reported_count"])} {label}. {e(data["scope"])}</p>'
            for pr in data["prs"]:
                threads = pr["unresolved_threads"]
                failed = [c["name"] for c in pr["checks"] if c["state"] == "fail"]
                pr_label = "Draft" if pr["draft"] and pr["state"] == "OPEN" else pr["state"].title()
                resolved = sum(t["resolved"] for t in pr["review_threads"])
                body += f'<article><h3><a href="{e(pr["url"])}">{e(pr["repository"])} #{pr["number"]}: {e(pr["title"])}</a></h3><p>{e(pr_label)} · CI {tag(pr["ci"])} · {len(threads)} unresolved / {resolved} resolved thread(s) · review {e(pr["review_decision"] or "none reported")}</p><p>Head <code>{e(pr["head"])}</code></p><p>Code-fix status: {e(pr["code_fix_status"])}.</p>'
                if failed:
                    body += f'<p>Failed checks: {e(", ".join(failed))}</p>'
                body += f'<p>Next: {e(pr["next_action"])}</p><p class="muted">Prior review ledger: {e(pr.get("ledger", {}).get("state", "not checked"))}</p>'
                ledger = pr.get("ledger", {})
                if ledger.get("path"):
                    body += f'<p><a href="{e(ledger["path"])}">Review ledger</a> · reviewed head <code>{e(ledger.get("header_head"))}</code> · head {e(ledger["head_comparison"])} / base {e(ledger["base_comparison"])}</p><p>{e(ledger["next_check"])}</p>'
                for thread in pr["review_threads"] if data.get("target") else threads:
                    body += f'<p><a href="{e(thread["url"] or pr["url"])}">{e(thread["path"])}:{e(thread["line"])}</a> · {"resolved" if thread["resolved"] else "open"} · {e(thread["author"])}{" · outdated diff" if thread["outdated"] else ""}</p>'
                body += f'<p class="muted">{e(pr["coverage_note"])}</p></article>'
        elif name == "history":
            body += f'<p>Atlas: {e(data["atlas"])}. {e(data["lookup"]["sources"])} retained lookup sources refreshed.</p>'
        sections.append(f'<section><h2>{e(name.title())}</h2>{body}</section>')
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Work status</title><style>body{font:16px/1.6 system-ui;background:#f6f5f1;color:#202824;max-width:1100px;margin:36px auto;padding:0 24px}h1{font-size:36px;margin-bottom:4px}h2{font-size:25px}h3{font-size:17px}section{background:white;border:1px solid #dadfd8;border-radius:12px;padding:24px;margin:24px 0}a{color:#245a80}article{border-top:1px solid #ddd;margin-top:18px}.state{padding:2px 8px;border-radius:6px;background:#ecebe6}.pass,.refreshed{background:#dcefdc}.fail{background:#f8d9d3}.unknown,.incomplete,.pending{background:#fff0c2}.muted{color:#616b64;font-size:13px}pre{white-space:pre-wrap;overflow-wrap:anywhere}code{overflow-wrap:anywhere}.error{color:#8a3424}</style><h1>Work status</h1><p class="muted">Observed ' + e(report["observed_at"]) + ' · local, read-only collection · no external notifications</p>' + ''.join(sections) + '<p>Sources are current only at the displayed observation times. PR facts are separate from review and approval.</p></html>'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path.home() / ".config/work-status/config.json")
    parser.add_argument("--out", type=Path, default=Path.home() / "Documents/ccusage-reports/work-status")
    parser.add_argument("--only", choices=("all", "prs"), default="all",
                        help="Accepted for compatibility. Collects PRs in either mode.")
    parser.add_argument("--pr", help="Target a github.com PR URL or OWNER/REPO#NUMBER, regardless of author or state.")
    parser.add_argument("--ledger", type=Path, help="Read an existing task-local review ledger for the named PR; never executes it.")
    parser.add_argument("--refresh-history", action="store_true", help="Also refresh find-work and existing local session-atlas HTML; no email.")
    args = parser.parse_args()
    if args.ledger and not args.pr:
        parser.error("--ledger requires --pr")
    if args.pr:
        try:
            parse_pr_target(args.pr)
        except ValueError as exc:
            parser.error(str(exc))
    config = json.loads(args.config.expanduser().read_text()) if args.config.expanduser().exists() else {}
    if not isinstance(config, dict):
        parser.error("config must be a JSON object")
    out = args.out.expanduser()
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    report = collect(config, refresh=args.refresh_history, out=out, target=args.pr, ledger_path=args.ledger)
    atomic_write(out / "latest.json", json.dumps(report, indent=2))
    atomic_write(out / "index.html", render(report))
    print(json.dumps({"report": str(out / "index.html"), "states": {k: v["state"] for k, v in report["collectors"].items()}}))
    return 2 if any(v.get("error") or v["state"] in ("unknown", "incomplete") for v in report["collectors"].values()) else 0


if __name__ == "__main__":
    sys.exit(main())

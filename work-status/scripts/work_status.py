#!/usr/bin/env python3
"""Read-only backup and PR digest. Writes local reports; never sends notifications."""

import argparse
from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit


PR_QUERY = """query($q:String!, $after:String) {
  search(query:$q, type:ISSUE, first:50, after:$after) {
    issueCount pageInfo { hasNextPage endCursor }
    nodes { ... on PullRequest {
      number title url isDraft headRefOid baseRefOid reviewDecision mergeStateStatus
      repository { nameWithOwner }
      commits(last:1) { nodes { commit { oid statusCheckRollup {
        contexts(first:100) { pageInfo { hasNextPage } nodes {
          ... on CheckRun { name status conclusion detailsUrl }
          ... on StatusContext { context state targetUrl }
        } }
      } } } }
      reviewThreads(first:100) { pageInfo { hasNextPage } nodes {
        isResolved isOutdated path line
        comments(first:1) { nodes { url author { login } } }
      } }
    } }
  }
}"""


def now():
    return datetime.now(timezone.utc).isoformat()


def run(argv, *, cwd=None, timeout=90, env=None, input=None):
    """One bounded attempt. Access failures do not trigger repeated login attempts."""
    try:
        result = subprocess.run([str(x) for x in argv], cwd=cwd, text=True,
                                capture_output=True, timeout=timeout,
                                env={**os.environ, **(env or {})}, input=input)
    except subprocess.TimeoutExpired as exc:
        stderr = exc.stderr or b""
        if isinstance(stderr, bytes):
            stderr = stderr.decode(errors="replace")
        stages = re.findall(r"work-status-stage: ([a-z0-9_-]+)", stderr)
        raise RuntimeError(f"{Path(str(argv[0])).name}: exceeded {timeout}s" +
                           (f"; last stage {stages[-1]}" if stages else "")) from exc
    if result.returncode:
        # Return useful sanitized diagnostics without printing arbitrary tool output.
        detail = result.stderr.lower()
        reason = ("remote observer deadline exceeded" if result.returncode in (142, -14) else
                  "authentication required" if any(s in detail for s in ("authentication failed", "please run:  gh auth login", "unable to locate credentials")) else
                  "network/access failure" if any(s in detail for s in ("connect", "resolve", "permission denied", "operation not permitted")) else
                  f"command exited {result.returncode}")
        stages = re.findall(r"work-status-stage: ([a-z0-9_-]+)", detail)
        if stages:
            reason += f"; last stage {stages[-1]}"
        api_error = re.search(r"An error occurred \(([A-Za-z0-9]+)\) when calling", result.stderr)
        if api_error:
            reason += "; " + api_error.group(1)
        try:
            error = json.loads(result.stdout).get("error", "")
            if re.fullmatch(r"[A-Za-z]+(?:Error|NotFound)", error):
                reason += f" (observer {error})"
        except (ValueError, AttributeError, TypeError):
            pass
        raise RuntimeError(f"{Path(str(argv[0])).name}: {reason}")
    return result.stdout


def checked_json(raw):
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("errors") or data.get("error"):
        raise ValueError("collector returned an error or invalid JSON object")
    return data


def deployed_release(cron, remote_home):
    """Parse known cron data, never evaluate the cron's shell instructions."""
    prefix = remote_home + "/.local/share/offsite-backup/releases/"
    begin, end = "# BEGIN ami-offsite-backup-nebius", "# END ami-offsite-backup-nebius"
    if cron.count(begin) != 1 or cron.count(end) != 1:
        raise ValueError("expected exactly one managed Nebius backup cron block")
    block = cron.split(begin, 1)[1].split(end, 1)[0]
    jobs = [line for line in block.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if len(jobs) != 1:
        raise ValueError("expected one managed backup trigger")
    hashes = re.findall(re.escape(prefix) + r"([0-9a-f]{40})(?=/|\s|$)", jobs[0])
    if not hashes or len(set(hashes)) != 1:
        raise ValueError("backup release missing or ambiguous in cron")
    expected = remote_home + "/.config/offsite-backup/backup.yaml"
    if not jobs[0].rstrip().endswith("-m devops.offsite_backup submit " + expected):
        raise ValueError("unrecognized backup config/entry point; inspect cron before adapting collector")
    return prefix + hashes[0], expected, jobs[0].split(" cd ", 1)[0]


def backup_status(config):
    repo = Path(config.get("repo", "~/Documents/amilabs")).expanduser()
    home = config.get("remote_home", "/home/jiehao")
    if not home.startswith("/home/") or ".." in PurePosixPath(home).parts or not re.fullmatch(r"/home/[a-zA-Z0-9_-]+", home):
        raise ValueError("remote_home must be one /home/USER directory")
    profile = config.get("read_profile", "r2-backup-restore")
    if profile != "r2-backup-restore":
        raise ValueError("observer requires the existing r2-backup-restore read profile")
    cron = run([repo / "bin/nb", "scrontab", "-l"], cwd=repo)
    release, path, schedule = deployed_release(cron, home)
    observer = Path(__file__).with_name("backup_observer.py").read_text()
    # bin/nb normally redirects Python bytecode lookup to a shared runtime
    # tree. An isolated stdlib-only reader can use the host's installed cache.
    remote = [repo / "bin/nb", "/usr/bin/python3", "-I", "-B", "-c", observer]
    yaml_text = checked_json(run([*remote, 'config', path], cwd=repo, timeout=45))['config_yaml']
    # macOS's existing Ruby/Psych safe parser avoids new packages locally and
    # importing even a small Python package from the remote shared filesystem.
    parsed = checked_json(run(['ruby', '-r', 'yaml', '-r', 'json', '-e',
        'puts JSON.generate(YAML.safe_load(STDIN.read, aliases: false))'], input=yaml_text, timeout=10))
    metadata = {k: parsed[k] for k in ('site', 'state_dir', 'tables', 'storage')}
    metadata['max_backup_age_hours'] = parsed.get('max_backup_age_hours', 48)
    # Do not send unneeded configuration or source paths back in SSH arguments.
    metadata['tables'] = [{k:t[k] for k in ('name', 'enrollment_file')} for t in metadata['tables']]
    metadata['storage'] = {k:metadata['storage'][k] for k in ('bucket', 'endpoint')} | {'prefix':parsed['storage'].get('prefix', 'lance-v1')}
    raw = run([*remote, 'receipts', json.dumps(metadata), release], cwd=repo, timeout=45)
    result = checked_json(raw)
    if not result.get("tables"):
        raise ValueError("backup observer returned no table evidence")
    storage = result.pop("storage")
    endpoint = urlsplit(storage["endpoint"])
    if (endpoint.scheme != "https" or not (endpoint.hostname or "").endswith(".r2.cloudflarestorage.com")
            or endpoint.username or endpoint.password or endpoint.query or endpoint.fragment or endpoint.path not in ("", "/")):
        raise ValueError("expected the deployed Cloudflare R2 HTTPS endpoint without credentials")
    result["read_profile"] = profile
    for table in result["tables"]:
        try:
            if table.get("error"):
                raise ValueError("remote receipt unreadable: " + table["error"])
            point = latest_point(storage, table["table"], table["generation"], profile)
            instant = datetime.now(timezone.utc)
            table.update(classify_backup(point, table.get("failure"), instant, result["max_backup_age_hours"]))
            table["observed_at"] = instant.isoformat()
        except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
            table.update(state="unknown", message=str(exc) if isinstance(exc, (RuntimeError, ValueError)) else type(exc).__name__)
        table.pop("failure", None)
    result["scope"] = "R2 completion manifest identity/times and latest failure receipts. No full manifest-schema validation, payload scan, recovery check or Datadog emission."
    result["schedule"] = schedule
    result["state"] = ("attention" if any(x["state"] in ("failed", "stale") for x in result["tables"]) else
                       "unknown" if any(x["state"] == "unknown" for x in result["tables"]) else "fresh")
    return result


def aware(value):
    if not isinstance(value, str):
        raise ValueError("backup timestamp is not a string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("backup timestamp has no timezone")
    return parsed


def latest_point(storage, table, generation, profile):
    """Use the established local read-only CLI; never enumerate payload objects."""
    if not re.fullmatch(r"[a-z][a-z0-9_-]{0,79}", table) or not re.fullmatch(r"[0-9a-f]{32}", generation):
        raise ValueError("invalid table or enrollment generation")
    prefix = f'{storage["prefix"]}/{table}/{generation}/snapshots/'
    argv = ["aws", "--profile", profile, "--endpoint-url", storage["endpoint"],
            "--region", "auto", "--cli-connect-timeout", "5", "--cli-read-timeout", "15",
            "--no-cli-pager", "--output", "json", "s3api"]
    env = {"AWS_MAX_ATTEMPTS": "2", "AWS_RETRY_MODE": "standard"}
    # AWS CLI handles pagination. Only snapshot metadata lives below this prefix.
    listing = checked_json(run([*argv, "list-objects-v2", "--bucket", storage["bucket"],
                                "--prefix", prefix], timeout=60, env=env))
    pattern = re.compile(re.escape(prefix) + r"[0-9a-f]{32}/manifest\.json$")
    completions = [item for item in listing.get("Contents", []) if pattern.fullmatch(item["Key"])]
    if not completions:
        return None
    newest = max(aware(item["LastModified"]) for item in completions)
    candidates = [item for item in completions if aware(item["LastModified"]) == newest]
    if len(candidates) > 20:
        raise ValueError("too many simultaneous completion candidates; inspect manually")
    points = []
    with tempfile.TemporaryDirectory(prefix="work-status-") as directory:
        for item in candidates:
            if not 0 < item["Size"] <= 64 * 1024 * 1024:
                raise ValueError("completion manifest size invalid")
            path = Path(directory) / "manifest.json"
            path.touch(mode=0o600, exist_ok=True)
            run([*argv, "get-object", "--bucket", storage["bucket"], "--key", item["Key"], path], timeout=60, env=env)
            if path.stat().st_size != item["Size"]:
                raise ValueError("manifest changed since listing")
            point = checked_json(path.read_text())
            expected_id = item["Key"].split("/")[-2]
            if (point.get("format") != "lance-v1" or
                    (point.get("table"), point.get("generation"), point.get("backup_id")) != (table, generation, expected_id)):
                raise ValueError("completion manifest identity mismatch")
            if aware(point["completed_at"]) < aware(point["backup_time"]):
                raise ValueError("completion precedes backup point")
            points.append({"backup_id": point["backup_id"], "generation": generation,
                           "backup_time": point["backup_time"], "completed_at": point["completed_at"],
                           "manifest": f's3://{storage["bucket"]}/{item["Key"]}'})
    return max(points, key=lambda p: (aware(p["completed_at"]), aware(p["backup_time"]), p["backup_id"]))


def classify_backup(point, failure, instant, max_age):
    if not point:
        return {"state": "unknown", "message": "No completion manifest for the enrolled generation."}
    age = (instant - aware(point["backup_time"])).total_seconds() / 3600
    state = "fresh" if 0 <= age <= max_age else "stale"
    message = "Recent completion manifest found." if state == "fresh" else "Latest backup point is stale or in the future."
    if failure and failure["backup_id"] != point["backup_id"] and aware(failure["failed_at"]) >= aware(point["completed_at"]):
        state, message = "failed", "A newer backup attempt failed; inspect its private job log."
    return {**point, "state": state, "age_hours": round(age, 2), "message": message}


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
    unresolved = []
    for thread in threads.get("nodes", []):
        if not thread["isResolved"]:
            first = next(iter(thread["comments"]["nodes"]), {})
            unresolved.append({"path": thread["path"], "line": thread["line"],
                               "outdated": thread["isOutdated"], "url": first.get("url"),
                               "author": (first.get("author") or {}).get("login")})
    complete = not connection.get("pageInfo", {}).get("hasNextPage", False) and not threads.get("pageInfo", {}).get("hasNextPage", False)
    head_matches = commit.get("oid") == pr["headRefOid"]
    # Empty checks is 'none reported', never a claim that required CI passed.
    ci = ("unknown" if not head_matches else "fail" if any(c["state"] == "fail" for c in checks) else
          "incomplete" if not complete else "pending" if any(c["state"] == "pending" for c in checks) else
          "unknown" if any(c["state"] == "unknown" for c in checks) else "pass" if checks else "none reported")
    action = ("Inspect failed checks on this head." if ci == "fail" else
              "Refresh incomplete or missing evidence." if not complete or not head_matches or ci == "unknown" else
              "Read and address unresolved review discussions." if unresolved else
              "Wait for checks on this head." if ci == "pending" else
              "Address requested review changes." if pr.get("reviewDecision") == "CHANGES_REQUESTED" else
              "Decide when the draft is ready to request review." if pr["isDraft"] else
              "Human merge decision; confirm required policies and review evidence." if pr.get("reviewDecision") == "APPROVED" else
              "Reviewer decision needed; confirm required checks before proceeding.")
    return {"repository": pr["repository"]["nameWithOwner"], "number": pr["number"],
            "title": pr["title"], "url": pr["url"], "draft": pr["isDraft"],
            "head": pr["headRefOid"], "base": pr["baseRefOid"],
            "review_decision": pr.get("reviewDecision"), "merge_state": pr.get("mergeStateStatus"),
            "ci": ci, "checks": checks, "unresolved_threads": unresolved, "next_action": action,
            "complete": complete and head_matches,
            "coverage_note": ("First 100 checks/threads; connection truncated." if not complete else
                              "Head changed or unavailable; recollect before relying on checks." if not head_matches else
                              "Current head status and review threads; no code review or merge-policy evaluation.")}


def ledger_evidence(pr):
    path = Path.home() / ".agents/reviews" / pr["repository"].replace("/", "-") / f'pr-{pr["number"]}.md'
    try:
        with path.open() as stream:
            header = stream.read(8192)
    except FileNotFoundError:
        return {"state": "not found in shared ledger directory"}
    except OSError:
        return {"state": "shared ledger unreadable"}
    match = re.search(r"(?im)^Base / head:.* / ([0-9a-f]{7,40})\s*$", header)
    head = match.group(1) if match else None
    return {"path": str(path), "header_head": head,
            "state": "header mentions current head" if head and pr["head"].startswith(head) else
                     "header head differs" if head else "header head unrecognized",
            "scope": "Header comparison only; task-local ledgers and appended follow-ups are not interpreted."}


def pr_status(config):
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
    atlas = Path(config.get("atlas_root", "~/Documents/session-atlas")).expanduser()
    lookup = Path(__file__).resolve().parents[2] / "find-work/scripts/find_work.py"
    # The installed copies live as sibling skill directories.
    command = [sys.executable, lookup, "refresh", "--atlas-root", atlas]
    if config.get("lookup_cache"):
        command += ["--cache-dir", str(Path(config["lookup_cache"]).expanduser())]
    result = checked_json(run(command, timeout=180))
    site = Path(config.get("atlas_out", str(out / "session-atlas"))).expanduser()
    archive = Path(config.get("atlas_archive", str(atlas / "archive"))).expanduser()
    run([sys.executable, atlas / "generate_site.py", "--all", "--out", site, "--archive", archive], cwd=atlas, timeout=300)
    return {"observed_at": now(), "state": "refreshed", "lookup": result["coverage"], "atlas": str(site / "index.html")}


def collect(config, only="all", refresh=False, out=Path(".")):
    result = {"schema": 1, "observed_at": now(), "collectors": {}}
    jobs = [("backup", backup_status), ("prs", pr_status)]
    if refresh:
        jobs.append(("history", lambda c: refresh_history(c, out)))
    for name, action in jobs:
        if name != "history" and only not in ("all", name):
            continue
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
        elif name == "backup":
            body += f'<p>Freshness threshold: {e(data["max_backup_age_hours"])} hours. Release <code>{e(data["release"][:12])}</code>. Trigger: {e(data["schedule"])}</p>'
            rows = ''.join(f'<tr><td>{e(t["table"])}</td><td>{tag(t["state"])}</td><td>{e(t.get("age_hours"))} h</td><td>{e(t.get("completed_at"))}</td><td>{e(t["message"])} {e(t.get("error") or "")}</td></tr>' for t in data["tables"])
            body += '<table><thead><tr><th>Table</th><th>State</th><th>Point age</th><th>Completed</th><th>Evidence</th></tr></thead><tbody>' + rows + '</tbody></table>'
            body += f'<p>{e(data["scope"])}</p>'
        elif name == "prs":
            body += f'<p>{len(data["prs"])} of {e(data["reported_count"])} authored open PRs. {e(data["scope"])}</p>'
            for pr in data["prs"]:
                threads = pr["unresolved_threads"]
                failed = [c["name"] for c in pr["checks"] if c["state"] == "fail"]
                body += f'<article><h3><a href="{e(pr["url"])}">{e(pr["repository"])} #{pr["number"]}: {e(pr["title"])}</a></h3><p>{"Draft" if pr["draft"] else "Open"} · CI {tag(pr["ci"])} · {len(threads)} unresolved thread(s) · review {e(pr["review_decision"] or "none reported")}</p><p>Head <code>{e(pr["head"])}</code></p>'
                if failed:
                    body += f'<p>Failed checks: {e(", ".join(failed))}</p>'
                body += f'<p>Next: {e(pr["next_action"])}</p><p class="muted">Prior review ledger: {e(pr.get("ledger", {}).get("state", "not checked"))}</p>'
                for thread in threads:
                    body += f'<p><a href="{e(thread["url"] or pr["url"])}">{e(thread["path"])}:{e(thread["line"])}</a> · {e(thread["author"])}{" · outdated diff" if thread["outdated"] else ""}</p>'
                body += f'<p class="muted">{e(pr["coverage_note"])}</p></article>'
        elif name == "history":
            body += f'<p>Atlas: {e(data["atlas"])}. {e(data["lookup"]["sources"])} retained lookup sources refreshed.</p>'
        sections.append(f'<section><h2>{e(name.title())}</h2>{body}</section>')
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Work status</title><style>body{font:16px/1.6 system-ui;background:#f6f5f1;color:#202824;max-width:1100px;margin:36px auto;padding:0 24px}h1{font-size:36px;margin-bottom:4px}h2{font-size:25px}h3{font-size:17px}section{background:white;border:1px solid #dadfd8;border-radius:12px;padding:24px;margin:24px 0}a{color:#245a80}table{border-collapse:collapse;width:100%;font-size:14px}td,th{text-align:left;border-bottom:1px solid #ddd;padding:10px;vertical-align:top}article{border-top:1px solid #ddd;margin-top:18px}.state{padding:2px 8px;border-radius:6px;background:#ecebe6}.fresh,.pass,.refreshed{background:#dcefdc}.fail,.failed,.stale,.attention{background:#f8d9d3}.unknown,.incomplete,.pending{background:#fff0c2}.muted{color:#616b64;font-size:13px}pre{white-space:pre-wrap;overflow-wrap:anywhere}code{overflow-wrap:anywhere}.error{color:#8a3424}</style><h1>Work status</h1><p class="muted">Observed ' + e(report["observed_at"]) + ' · local, read-only collection · no external notifications</p><p id="age"></p>' + ''.join(sections) + '<p>Sources are current only at the displayed observation times. Freshness is separate from integrity and recovery. PR facts are separate from review and approval.</p><script>const age=(Date.now()-Date.parse(' + json.dumps(report["observed_at"]) + '))/36e5;if(age>26)document.getElementById("age").textContent="This report is over 26 hours old. Refresh before relying on it.";</script></html>'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path.home() / ".config/work-status/config.json")
    parser.add_argument("--out", type=Path, default=Path.home() / "Documents/ccusage-reports/work-status")
    parser.add_argument("--only", choices=("all", "backup", "prs"), default="all")
    parser.add_argument("--refresh-history", action="store_true", help="Also refresh find-work and existing local session-atlas HTML; no email.")
    args = parser.parse_args()
    config = json.loads(args.config.expanduser().read_text()) if args.config.expanduser().exists() else {}
    if not isinstance(config, dict):
        parser.error("config must be a JSON object")
    out = args.out.expanduser()
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    report = collect(config, args.only, args.refresh_history, out)
    atomic_write(out / "latest.json", json.dumps(report, indent=2))
    atomic_write(out / "index.html", render(report))
    print(json.dumps({"report": str(out / "index.html"), "states": {k: v["state"] for k, v in report["collectors"].items()}}))
    return 2 if any(v.get("error") or v["state"] in ("unknown", "incomplete") for v in report["collectors"].values()) else 0


if __name__ == "__main__":
    sys.exit(main())

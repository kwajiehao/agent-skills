#!/usr/bin/env python3
"""Find earlier work using session-atlas's existing transcript parser."""

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile


VERSION = 2
STOP = set('a an and are as at be been by can did do does earlier find for from had has have help i in is it latest look me my of on or our please previous recent session sessions that the this to was we were what where which with work you'.split())
LOOKUP = re.compile(r'(?:find|locate|which|recent).{0,70}sessions?|sessions?.{0,40}(?:talking|discussing)', re.I | re.S)
PATH = re.compile(r'(?:/Users/|/home/|/mnt/|devops/|data/|outputs/|work/)[\w./@+() -]+')


def now():
    return datetime.now(timezone.utc).isoformat()


def redact(text):
    text = re.sub(r'(?i)((?:api[_ -]?key|access[_ -]?token|secret[_ -]?key|password|authorization)\s*[=:]\s*)[^\s,;]+', r'\1[REDACTED]', text)
    return re.sub(r'\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16})\b', '[REDACTED]', text)


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.find-work-')
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, ensure_ascii=False)
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atlas_parser(root):
    if not (root / 'codex_parse.py').is_file():
        raise ValueError(f'Session-atlas parser not found at {root}; use --atlas-root.')
    sys.path.insert(0, str(root))
    parser = importlib.import_module('codex_parse')
    signature = hashlib.sha256()
    for name in ('codex_parse.py', 'ccx_parse.py'):
        signature.update((root / name).read_bytes())
    return parser, signature.hexdigest()


def metadata(home):
    """Read current titles without modifying the app database."""
    candidates = sorted(home.glob('state_*.sqlite'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        return {}, 'No Codex state database; titles fall back to retained prompts.'
    try:
        with closing(sqlite3.connect(candidates[0].resolve().as_uri() + '?mode=ro', uri=True)) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute('select id,title,source,cwd from threads').fetchall()
            return {row['id']: dict(row) for row in rows}, None
    except sqlite3.Error:
        return {}, 'Codex metadata could not be read; titles fall back to retained prompts.'


def source_document(parsed, source):
    if parsed is None:
        return None
    cwd, session, milestones, _, diagnostics = parsed
    segments = []
    previous_lookup = False
    for milestone in milestones:
        text = milestone.get('text') or ''
        lookup = bool(LOOKUP.search(text) or (previous_lookup and re.match(
            r'\s*(?:actually|no[, ]|not that|i had one|this morning|anything else|what about)', text, re.I)))
        previous_lookup = lookup
        if text and not text.startswith(('<heartbeat>', '<send_user_message_question_reply>')):
            segments.append({'kind': 'lookup' if lookup else 'prompt', 'text': redact(text), 'at': milestone.get('ts')})
        # Exclude answers whose job was only to locate another conversation.
        if not lookup:
            activity = milestone.get('activity') or {}
            for response in activity.get('responses', []):
                value = response.get('text') or ''
                if value:
                    segments.append({'kind': 'answer', 'text': redact(value[:2400]), 'at': response.get('ts') or milestone.get('ts')})
            for tool in activity.get('tool_events', []):
                label = tool.get('label') or ''
                if label:
                    segments.append({'kind': 'tool', 'text': redact(label), 'at': milestone.get('ts')})
    return {'id': session['id'], 'cwd': cwd, 'title': session.get('title'),
            'last_activity': session.get('last_ts'), 'is_agent': bool(session.get('is_subagent')),
            'source': source, 'segments': segments, 'diagnostics': len(diagnostics)}


def refresh(atlas_root, home, cache_dir, archive_root=None):
    parser, parser_version = atlas_parser(atlas_root)
    cache_path = cache_dir / 'search.json'
    try:
        old = json.loads(cache_path.read_text())
    except (OSError, ValueError):
        old = {}
    if not isinstance(old, dict) or old.get('version') != VERSION or old.get('parser_version') != parser_version:
        old = {}
    previous = old.get('sources', {})
    if not isinstance(previous, dict):
        previous = {}
    paths = parser.codex_home_rollouts([str(home)])
    live_names = {Path(path).stem for path in paths}
    archive_root = archive_root or atlas_root / 'archive'
    archives = [p for p in (archive_root / 'codex').glob('rollout-*.json') if p.stem not in live_names]
    sources, warnings = {}, []
    parsed_count = reused = 0
    for path in [Path(p) for p in paths] + archives:
        key = str(path.resolve())
        try:
            stat = path.stat()
            signature = [stat.st_size, stat.st_mtime_ns]
            cached = previous.get(key)
            if isinstance(cached, dict) and cached.get('signature') == signature and 'document' in cached:
                sources[key] = previous[key]
                reused += 1
                continue
            if path.suffix == '.json':
                item = json.loads(path.read_text())
                parsed = item['cwd'], item['session'], item['milestones'], item.get('branches', {}), item.get('diagnostics', [])
            else:
                parsed = parser._parse_rollout(str(path))
            document = source_document(parsed, key)
            sources[key] = {'signature': signature, 'document': document}
            parsed_count += 1
        except (OSError, ValueError, KeyError, TypeError) as exc:
            warnings.append(f'Could not index {path.name}: {type(exc).__name__}')
    index = {'version': VERSION, 'parser_version': parser_version, 'refreshed_at': now(),
             'sources': sources, 'warnings': warnings}
    atomic_json(cache_path, index)
    titles, warning = metadata(home)
    if warning:
        warnings.append(warning)
    documents = {}
    for entry in sources.values():
        doc = entry.get('document')
        if not doc:
            continue
        target = documents.setdefault(doc['id'], {**doc, 'sources': [], 'segments': [], 'diagnostics': 0})
        target['sources'].append(doc['source'])
        target['segments'].extend(doc['segments'])
        target['diagnostics'] += doc['diagnostics']
        if (doc.get('last_activity') or '') > (target.get('last_activity') or ''):
            target['last_activity'] = doc['last_activity']
    for id, doc in documents.items():
        row = titles.get(id, {})
        if row.get('title'):
            doc['title'] = row['title']
            doc['title_source'] = 'Codex metadata'
        else:
            doc['title'] = doc.get('title') or next((p['text'][:180] for p in doc['segments'] if p['kind'] == 'prompt'), 'Untitled retained conversation')
            doc['title_source'] = 'Retained parser/prompt fallback'
        source = str(row.get('source', ''))
        doc['is_agent'] = doc['is_agent'] or 'subagent' in source or 'guardian' in source
        seen = set()
        unique = []
        for segment in doc['segments']:
            key = segment['kind'], segment['at'], segment['text']
            if key not in seen:
                seen.add(key)
                unique.append(segment)
        doc['segments'] = unique
    return list(documents.values()), {'refreshed_at': index['refreshed_at'], 'sources': len(sources),
        'threads': len(documents), 'parsed': parsed_count, 'reused': reused,
        'sources_without_indexed_activity': sum(entry.get('document') is None for entry in sources.values()),
        'skipped_records': sum(x['diagnostics'] for x in documents.values()), 'warnings': warnings,
        'coverage': 'Retained Codex prompts, bounded assistant excerpts/tool labels and existing atlas archives; not every tool output or deleted session.'}


def terms(text):
    words = re.findall(r'[a-z0-9]+', text.lower())
    result = []
    for word in words:
        if word in STOP:
            continue
        if word in ('crontab', 'scrontab'):
            word = 'cron'
        elif word.endswith('s') and len(word) > 4:
            word = word[:-1]
        result.append(word)
    return set(result)


def before_time(value, boundary):
    if not boundary:
        return True
    if not value:
        return False
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')) <= boundary
    except (ValueError, TypeError):
        return False


def search(documents, query, pr=None, limit=3, before=None, include_agents=False, sort='relevance'):
    wanted = terms(query)
    if pr:
        wanted.add(str(pr))
    if not wanted:
        raise ValueError('Give a topic or --pr NUMBER.')
    boundary = datetime.fromisoformat(before.replace('Z', '+00:00')) if before else None
    if boundary and boundary.tzinfo is None:
        raise ValueError('--before needs a timezone, e.g. 2026-11-05T12:00:00+08:00.')
    results = []
    for doc in documents:
        if doc['is_agent'] and not include_agents:
            continue
        title_words = terms(doc['title'][:180])
        matches = []
        coverage = set()
        for segment in doc['segments']:
            if segment['kind'] == 'lookup' or not before_time(segment['at'], boundary):
                continue
            words = terms(segment['text'])
            hit = wanted & words
            if pr and not re.search(rf'(?<![A-Za-z0-9]){re.escape(str(pr))}(?![A-Za-z0-9])', segment['text']):
                continue
            if not hit:
                continue
            coverage.update(hit)
            weight = {'prompt': 2.5, 'answer': 1.0, 'tool': 0.6}[segment['kind']]
            value = len(hit) / len(wanted) * weight
            matches.append((value, segment['at'] or '', segment, hit))
        if not matches:
            continue
        matches.sort(key=lambda x: (x[0], x[1]), reverse=True)
        best = matches[0]
        # Coverage first, then one strong evidence match; repeated mentions do not inflate rank.
        score = len(coverage) / len(wanted) * 10 + best[0] + len(wanted & title_words) / len(wanted)
        selected = max(matches, key=lambda x: x[1]) if sort == 'recent' else best
        segment = selected[2]
        raw = segment['text']
        positions = [m.start() for word in selected[3] for m in re.finditer(re.escape(word), raw, re.I)]
        start = max(0, min(positions, default=0) - 110)
        excerpt = ('…' if start else '') + ' '.join(raw[start:start + 560].split())
        referenced = list(dict.fromkeys(m.group(0).strip().rstrip('.,:; )') for m in PATH.finditer(raw)))[:8]
        results.append({'thread_id': doc['id'], 'title': doc['title'], 'title_source': doc['title_source'],
            'url': f"codex://threads/{doc['id']}", 'cwd': doc['cwd'], 'last_activity': doc['last_activity'],
            'matched_at': segment['at'], 'evidence_kind': segment['kind'], 'excerpt': excerpt,
            'referenced_paths': referenced, 'sources': doc['sources'], 'score': round(score, 4)})
    return sorted(results, key=lambda r: (r['matched_at'] or '', r['score']) if sort == 'recent' else
                  (r['score'], r['matched_at'] or ''), reverse=True)[:limit]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query', nargs='*')
    parser.add_argument('--pr', type=int)
    parser.add_argument('--limit', type=int, default=3)
    parser.add_argument('--before')
    parser.add_argument('--sort', choices=('relevance', 'recent'), default='relevance')
    parser.add_argument('--include-agents', action='store_true')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--atlas-root', type=Path, default=Path.home() / 'Documents/session-atlas')
    parser.add_argument('--codex-home', type=Path, default=Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))))
    parser.add_argument('--cache-dir', type=Path, default=Path.home() / '.local/state/find-work')
    args = parser.parse_args()
    if not 1 <= args.limit <= 20:
        parser.error('--limit must be between 1 and 20')
    documents, coverage = refresh(args.atlas_root.expanduser(), args.codex_home.expanduser(), args.cache_dir.expanduser())
    refresh_only = args.query == ['refresh'] and args.pr is None
    results = [] if refresh_only else search(documents, ' '.join(args.query), args.pr, args.limit, args.before, args.include_agents, args.sort)
    if args.json or refresh_only:
        print(json.dumps({'coverage': coverage, 'results': results}, indent=2, ensure_ascii=False))
    else:
        print(f"Checked {coverage['sources']} retained sources at {coverage['refreshed_at']}; "
              f"{coverage['sources_without_indexed_activity']} without indexable activity; {coverage['skipped_records']} skipped records.")
        for result in results:
            print(f"\n{result['title']}\n{result['url']}\nMatch: {result['matched_at']} ({result['evidence_kind']}); last activity: {result['last_activity']}\n{result['excerpt']}")
        if not results:
            print('No retained evidence matched. This does not establish that the work never happened.')
        for warning in coverage['warnings']:
            print('Warning:', warning, file=sys.stderr)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, sqlite3.Error) as exc:
        print(f'find-work: {exc}', file=sys.stderr)
        raise SystemExit(2)

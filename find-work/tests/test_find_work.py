import importlib.util
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('find_work', Path(__file__).parents[1] / 'scripts/find_work.py')
fw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fw)


def doc(id, prompt, *, kind='prompt', agent=False, at='2026-11-04T02:00:00Z'):
    return {'id': id, 'title': prompt, 'title_source': 'fixture', 'cwd': '/work',
            'last_activity': at, 'is_agent': agent, 'sources': [],
            'segments': [{'kind': kind, 'at': at, 'text': prompt}]}


class SearchTests(unittest.TestCase):
    def test_real_work_ranks_above_lookup_and_repeated_incidental_mentions(self):
        actual = doc('actual', 'Check my Nebius crontab backup jobs')
        lookup = doc('lookup', 'find sessions about Nebius backup cron', kind='lookup')
        incidental = doc('incidental', 'we discussed the Nebius backup')
        incidental['segments'] *= 50
        self.assertEqual([r['thread_id'] for r in fw.search([incidental, lookup, actual], 'Nebius backup cron')], ['actual', 'incidental'])

    def test_exact_pr_and_historical_boundary(self):
        docs = [doc('wrong', 'PR 17960'), doc('right', 'Review PR 7960'),
                doc('future', 'PR 7960', at='2026-11-06T02:00:00Z')]
        result = fw.search(docs, '', pr=7960, before='2026-11-05T00:00:00+08:00')
        self.assertEqual([r['thread_id'] for r in result], ['right'])
        with self.assertRaisesRegex(ValueError, 'timezone'):
            fw.search(docs, 'PR', before='2026-11-05')

    def test_agents_are_opt_in_and_secrets_are_redacted(self):
        self.assertFalse(fw.search([doc('child', 'backup cron', agent=True)], 'backup'))
        self.assertTrue(fw.search([doc('child', 'backup cron', agent=True)], 'backup', include_agents=True))
        value = fw.redact('api_key=private password:secret ghp_' + 'x' * 30)
        self.assertNotIn('private', value)
        self.assertNotIn('secret', value)
        self.assertEqual(value.count('[REDACTED]'), 3)

    def test_latest_uses_matching_evidence_not_unrelated_chat_activity(self):
        old = doc('old', 'backup cron', at='2026-11-01T00:00:00Z')
        old['last_activity'] = '2026-11-07T00:00:00Z'
        recent = doc('recent', 'backup', kind='answer', at='2026-11-05T00:00:00Z')
        self.assertEqual(fw.search([old, recent], 'backup cron', sort='recent')[0]['thread_id'], 'recent')

    def test_lookup_answers_do_not_become_new_evidence(self):
        parsed = ('/work', {'id': 'a', 'last_ts': 'now'}, [
            {'text': 'find the session about backups', 'ts': 'then',
             'activity': {'responses': [{'text': 'Nebius backup cron', 'ts': 'then'}]}},
            {'text': 'actually I had one this morning', 'ts': 'then',
             'activity': {'responses': [{'text': 'Nebius backup cron'}]}},
            {'text': 'Now check Nebius backup cron', 'ts': 'later'}], {}, [])
        result = fw.source_document(parsed, 'fixture')
        self.assertEqual([s['kind'] for s in result['segments']], ['lookup', 'lookup', 'prompt'])

    def test_resume_dedup_archive_recovery_titles_and_changed_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home, archive, cache = root / 'home', root / 'archive/codex', root / 'cache'
            home.mkdir(); archive.mkdir(parents=True)
            one, two = home / 'rollout-one.jsonl', home / 'rollout-two.jsonl'
            one.write_text('1'); two.write_text('2')
            milestone = {'text': 'backup cron', 'ts': '2026-11-04T00:00:00Z'}
            def parse(path):
                return '/work', {'id': 'same', 'last_ts': '2026-11-04T00:00:00Z'}, [milestone], {}, []
            (archive / 'rollout-lost.json').write_text(json.dumps({'cwd': '/old',
                'session': {'id': 'archived'}, 'milestones': [{'text': 'old restore', 'ts': 'then'}]}))
            with closing(sqlite3.connect(home / 'state_5.sqlite')) as connection:
                connection.execute('create table threads (id,title,source,cwd)')
                connection.execute('insert into threads values (?,?,?,?)', ('same', 'Exact native title', 'cli', '/work'))
                connection.commit()
            parser = SimpleNamespace(codex_home_rollouts=lambda _: [str(one), str(two)], _parse_rollout=parse)
            with patch.object(fw, 'atlas_parser', return_value=(parser, 'v1')):
                docs, coverage = fw.refresh(root, home, cache, root / 'archive')
                self.assertEqual(len(docs), 2)
                actual = next(d for d in docs if d['id'] == 'same')
                self.assertEqual(actual['title'], 'Exact native title')
                self.assertEqual(len(actual['segments']), 1)
                self.assertEqual(coverage['parsed'], 3)
                _, coverage = fw.refresh(root, home, cache, root / 'archive')
                self.assertEqual(coverage['reused'], 3)
                one.write_text('changed')
                _, coverage = fw.refresh(root, home, cache, root / 'archive')
                self.assertEqual(coverage['parsed'], 1)
                (cache / 'search.json').write_text('[]')
                _, coverage = fw.refresh(root, home, cache, root / 'archive')
                self.assertEqual(coverage['parsed'], 3)
            self.assertEqual((cache / 'search.json').stat().st_mode & 0o777, 0o600)


if __name__ == '__main__':
    unittest.main()

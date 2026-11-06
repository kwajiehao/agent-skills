from copy import deepcopy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('work_status', Path(__file__).parents[1] / 'scripts/work_status.py')
ws = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ws)


def pr():
    return {'number': 1, 'title': '<script>bad</script>', 'url': 'https://github.com/a/b/pull/1',
            'isDraft': True, 'headRefOid': 'head', 'baseRefOid': 'base',
            'reviewDecision': 'REVIEW_REQUIRED', 'mergeStateStatus': 'BLOCKED',
            'repository': {'nameWithOwner': 'a/b'},
            'commits': {'nodes': [{'commit': {'oid': 'head', 'statusCheckRollup': {
                'contexts': {'pageInfo': {'hasNextPage': False}, 'nodes': [
                    {'name': 'test', 'status': 'COMPLETED', 'conclusion': 'SUCCESS', 'detailsUrl': None}]}}}}]},
            'reviewThreads': {'pageInfo': {'hasNextPage': False}, 'nodes': []}}


class StatusTests(unittest.TestCase):
    def test_backup_fresh_failed_stale_missing_and_old_failure(self):
        point = {'backup_id': 'a' * 32, 'backup_time': '2026-11-06T00:00:00Z', 'completed_at': '2026-11-06T01:00:00Z'}
        instant = datetime(2026, 11, 7, tzinfo=timezone.utc)
        self.assertEqual(ws.classify_backup(point, None, instant, 48)['state'], 'fresh')
        self.assertEqual(ws.classify_backup(point, None, instant, 20)['state'], 'stale')
        failure = {'backup_id': 'b' * 32, 'failed_at': '2026-11-06T02:00:00Z'}
        self.assertEqual(ws.classify_backup(point, failure, instant, 48)['state'], 'failed')
        failure['failed_at'] = '2026-11-05T02:00:00Z'
        self.assertEqual(ws.classify_backup(point, failure, instant, 48)['state'], 'fresh')
        self.assertEqual(ws.classify_backup(None, failure, instant, 48)['state'], 'unknown')

    def test_latest_manifest_ignores_payload_keys_and_rejects_identity_mismatch(self):
        storage = {'prefix': 'lance-v1', 'bucket': 'fixture', 'endpoint': 'https://example.r2.cloudflarestorage.com'}
        generation, backup_id = 'a' * 32, 'b' * 32
        key = f'lance-v1/videos/{generation}/snapshots/{backup_id}/manifest.json'
        point = {'format': 'lance-v1', 'table': 'videos', 'generation': generation, 'backup_id': backup_id,
                 'backup_time': '2026-11-06T00:00:00Z', 'completed_at': '2026-11-06T01:00:00Z'}
        def runner(argv, **kwargs):
            text = json.dumps(point)
            if 'list-objects-v2' in argv:
                return json.dumps({'Contents': [{'Key': key, 'LastModified': point['completed_at'], 'Size': len(text)},
                                               {'Key': key + '/payload', 'LastModified': point['completed_at'], 'Size': 1}]})
            self.assertIn('get-object', argv)
            Path(argv[-1]).write_text(text)
            return '{}'
        with patch.object(ws, 'run', side_effect=runner):
            self.assertEqual(ws.latest_point(storage, 'videos', generation, 'r2-backup-restore')['backup_id'], backup_id)
            point['table'] = 'other'
            with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                ws.latest_point(storage, 'videos', generation, 'r2-backup-restore')

    def test_pr_head_change_and_truncation_cannot_be_green(self):
        value = pr()
        self.assertEqual(ws.summarize_pr(value)['ci'], 'pass')
        value['headRefOid'] = 'new-head'
        self.assertEqual(ws.summarize_pr(value)['ci'], 'unknown')
        value = pr(); value['reviewThreads']['pageInfo']['hasNextPage'] = True
        self.assertEqual(ws.summarize_pr(value)['ci'], 'incomplete')
        self.assertFalse(ws.summarize_pr(value)['complete'])

    def test_failure_pending_and_outdated_unresolved_threads(self):
        value = pr()
        check = value['commits']['nodes'][0]['commit']['statusCheckRollup']['contexts']['nodes'][0]
        check['conclusion'] = 'FAILURE'
        self.assertEqual(ws.summarize_pr(value)['ci'], 'fail')
        check['status'] = 'IN_PROGRESS'
        self.assertEqual(ws.summarize_pr(value)['ci'], 'pending')
        value['reviewThreads']['nodes'] = [{'isResolved': False, 'isOutdated': True,
            'path': 'file.py', 'line': None, 'comments': {'nodes': [{'url': 'https://github.com/a/b', 'author': None}]}}]
        summary = ws.summarize_pr(value)
        self.assertEqual(len(summary['unresolved_threads']), 1)
        self.assertTrue(summary['draft'])
        self.assertEqual(summary['review_decision'], 'REVIEW_REQUIRED')

    def test_cron_is_data_ambiguous_or_changed_entry_point_is_rejected(self):
        home = '/home/test'
        root = home + '/.local/share/offsite-backup/releases/' + 'a' * 40
        cron = '# BEGIN ami-offsite-backup-nebius\n17 * * * * cd ' + root + ' && ' + root + '/devops/offsite_backup/.venv/bin/python -m devops.offsite_backup submit /home/test/.config/offsite-backup/backup.yaml\n# END ami-offsite-backup-nebius'
        self.assertEqual(ws.deployed_release(cron, home)[:2], (root, home + '/.config/offsite-backup/backup.yaml'))
        for bad in (cron.replace('submit', 'run'), cron + cron, cron.replace('a' * 40 + '/devops', 'b' * 40 + '/devops')):
            with self.assertRaises(ValueError):
                ws.deployed_release(bad, home)

    def test_errors_replace_old_health_and_other_collectors_continue(self):
        with patch.object(ws, 'backup_status', side_effect=RuntimeError('nb: network/access failure')), patch.object(ws, 'pr_status', return_value={'state': 'observed', 'observed_at': 'now', 'prs': [], 'reported_count': 0, 'scope': 'fixture'}):
            report = ws.collect({})
        self.assertEqual(report['collectors']['backup']['state'], 'unknown')
        self.assertEqual(report['collectors']['prs']['state'], 'observed')
        self.assertIn('Collection failed', ws.render(report))

    def test_graphql_partial_errors_do_not_become_success(self):
        with self.assertRaises(ValueError):
            ws.checked_json('{"data":{},"errors":[{"message":"forbidden"}]}')

    def test_deadline_diagnostics_do_not_misclassify_echoed_code_as_auth(self):
        failure = subprocess.CompletedProcess(['nb'], 142, '',
            'credentials profile in echoed command\nwork-status-stage: verification-receipts\n')
        with patch.object(ws.subprocess, 'run', return_value=failure):
            with self.assertRaisesRegex(RuntimeError, 'remote observer deadline exceeded; last stage verification-receipts'):
                ws.run(['nb'])
        timeout = subprocess.TimeoutExpired(['nb'], 180, stderr=b'work-status-stage: imports\n')
        with patch.object(ws.subprocess, 'run', side_effect=timeout):
            with self.assertRaisesRegex(RuntimeError, 'exceeded 180s; last stage imports'):
                ws.run(['nb'], timeout=180)

    def test_ledger_only_reports_explicit_header_comparison(self):
        value = ws.summarize_pr(pr()); value['head'] = 'abcdef0' + '1' * 33
        with tempfile.TemporaryDirectory() as directory, patch.object(ws.Path, 'home', return_value=Path(directory)):
            self.assertIn('not found', ws.ledger_evidence(value)['state'])
            path = Path(directory) / '.agents/reviews/a-b/pr-1.md'
            path.parent.mkdir(parents=True)
            path.write_text('Base / head: 1111111 / abcdef0\n')
            self.assertEqual(ws.ledger_evidence(value)['state'], 'header mentions current head')
            path.write_text('Base / head: 1111111 / 2222222\nFollow-up: abcdef0\n')
            self.assertEqual(ws.ledger_evidence(value)['state'], 'header head differs')

    def test_search_pagination_and_html_escaping(self):
        value = pr()
        def page(nodes, more, cursor):
            return json.dumps({'data': {'search': {'nodes': nodes, 'issueCount': 2, 'pageInfo': {'hasNextPage': more, 'endCursor': cursor}}}})
        other = deepcopy(value); other['url'] += '2'; other['number'] = 2
        with patch.object(ws, 'run', side_effect=[page([value], True, 'c'), page([other], False, None)]) as runner:
            status = ws.pr_status({'author': 'test'})
        self.assertTrue(status['complete'])
        self.assertIn('after=c', runner.call_args.args[0])
        rendered = ws.render({'observed_at': 'now', 'collectors': {'prs': status}})
        self.assertNotIn('<script>bad</script>', rendered)
        self.assertIn('&lt;script&gt;bad', rendered)

    def test_reports_are_private_and_atomically_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report/latest.json'
            ws.atomic_write(path, '{"state":"fresh"}')
            ws.atomic_write(path, '{"state":"unknown"}')
            self.assertEqual(json.loads(path.read_text())['state'], 'unknown')
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(list(path.parent.glob('.work-status-*')), [])


if __name__ == '__main__':
    unittest.main()

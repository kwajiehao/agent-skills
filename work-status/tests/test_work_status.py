from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
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

    def test_pr_collection_failure_reports_unknown_and_history_refresh_continues(self):
        history = {'state': 'refreshed', 'observed_at': 'now', 'atlas': 'index.html',
                   'lookup': {'sources': 1}}
        failure = RuntimeError('gh: network/access failure')
        with patch.object(ws, 'pr_status', side_effect=failure), patch.object(ws, 'refresh_history', return_value=history):
            report = ws.collect({}, refresh=True)
        self.assertEqual(report['collectors']['prs']['state'], 'unknown')
        self.assertEqual(report['collectors']['history']['state'], 'refreshed')
        self.assertIn('Collection failed', ws.render(report))

    def test_history_refresh_uses_configured_archive_for_lookup_and_atlas(self):
        atlas = Path('/work/atlas')
        archive = Path('/data/history')
        with patch.object(ws, 'run', side_effect=['{"coverage":{"sources":1}}', '']) as runner:
            status = ws.refresh_history({'atlas_root': str(atlas), 'atlas_archive': str(archive)}, Path('/reports'))
        lookup, generate = [call.args[0] for call in runner.call_args_list]
        self.assertEqual(lookup[lookup.index('--archive-root') + 1], archive)
        self.assertEqual(generate[generate.index('--archive') + 1], archive)
        self.assertEqual(status['state'], 'refreshed')

    def test_graphql_partial_errors_do_not_become_success(self):
        with self.assertRaises(ValueError):
            ws.checked_json('{"data":{},"errors":[{"message":"forbidden"}]}')

    def test_command_timeout_reports_only_command_and_deadline(self):
        timeout = subprocess.TimeoutExpired(['gh'], 180, stderr=b'private diagnostic')
        with patch.object(ws.subprocess, 'run', side_effect=timeout):
            with self.assertRaises(RuntimeError) as error:
                ws.run(['gh'], timeout=180)
        self.assertEqual(str(error.exception), 'gh: exceeded 180s')

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

    def targeted_cli(self, value, ledger_text=None):
        """Exercise the real CLI through a read-only fake gh process."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tool = root / 'gh'
            fixture = {'data': {'repository': {'pullRequest': value}}}
            tool.write_text('#!' + sys.executable + '\nimport json, sys\n'
                'args = sys.argv[1:]\n'
                'assert args[:2] == ["api", "graphql"]\n'
                'assert "--hostname" in args and "github.com" in args\n'
                'assert "owner=a" in args and "name=b" in args and "number=1" in args\n'
                'query = next(x for x in args if x.startswith("query="))\n'
                'assert "pullRequest(number:$number)" in query and "search(query:" not in query\n'
                'print(' + repr(json.dumps(fixture)) + ')\n')
            tool.chmod(0o700)
            config = root / 'config.json'
            config.write_text(json.dumps({'author':'someone-else'}))
            argv = [sys.executable, str(Path(ws.__file__)), '--pr', 'https://github.com/a/b/pull/1',
                    '--config', str(config), '--out', str(root/'out')]
            if ledger_text is not None:
                ledger = root / 'review ledger.md'
                ledger.write_text(ledger_text)
                argv += ['--ledger', str(ledger)]
            result = subprocess.run(argv, text=True, capture_output=True,
                env={**os.environ, 'PATH':str(root)+os.pathsep+os.environ['PATH']}, timeout=15)
            report = json.loads((root/'out/latest.json').read_text())
            page = (root/'out/index.html').read_text()
            self.assertEqual(set(report['collectors']), {'prs'})
            return result.returncode, report['collectors']['prs'], page

    def named_pr(self):
        value = pr()
        value.update(headRefOid='a'*40, baseRefOid='b'*40, state='MERGED',
                     author={'login':'another-author'}, isDraft=False)
        value['commits']['nodes'][0]['commit']['oid'] = 'a'*40
        value['reviewThreads']['nodes'] = [{'id':'thread-1', 'isResolved':True, 'isOutdated':False,
            'path':'driver.py', 'line':9, 'comments':{'nodes':[{'url':value['url']+'#discussion-1', 'author':{'login':'reviewer'}}]}}]
        return value

    def test_named_merged_pr_of_another_author_does_not_use_authored_search(self):
        rc, result, page = self.targeted_cli(self.named_pr())
        self.assertEqual(rc, 0)
        self.assertTrue(result['complete'])
        item = result['prs'][0]
        self.assertEqual((item['author'], item['state']), ('another-author', 'MERGED'))
        self.assertEqual(len(item['review_threads']), 1)
        self.assertIn('Merged', page)

    def test_resolved_discussion_and_unchanged_reviewed_head_do_not_verify_code_fix(self):
        ledger = 'PR: https://github.com/a/b/pull/1\nCurrent reviewed head: `'+'a'*40+'`\nBase: '+'b'*40+'\nR3: open; deadlock reproduced.\n'
        rc, result, page = self.targeted_cli(self.named_pr(), ledger)
        self.assertEqual(rc, 0)
        item = result['prs'][0]
        self.assertEqual(item['unresolved_threads'], [])
        self.assertTrue(item['review_threads'][0]['resolved'])
        self.assertEqual(item['ledger']['head_comparison'], 'unchanged')
        self.assertEqual(item['code_fix_status'], 'unverified by this collector')
        self.assertIn('Code-fix status: unverified', page)
        self.assertIn('Review ledger', page)

    def test_changed_revision_preserves_both_heads_for_focused_review(self):
        ledger = 'PR: https://github.com/a/b/pull/1\nReviewed head: '+'c'*40+'\nBase: '+'b'*40+'\n'
        rc, result, _ = self.targeted_cli(self.named_pr(), ledger)
        self.assertEqual(rc, 0)
        item = result['prs'][0]
        self.assertEqual(item['ledger']['head_comparison'], 'changed')
        self.assertEqual(item['ledger']['header_head'], 'c'*40)
        self.assertEqual(item['head'], 'a'*40)
        self.assertEqual(item['ledger']['base_comparison'], 'unchanged')
        self.assertEqual(item['code_fix_status'], 'unverified by this collector')

    def test_wrong_pr_ledger_is_rejected_instead_of_reusing_its_evidence(self):
        rc, result, _ = self.targeted_cli(self.named_pr(), 'PR: https://github.com/a/b/pull/2\nHead: '+'a'*40+'\n')
        self.assertEqual(rc, 2)
        self.assertEqual(result['state'], 'unknown')
        self.assertIn('requested PR', result['error'])

    def test_unrecognized_ledger_head_and_truncated_threads_remain_unknown_or_incomplete(self):
        value = self.named_pr()
        value['reviewThreads']['pageInfo']['hasNextPage'] = True
        rc, result, _ = self.targeted_cli(value, 'PR: https://github.com/a/b/pull/1\nDetails without an explicit reviewed head.\n')
        self.assertEqual(rc, 2)
        self.assertEqual(result['state'], 'incomplete')
        self.assertEqual(result['prs'][0]['ledger']['head_comparison'], 'unknown')
        self.assertEqual(result['prs'][0]['code_fix_status'], 'unverified by this collector')

    def test_target_parsing_accepts_review_links_and_rejects_other_hosts_and_invalid_numbers(self):
        self.assertEqual(ws.parse_pr_target('a/b#1'), ('a','b',1))
        self.assertEqual(ws.parse_pr_target('https://github.com/a/b/pull/1/files#r9'), ('a','b',1))
        for target in ['https://evil.example/a/b/pull/1','https://github.com@evil.example/a/b/pull/1',
                       'a/b#0', 'a/b#2147483648', '../b#1', 'https://github.com/a/b/issues/1']:
            with self.subTest(target=target), self.assertRaises(ValueError):
                ws.parse_pr_target(target)

    def test_pr_arguments_reject_ledger_without_target_and_unsupported_collector_before_collection(self):
        for args in [['--ledger','missing.md'], ['--pr','a/b#1','--only','backup'], ['--only','backup']]:
            with self.subTest(args=args), patch.object(sys, 'argv', ['work-status',*args]), patch.object(ws,'collect') as collector:
                with self.assertRaises(SystemExit) as error:
                    ws.main()
                self.assertEqual(error.exception.code, 2)
                collector.assert_not_called()


if __name__ == '__main__':
    unittest.main()

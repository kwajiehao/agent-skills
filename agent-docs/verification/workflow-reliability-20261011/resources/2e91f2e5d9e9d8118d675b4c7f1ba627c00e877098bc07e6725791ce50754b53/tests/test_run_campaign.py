"""Behavioral checks for evidence, process lifecycle, and contained real effects."""

import json
import os
from pathlib import Path
import runpy
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RECORDER = ROOT / "scripts" / "run_campaign.py"
FIXTURES = ROOT / "tests" / "fixtures"


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="fuzz-recorder-test-")
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name)
        for name in ("queue_target.py", "fuzz_queue.py"):
            shutil.copyfile(FIXTURES / name, self.repo / name)
        self.plan = {
            "schema_version": 1, "target": "queue", "profile": "smoke",
            "command": [sys.executable, "fuzz_queue.py"], "timeout_seconds": 5,
            "requirements": ["REQ-ONCE", "REQ-REJECTION"],
            "required_scenarios": {"SCN-RETRY": 1},
            "source_files": ["queue_target.py", "fuzz_queue.py"],
            "revisions": {key: "fixture-v1" for key in (
                "product", "harness", "specification", "dependencies", "corpus")},
            "environment": {"TZ": "UTC"},
            "policy": {key: "isolated synthetic test fixture" for key in (
                "authorization", "isolation", "artifact_policy", "owner")},
        }

    def arguments(self, run_name="run"):
        plan_path = self.repo / "plan.json"
        plan_path.write_text(json.dumps(self.plan))
        return [sys.executable, str(RECORDER), "--plan", str(plan_path),
                "--repo", str(self.repo), "--run-dir", str(self.repo / run_name)]

    def execute(self, run_name="run"):
        completed = subprocess.run(self.arguments(run_name), capture_output=True, text=True, timeout=10)
        result_path = self.repo / run_name / "result.json"
        result = json.loads(result_path.read_text()) if result_path.exists() else None
        return completed, result

    def append_adapter(self, code):
        path = self.repo / "fuzz_queue.py"
        path.write_text(path.read_text() + "\n" + code + "\n")

    def test_real_commit_retry_and_invalid_input_rejection_pass(self):
        completed, result = self.execute()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["report"]["scenarios"]["SCN-RETRY"]["checked"], 5)
        self.assertEqual(result["report"]["oracle_checks"]["REQ-REJECTION"], 4)
        self.assertEqual(list((self.repo / "run").glob("queue-case-*")), [])

    def test_seeded_duplicate_effect_is_retained_as_finding(self):
        target = self.repo / "queue_target.py"
        target.write_text(target.read_text().replace(
            "INSERT OR IGNORE INTO effects VALUES (?, 1)",
            "INSERT INTO effects VALUES (?, 1) ON CONFLICT(job_id) DO UPDATE SET applications = applications + 1",
        ))
        completed, result = self.execute()
        self.assertEqual(completed.returncode, 1, completed.stderr)
        case = json.loads((self.repo / "run" / result["report"]["findings"][0]["artifact"]).read_text())
        self.assertEqual((case["expected"], case["observed"]), (1, 2))
        replay = '''
import json, sys, tempfile
from pathlib import Path
from queue_target import initialize, deliver, applications
case = json.loads(Path(sys.argv[1]).read_text())
with tempfile.TemporaryDirectory() as directory:
    database = Path(directory) / "replay.sqlite"
    initialize(database)
    for event in case["trace"]:
        if event.get("action") in ("deliver", "retry"):
            try:
                deliver(database, event["job"], event.get("lose_ack", False))
            except TimeoutError:
                pass
    assert applications(database, case["trace"][0]["job"]) == case["observed"]
'''
        replayed = subprocess.run(
            [sys.executable, "-c", replay, str(self.repo / "run" / "F-0.json")],
            cwd=self.repo / "run" / "source", capture_output=True, text=True, timeout=5,
        )
        self.assertEqual(replayed.returncode, 0, replayed.stderr)

    def test_planned_but_unobserved_scenario_is_not_success(self):
        self.append_adapter('report["scenarios"]["SCN-RETRY"].update(observed=0, checked=0)\n(run_dir / "report.json").write_text(json.dumps(report))')
        completed, result = self.execute()
        self.assertEqual(completed.returncode, 2)
        self.assertIn("scenario:SCN-RETRY", result["coverage_gaps"])

    def test_unexecuted_required_oracle_is_not_success(self):
        self.plan["requirements"].append("REQ-RECOVERY")
        completed, result = self.execute()
        self.assertEqual(completed.returncode, 2)
        self.assertIn("oracle:REQ-RECOVERY", result["coverage_gaps"])

    def test_missing_report_is_not_success(self):
        self.plan["command"] = [sys.executable, "-c", "pass"]
        completed, result = self.execute()
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(result["status"], "harness_error")

    def test_malformed_counter_is_not_success(self):
        self.append_adapter('report["scenarios"]["SCN-RETRY"]["checked"] = 100\n(run_dir / "report.json").write_text(json.dumps(report))')
        completed, result = self.execute()
        self.assertEqual(completed.returncode, 3)

    def test_scenario_histories_cannot_exceed_executed_cases(self):
        for checked in (100, 1):
            with self.subTest(checked=checked):
                self.plan["required_scenarios"]["SCN-RETRY"] = checked
                self.append_adapter(
                    'report["cases"] = 1\n'
                    f'report["scenarios"]["SCN-RETRY"].update(generated=100, observed=100, checked={checked})\n'
                    '(run_dir / "report.json").write_text(json.dumps(report))'
                )
                completed, result = self.execute(f"run-{checked}")
                self.assertEqual(completed.returncode, 3, completed.stderr)
                self.assertEqual(result["status"], "harness_error")
                self.assertIn("executed cases", " ".join(result["diagnostics"]))

    def test_overlapping_scenarios_and_unexecuted_generation_are_allowed(self):
        self.plan["required_scenarios"]["SCN-OVERLAP"] = 5
        self.append_adapter(
            'report["scenarios"]["SCN-OVERLAP"] = {"generated": 100, "observed": 5, "checked": 5}\n'
            '(run_dir / "report.json").write_text(json.dumps(report))'
        )
        completed, result = self.execute()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(result["status"], "completed")
        self.assertGreater(sum(s["checked"] for s in result["report"]["scenarios"].values()),
                           result["report"]["cases"])

    def test_nonfinite_native_metrics_leave_valid_terminal_evidence(self):
        for index, token in enumerate(("NaN", "Infinity", "-Infinity", "1e9999", "-1e9999")):
            with self.subTest(token=token):
                suffix = ', "native_metrics": {"nested": [' + token + ']}}'
                self.append_adapter(
                    f'(run_dir / "report.json").write_text(json.dumps(report)[:-1] + {suffix!r})'
                )
                completed, result = self.execute(f"run-{index}")
                self.assertEqual(completed.returncode, 3, completed.stderr)
                self.assertEqual(result["status"], "harness_error")
                self.assertIsNone(result["report"])
                self.assertIn("finite", " ".join(result["diagnostics"]))
                self.assertIn(token, (self.repo / f"run-{index}" / "report.json").read_text())

    def test_native_metric_nesting_is_bounded(self):
        # The report's root object is level 1; arrays add one level each.
        for depth in (63, 64, 1500, 10000):
            with self.subTest(array_depth=depth):
                suffix = ', "native_metrics": ' + '[' * depth + '0' + ']' * depth + '}'
                self.append_adapter(
                    f'(run_dir / "report.json").write_text(json.dumps(report)[:-1] + {suffix!r})'
                )
                completed, result = self.execute(f"run-{depth}")
                if depth == 63:
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    self.assertEqual(result["status"], "completed")
                else:
                    self.assertEqual(completed.returncode, 3, completed.stderr)
                    self.assertEqual(result["status"], "harness_error")
                    self.assertIsNone(result["report"])
                    self.assertIn("nesting", " ".join(result["diagnostics"]))
                    self.assertTrue((self.repo / f"run-{depth}" / "report.json").is_file())

    def test_finite_extra_native_metrics_are_retained(self):
        self.append_adapter(
            'report["native_metrics"] = {"mean": 1.25, "nested": [None, True, {"label": "retry"}]}\n'
            '(run_dir / "report.json").write_text(json.dumps(report))'
        )
        completed, result = self.execute()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(result["report"]["native_metrics"],
                         {"mean": 1.25, "nested": [None, True, {"label": "retry"}]})

    def test_duplicate_report_keys_cannot_hide_a_finding(self):
        for index, key in enumerate(('"findings"', '"find\\u0069ngs"')):
            with self.subTest(key=key):
                suffix = ', ' + key + ': []}'
                self.append_adapter(
                    '(run_dir / "case.json").write_text("retained failing input")\n'
                    'report["findings"] = [{"id": "F-duplicate", "artifact": "case.json"}]\n'
                    f'(run_dir / "report.json").write_text(json.dumps(report)[:-1] + {suffix!r})'
                )
                completed, result = self.execute(f"run-{index}")
                self.assertEqual(completed.returncode, 3, completed.stderr)
                self.assertEqual(result["status"], "harness_error")
                self.assertIsNone(result["report"])
                self.assertIn("duplicate", " ".join(result["diagnostics"]))
                self.assertIn("F-duplicate", (self.repo / f"run-{index}" / "report.json").read_text())
                self.assertTrue((self.repo / f"run-{index}" / "case.json").is_file())

    def test_nested_duplicate_report_keys_are_rejected(self):
        suffix = ', "native_metrics": {"samples": [{"count": 0, "count": 9}]}}'
        self.append_adapter(
            f'(run_dir / "report.json").write_text(json.dumps(report)[:-1] + {suffix!r})'
        )
        completed, result = self.execute()
        self.assertEqual(completed.returncode, 3, completed.stderr)
        self.assertEqual(result["status"], "harness_error")
        self.assertIsNone(result["report"])
        self.assertIn("duplicate", " ".join(result["diagnostics"]))

    def test_duplicate_profile_keys_are_rejected_before_execution(self):
        arguments = self.arguments()
        plan_path = self.repo / "plan.json"
        plan_path.write_text(plan_path.read_text()[:-1] + ', "timeout_seconds": 1}')
        completed = subprocess.run(arguments, capture_output=True, text=True, timeout=10)
        self.assertEqual(completed.returncode, 3, completed.stderr)
        self.assertIn("duplicate", completed.stderr)
        self.assertFalse((self.repo / "run").exists())

    def test_unrepresentable_timeout_is_a_configuration_error(self):
        self.plan["timeout_seconds"] = 10 ** 400
        completed, result = self.execute()
        self.assertEqual(completed.returncode, 3, completed.stderr)
        self.assertIn("timeout_seconds", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertIsNone(result)
        self.assertFalse((self.repo / "run").exists())

    def test_profile_schema_version_must_be_integer_one(self):
        for index, version in enumerate((True, 1.0, "1", None, 2)):
            with self.subTest(version=version):
                self.plan["schema_version"] = version
                completed, result = self.execute(f"run-{index}")
                self.assertEqual(completed.returncode, 3, completed.stderr)
                self.assertIsNone(result)
                self.assertFalse((self.repo / f"run-{index}").exists())

    def test_report_schema_version_must_be_integer_one(self):
        for index, version in enumerate((True, 1.0, "1", None, 2)):
            with self.subTest(version=version):
                self.append_adapter(
                    f'report["schema_version"] = {version!r}\n'
                    '(run_dir / "report.json").write_text(json.dumps(report))'
                )
                completed, result = self.execute(f"run-{index}")
                self.assertEqual(completed.returncode, 3, completed.stderr)
                self.assertEqual(result["status"], "harness_error")
                self.assertIn("schema_version", " ".join(result["diagnostics"]))

    def test_finding_must_retain_its_case(self):
        self.append_adapter('report["findings"] = [{"id": "F-lost", "artifact": "missing.json"}]\n(run_dir / "report.json").write_text(json.dumps(report))')
        completed, result = self.execute()
        self.assertEqual(completed.returncode, 3)

    def finding_with_worker_cleanup(self, delete_artifact):
        worker = f'''
import os, signal, sys, time
from pathlib import Path
run_dir = Path(os.environ["FUZZ_RUN_DIR"])
def cleanup(*args):
    if {delete_artifact!r}:
        (run_dir / "case.json").unlink()
    (run_dir / "worker-cleaned").touch()
    sys.exit(0)
signal.signal(signal.SIGTERM, cleanup)
(run_dir / "worker-ready").touch()
time.sleep(5)
'''
        self.append_adapter(f'''
import subprocess, sys, time
(run_dir / "case.json").write_text(json.dumps({{"input": "retry", "failure": "duplicate effect"}}))
subprocess.Popen([sys.executable, "-c", {worker!r}])
deadline = time.monotonic() + 2
while not (run_dir / "worker-ready").exists() and time.monotonic() < deadline:
    time.sleep(0.01)
assert (run_dir / "worker-ready").exists()
report["findings"] = [{{"id": "F-cleanup", "artifact": "case.json"}}]
(run_dir / "report.json").write_text(json.dumps(report))
''')
        completed, result = self.execute()
        self.assertTrue((self.repo / "run" / "worker-cleaned").is_file())
        self.assertEqual((self.repo / "run" / "case.json").exists(), not delete_artifact)
        return completed, result

    def test_finding_removed_by_worker_cleanup_is_an_evidence_error(self):
        completed, result = self.finding_with_worker_cleanup(delete_artifact=True)
        self.assertEqual(completed.returncode, 3, completed.stderr)
        self.assertEqual(result["status"], "harness_error")
        self.assertIn("case.json", " ".join(result["diagnostics"]))
        self.assertEqual(result["report"]["findings"][0]["id"], "F-cleanup")

    def test_finding_retained_after_worker_cleanup_remains_a_finding(self):
        completed, result = self.finding_with_worker_cleanup(delete_artifact=False)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertEqual(result["status"], "findings")
        self.assertEqual(result["diagnostics"], [])

    def test_report_updates_during_worker_cleanup_are_not_lost(self):
        updates = {
            "error": ('report["harness_errors"].append("observer failed during cleanup")', 3, "harness_error"),
            "finding": (
                '(run_dir / "late-case.json").write_text("retained failing input"); '
                'report["findings"].append({"id": "F-late", "artifact": "late-case.json"})',
                1, "findings",
            ),
            "gap": ('report["oracle_checks"]["REQ-ONCE"] = 0', 2, "coverage_gap"),
        }
        for name, (update, exit_code, status) in updates.items():
            with self.subTest(update=name):
                worker = f'''
import json, os, signal, sys, time
from pathlib import Path
run_dir = Path(os.environ["FUZZ_RUN_DIR"])
def cleanup(*args):
    report = json.loads((run_dir / "report.json").read_text())
    {update}
    (run_dir / "report.json").write_text(json.dumps(report))
    (run_dir / "worker-cleaned").touch()
    sys.exit(0)
signal.signal(signal.SIGTERM, cleanup)
(run_dir / "worker-ready").touch()
time.sleep(5)
'''
                # Each run gets exactly one worker, not the previous subtest's code.
                shutil.copyfile(FIXTURES / "fuzz_queue.py", self.repo / "fuzz_queue.py")
                self.append_adapter(f'''
import subprocess, sys, time
subprocess.Popen([sys.executable, "-c", {worker!r}])
deadline = time.monotonic() + 2
while not (run_dir / "worker-ready").exists() and time.monotonic() < deadline:
    time.sleep(0.01)
assert (run_dir / "worker-ready").exists()
''')
                completed, result = self.execute(f"run-{name}")
                run_dir = self.repo / f"run-{name}"
                self.assertTrue((run_dir / "worker-cleaned").is_file())
                self.assertEqual(completed.returncode, exit_code, completed.stderr)
                self.assertEqual(result["status"], status)
                self.assertEqual(result["report"], json.loads((run_dir / "report.json").read_text()))

    def test_timeout_retains_available_report_without_claiming_completion(self):
        self.plan["timeout_seconds"] = 0.5
        self.append_adapter(
            'report["harness_errors"].append("incomplete observer output")\n'
            '(run_dir / "report.json").write_text(json.dumps(report))\n'
            'import time; time.sleep(5)'
        )
        completed, result = self.execute()
        self.assertEqual(completed.returncode, 4, completed.stderr)
        self.assertEqual(result["status"], "timed_out")
        self.assertEqual(result["report"]["harness_errors"], ["incomplete observer output"])

    def test_nonzero_command_cannot_claim_clean_success(self):
        self.append_adapter("raise SystemExit(7)")
        completed, result = self.execute()
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(result["command_exit_code"], 7)

    def test_selected_uncommitted_bytes_are_captured_and_source_drift_fails(self):
        original = (self.repo / "queue_target.py").read_bytes()
        self.append_adapter('Path("queue_target.py").write_text("# changed during run")')
        completed, result = self.execute()
        self.assertEqual(completed.returncode, 3)
        self.assertEqual((self.repo / "run" / "source" / "queue_target.py").read_bytes(), original)
        self.assertEqual(result["source_changed"], ["queue_target.py"])

    def test_run_directory_cannot_be_overwritten(self):
        completed, result = self.execute()
        original = (self.repo / "run" / "manifest.json").read_bytes()
        repeated, _ = self.execute()
        self.assertEqual(repeated.returncode, 3)
        self.assertEqual((self.repo / "run" / "manifest.json").read_bytes(), original)

    def test_timeout_records_incomplete_execution(self):
        self.plan["timeout_seconds"] = 0.15
        self.plan["command"] = [sys.executable, "-c", "import time; time.sleep(30)"]
        completed, result = self.execute()
        self.assertEqual(completed.returncode, 4, (completed.stderr, result))
        self.assertEqual(result["status"], "timed_out")

    def test_sigterm_records_interruption_and_stops_child(self):
        self.plan["command"] = [sys.executable, "-c", "import time; time.sleep(30)"]
        process = subprocess.Popen(self.arguments(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(lambda: process.kill() if process.poll() is None else None)
        process_path = self.repo / "run" / "process.json"
        deadline = time.monotonic() + 4
        while not process_path.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertTrue(process_path.exists())
        child = json.loads(process_path.read_text())["pid"]
        process.send_signal(signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 5, (stdout, stderr))
        result = json.loads((self.repo / "run" / "result.json").read_text())
        self.assertEqual(result["status"], "interrupted")
        with self.assertRaises(ProcessLookupError):
            os.kill(child, 0)

    def test_ambient_secret_not_inherited(self):
        self.append_adapter('assert "FUZZ_TEST_SECRET" not in os.environ')
        with mock.patch.dict(os.environ, {"FUZZ_TEST_SECRET": "synthetic-secret-sentinel"}):
            completed, result = self.execute()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertNotIn("synthetic-secret-sentinel", (self.repo / "run" / "manifest.json").read_text())

    def test_output_is_bounded(self):
        self.append_adapter('print("x" * (2 * 1024 * 1024))')
        completed, result = self.execute()
        self.assertEqual(completed.returncode, 0)
        self.assertTrue(result["log_truncated"])
        self.assertEqual((self.repo / "run" / "output.log").stat().st_size, 1024 * 1024)

    def test_source_cannot_escape_by_symlink(self):
        (self.repo / "link.py").symlink_to(self.repo / "queue_target.py")
        self.plan["source_files"].append("link.py")
        completed, result = self.execute()
        self.assertEqual(completed.returncode, 3)
        self.assertIsNone(result)
        self.assertFalse((self.repo / "run").exists())


class EvidenceWriterTests(unittest.TestCase):
    def setUp(self):
        self.api = runpy.run_path(str(RECORDER))
        self.temporary = tempfile.TemporaryDirectory(prefix="fuzz-writer-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.destination = self.directory / "result.json"

    def test_serialization_failure_does_not_publish_a_partial_record(self):
        with self.assertRaises(ValueError):
            self.api["write_new"](self.destination, {"metric": float("nan")})
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_record_is_complete_before_publication_and_never_replaced(self):
        record = {"status": "completed", "report": {"cases": 1}}
        real_link = os.link

        def publish(source, destination):
            self.assertFalse(Path(destination).exists())
            self.assertEqual(json.loads(Path(source).read_text()), record)
            real_link(source, destination)

        with mock.patch.object(self.api["os"], "link", side_effect=publish) as link:
            self.api["write_new"](self.destination, record)
        link.assert_called_once()
        original = self.destination.read_bytes()
        with self.assertRaises(FileExistsError):
            self.api["write_new"](self.destination, {"status": "harness_error"})
        self.assertEqual(self.destination.read_bytes(), original)
        self.assertEqual(list(self.directory.iterdir()), [self.destination])

    def test_write_failure_does_not_publish_a_partial_record(self):
        with mock.patch.object(self.api["os"], "fsync", side_effect=OSError("injected write failure")):
            with self.assertRaises(OSError):
                self.api["write_new"](self.destination, {"status": "completed"})
        self.assertEqual(list(self.directory.iterdir()), [])


if __name__ == "__main__":
    unittest.main()

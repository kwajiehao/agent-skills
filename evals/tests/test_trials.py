"""Behavioral grading regressions; these are grader fixtures, not agent trials."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).parents[1] / "run_evals.py"
SPEC = importlib.util.spec_from_file_location("run_evals", MODULE)
evals = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evals)


class TrialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.evidence = self.root / "trace.txt"
        self.evidence.write_text("Observed commands and output, plus the final answer.\n")
        self.ref = {"path": "trace.txt", "sha256": hashlib.sha256(self.evidence.read_bytes()).hexdigest()}
        self.rubric = {"scenario_id": "sample", "criteria": [
            {"id": "works", "fact": "fixed", "equals": True},
            {"id": "scope", "fact": "scope_violations", "equals": 0},
        ]}
        self.trial = {
            "schema_version": 1, "trial_id": "sample-A-1", "execution_kind": "grader_fixture",
            "scenario_id": "sample", "arm": "A", "repeat": 1, "match_id": "sample-1",
            "fixture_digest": "a" * 64,
            "skill_identity": {"name": "sample", "revision": "test", "digest": "b" * 64},
            "model_identity": {"name": "test-model", "revision": None, "configuration": {}},
            "conditions": {"environment": "local fixture", "permissions": "isolated", "budget": "one turn"},
            "observer": "test assessor", "trace_complete": True, "trace": [self.ref],
            "facts": {"fixed": {"value": True, "evidence": [self.ref]},
                      "scope_violations": {"value": 0, "evidence": [self.ref]}},
            "events": [], "usage": {"latency_seconds": None, "tokens": None},
        }

    def tearDown(self):
        self.temp.cleanup()

    def grade(self, trial=None):
        return evals.grade_trial(trial or self.trial, self.rubric, self.root)

    def test_observed_success_and_failure_are_distinguished(self):
        self.assertTrue(self.grade()["accepted_without_correction"])
        self.trial["facts"]["fixed"]["value"] = False
        self.assertFalse(self.grade()["accepted_without_correction"])
        self.assertEqual(self.grade()["criteria"][0]["status"], "fail")

    def test_missing_criterion_is_unmeasured_not_success(self):
        del self.trial["facts"]["fixed"]
        self.assertIsNone(self.grade()["accepted_without_correction"])
        self.assertEqual(self.grade()["criteria"][0]["status"], "unmeasured")

    def test_evidence_is_required_and_tampering_rejected(self):
        self.evidence.write_text("replaced trace")
        with self.assertRaisesRegex(evals.InvalidTrial, "digest"):
            self.grade()

    def test_traversal_and_symlink_evidence_rejected(self):
        self.trial["facts"]["fixed"]["evidence"][0]["path"] = "../outside.txt"
        with self.assertRaises(evals.InvalidTrial):
            self.grade()
        self.trial["facts"]["fixed"]["evidence"][0] = dict(self.ref, path="link.txt")
        (self.root / "link.txt").symlink_to(self.evidence)
        with self.assertRaises(evals.InvalidTrial):
            self.grade()

    def test_incomplete_trace_does_not_claim_zero_questions(self):
        self.trial["trace_complete"] = False
        result = self.grade()
        self.assertIsNone(result["metrics"]["unnecessary_questions"])
        self.assertIsNone(result["accepted_without_correction"])

    def test_false_completion_and_correction_invalidate_acceptance(self):
        for event in ("false_completion", "human_correction", "scope_violation"):
            with self.subTest(event=event):
                trial = copy.deepcopy(self.trial)
                trial["events"] = [{"type": event, "evidence": [self.ref]}]
                self.assertFalse(self.grade(trial)["accepted_without_correction"])

    def test_recovery_is_unmeasured_without_interruption(self):
        self.assertIsNone(self.grade()["metrics"]["interrupted_recovery"])
        self.trial["events"] = [{"type": "interruption", "evidence": [self.ref]},
                                {"type": "recovered", "evidence": [self.ref]}]
        self.assertTrue(self.grade()["metrics"]["interrupted_recovery"])

    def test_recovery_requires_causal_order_and_complete_trace(self):
        self.trial["events"] = [{"type": "recovered", "evidence": [self.ref]},
                                {"type": "interruption", "evidence": [self.ref]}]
        self.assertFalse(self.grade()["metrics"]["interrupted_recovery"])
        self.trial["trace_complete"] = False
        self.assertIsNone(self.grade()["metrics"]["interrupted_recovery"])

    def test_unknown_tokens_and_latency_stay_unknown(self):
        self.assertIsNone(self.grade()["metrics"]["tokens"])
        self.assertIsNone(self.grade()["metrics"]["latency_seconds"])

    def test_bool_is_not_accepted_as_a_count(self):
        self.trial["facts"]["scope_violations"]["value"] = False
        self.assertEqual(self.grade()["criteria"][1]["status"], "fail")

    def test_nested_boolean_is_not_accepted_as_a_numeric_observation(self):
        self.rubric["criteria"][0]["equals"] = {"count": 0}
        self.trial["facts"]["fixed"]["value"] = {"count": False}
        self.assertEqual(self.grade()["criteria"][0]["status"], "fail")

    def test_each_interruption_needs_its_own_recovery(self):
        self.trial["events"] = [{"type": kind, "evidence": [self.ref]} for kind in
                                ("interruption", "interruption", "recovered")]
        self.assertFalse(self.grade()["metrics"]["interrupted_recovery"])

    def test_script_fixtures_never_enter_behavioral_comparison(self):
        result = self.grade()
        self.assertEqual(evals.summarize([result])["agent_trials"], 0)
        self.assertEqual(evals.summarize([result])["grader_fixtures"], 1)

    def archive(self):
        (self.root / "trial.json").write_text(json.dumps(self.trial))
        return evals.verify_archive(self.root, ["sample"], {"sample": self.rubric})

    def test_archive_verification_keeps_partial_trace_metrics_unknown(self):
        self.trial.update(execution_kind="actual_agent", trace_complete=False)
        summary = self.archive()
        self.assertEqual(summary["agent_trials"], 1)
        self.assertIsNone(summary["by_arm"]["A"]["metrics"]["human_corrections"]["mean"])

    def test_archive_verification_rejects_fixture_only_and_failed_records(self):
        with self.assertRaises(evals.InvalidTrial):
            self.archive()
        self.trial["execution_kind"] = "actual_agent"
        self.trial["facts"]["fixed"]["value"] = False
        with self.assertRaises(evals.InvalidTrial):
            self.archive()

    def test_archive_verification_requires_requested_scenario_and_actual_evidence(self):
        self.trial["execution_kind"] = "actual_agent"
        self.archive()
        with self.assertRaises(evals.InvalidTrial):
            evals.verify_archive(self.root, ["other"], {"sample": self.rubric})
        self.evidence.write_text("drifted evidence")
        with self.assertRaises(evals.InvalidTrial):
            self.archive()

    def test_matched_arms_require_same_fixture_model_conditions_repeat(self):
        a = copy.deepcopy(self.trial)
        a.update(execution_kind="actual_agent", trial_id="A", arm="A")
        b = copy.deepcopy(a)
        b.update(trial_id="B", arm="B")
        b["skill_identity"]["digest"] = "c" * 64
        paired = [self.grade(a), self.grade(b)]
        self.assertEqual(len(evals.summarize(paired)["matched_pairs"]), 1)
        for field, value in (("fixture_digest", "d" * 64), ("repeat", 2),
                             ("model_identity", {"name": "different", "revision": None, "configuration": {}}),
                             ("conditions", {"environment": "other", "permissions": "isolated", "budget": "one turn"})):
            with self.subTest(field=field):
                changed = copy.deepcopy(b)
                changed[field] = value
                self.assertEqual(evals.summarize([self.grade(a), self.grade(changed)])["matched_pairs"], [])

    def test_duplicate_trial_id_is_not_a_repeat(self):
        with self.assertRaisesRegex(evals.InvalidTrial, "duplicate"):
            evals.summarize([self.grade(), self.grade()])

    def test_prepare_creates_isolated_dirty_fixture_and_stable_digest(self):
        first = self.root / "first"
        second = self.root / "second"
        manifest = evals.prepare_case("core-dirty-worktree", first)
        other = evals.prepare_case("core-dirty-worktree", second)
        self.assertEqual(manifest["fixture_digest"], other["fixture_digest"])
        self.assertEqual((first / "repo" / "notes.txt").read_text(), "My unfinished note.\n")
        self.assertNotIn("criteria", (first / "prompt.md").read_text())
        with self.assertRaises(evals.InvalidTrial):
            evals.prepare_case("core-dirty-worktree", first)


if __name__ == "__main__":
    unittest.main()

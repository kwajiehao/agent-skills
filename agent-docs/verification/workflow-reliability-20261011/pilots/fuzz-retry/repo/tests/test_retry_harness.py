"""Controls validate the tester; expected injected defects are not findings."""
import unittest
from unittest.mock import patch

import retry_fuzz
from store import apply_job


class RetryHarnessControls(unittest.TestCase):
    def test_valid_single_and_lost_ack_commit(self):
        for lost in (False, True):
            result = retry_fuzz.execute({"actions": [
                {"job_id": "control", "amount": 0, "lose_ack": lost}]})
            self.assertEqual(result["violations"], [])
            self.assertEqual(result["trace"][0]["durable_rows"], [("control", 0)])

    def test_unrelated_and_reordered_events_do_not_cover_retry(self):
        cases = [
            [{"job_id": "a", "amount": 1, "lose_ack": True},
             {"job_id": "b", "amount": 2, "lose_ack": False}],
            [{"job_id": "a", "amount": 1, "lose_ack": False},
             {"job_id": "a", "amount": 1, "lose_ack": True}],
        ]
        for actions in cases:
            result = retry_fuzz.execute({"actions": actions})
            self.assertFalse(result["scenario_observed"])
            self.assertFalse(result["scenario_checked"])
            self.assertFalse(retry_fuzz.planned_scenario({"actions": actions}))

    def test_ack_oracle_detects_an_in_memory_seeded_defect(self):
        def missing_timeout(path, job_id, amount, lose_ack=False):
            return apply_job(path, job_id, amount, lose_ack=False)

        # Audit-only control still executes the real insertion/commit; the
        # substitute suppresses exactly the acknowledgement-loss exception.
        with patch("retry_fuzz.apply_job", side_effect=missing_timeout):
            result = retry_fuzz.execute({"actions": [
                {"job_id": "control", "amount": 1, "lose_ack": True}]})
        self.assertEqual([v["requirement"] for v in result["violations"]], ["REQ-002"])
        self.assertFalse(result["scenario_observed"])

    def test_generation_and_replay_are_deterministic(self):
        first = retry_fuzz.generate(20261011)
        self.assertEqual(first, retry_fuzz.generate(20261011))
        self.assertEqual(retry_fuzz.execute(first), retry_fuzz.execute(first))


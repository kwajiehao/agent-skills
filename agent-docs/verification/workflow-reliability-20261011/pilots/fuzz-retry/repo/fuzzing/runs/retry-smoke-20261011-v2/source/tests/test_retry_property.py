import json
from pathlib import Path
import unittest

from retry_fuzz import execute, generate


class RetryPropertyTests(unittest.TestCase):
    def test_generated_retry_histories(self):
        for seed in range(32):
            with self.subTest(seed=seed):
                result = execute(generate(seed))
                self.assertTrue(result["scenario_checked"], result)
                self.assertFalse(result["violations"], json.dumps({
                    "seed": seed, "actions": result["case"]["actions"],
                    "first_violation": result["violations"][:1]}))

    def test_retained_lost_ack_regression(self):
        corpus = Path(__file__).resolve().parents[1] / "fuzzing/corpus/lost-ack-retry.json"
        result = execute(json.loads(corpus.read_text()))
        self.assertTrue(result["scenario_checked"], result)
        self.assertFalse(result["violations"], json.dumps(result["violations"]))

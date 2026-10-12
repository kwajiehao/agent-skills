import tempfile
from pathlib import Path
import unittest
from store import apply_job, effect_count


class StoreTests(unittest.TestCase):
    def test_single_delivery(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "jobs.sqlite"
            apply_job(path, "job-7", 4)
            self.assertEqual(effect_count(path, "job-7"), 1)

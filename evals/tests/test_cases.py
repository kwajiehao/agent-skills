"""Execute raw project fixtures to establish controls before agent trials."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location("run_evals", Path(__file__).parents[1] / "run_evals.py")
evals = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evals)


class CaseControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def prepare(self, name):
        return Path(evals.prepare_case(name, self.root / name)["repo"])

    def command(self, repo, code):
        return subprocess.run(["python3", "-c", code], cwd=repo, text=True, capture_output=True)

    def test_prepare_does_not_copy_runtime_caches_into_raw_projects(self):
        catalog = self.root / "catalog"
        fixture = catalog / "fixtures" / "sample"
        (fixture / "__pycache__").mkdir(parents=True)
        (fixture / "__pycache__" / "source.pyc").write_bytes(b"stale cache")
        (fixture / ".pytest_cache").mkdir()
        (fixture / ".pytest_cache" / "state").write_text("previous execution")
        (fixture / "source.py").write_text("value = 1\n")
        (catalog / "cases.json").write_text(json.dumps([{
            "id": "sample", "fixture": "sample", "skill": "sample",
            "prompt": "Inspect {repo}.",
        }]))
        with mock.patch.object(evals, "HERE", catalog):
            repo = Path(evals.prepare_case("sample", self.root / "clean-trial")["repo"])
        self.assertEqual((repo / "source.py").read_text(), "value = 1\n")
        self.assertFalse((repo / "__pycache__").exists())
        self.assertFalse((repo / ".pytest_cache").exists())

    def test_every_scenario_prepares_and_has_a_matching_hidden_rubric(self):
        cases = json.loads((evals.HERE / "cases.json").read_text())
        rubrics = json.loads((evals.HERE / "rubrics.json").read_text())
        self.assertEqual({case["id"] for case in cases}, {rubric["scenario_id"] for rubric in rubrics})
        self.assertEqual(len(cases), len({case["id"] for case in cases}))
        for case in cases:
            with self.subTest(case=case["id"]):
                repo = self.prepare(case["id"])
                self.assertTrue((repo / ".git").is_dir())
                self.assertFalse((repo / "rubrics.json").exists())

    def test_mature_native_properties_are_real_and_passing(self):
        repo = self.prepare("fuzz-mature-native")
        result = subprocess.run(["python3", "-m", "unittest", "discover", "-s", "tests", "-v"],
                                cwd=repo, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Ran 1 test", result.stderr)

    def test_seeded_retry_defect_has_standalone_red_and_single_delivery_green(self):
        repo = self.prepare("fuzz-seeded-retry")
        common = "import tempfile; from pathlib import Path; from store import apply_job, effect_count\n"
        green = self.command(repo, common +
            "with tempfile.TemporaryDirectory() as d:\n p=Path(d)/'db'; apply_job(p,'x',3); assert effect_count(p,'x') == 1\n")
        self.assertEqual(green.returncode, 0, green.stderr)
        red = self.command(repo, common +
            "with tempfile.TemporaryDirectory() as d:\n"
            " p=Path(d)/'db'\n"
            " try: apply_job(p,'x',3,lose_ack=True)\n"
            " except TimeoutError: pass\n"
            " apply_job(p,'x',3); assert effect_count(p,'x') == 1\n")
        self.assertNotEqual(red.returncode, 0)
        self.assertIn("AssertionError", red.stderr)

    def test_existing_durable_store_test_passes_but_restart_contract_fails(self):
        repo = self.prepare("core-runtime-verifier")
        current = subprocess.run(["python3", "-m", "unittest", "discover", "-s", "tests"],
                                 cwd=repo, text=True, capture_output=True)
        self.assertEqual(current.returncode, 0, current.stderr)
        saved = self.command(repo, "from storage import save_value; save_value('value.json', {'n':7})")
        self.assertEqual(saved.returncode, 0, saved.stderr)
        fresh = self.command(repo, "from storage import load_value; assert load_value('value.json') == {'n':7}")
        self.assertNotEqual(fresh.returncode, 0)
        self.assertIn("AssertionError", fresh.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node is needed to exercise JS dependency fixtures")
    def test_resolved_dependency_versions_have_different_actual_default_behavior(self):
        repo = self.prepare("dep-resolved-default")
        code = "const p=require(process.argv[1]); try {console.log(p.parseNumber('007'))} catch(e) {console.log(e.name)}"
        outputs = []
        for version in ("1.4.0", "1.6.0"):
            package = repo / "evidence" / version / "parse-number"
            result = subprocess.run(["node", "-e", code, str(package)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            outputs.append(result.stdout.strip())
        self.assertEqual(outputs, ["7", "TypeError"])

    def test_walkthrough_draft_is_incorrect_despite_unchanged_head(self):
        repo = self.prepare("walkthrough-source-integrity")
        draft = json.loads((repo / ".walkthrough/draft/notes.json").read_text())
        self.assertNotEqual(draft["excerpts"][0]["code"], (repo / "greeting.py").read_text().rstrip("\n"))
        self.assertEqual(draft["changed_files"], [])
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=repo, text=True)
        self.assertIn("greeting.py", changed)


if __name__ == "__main__":
    unittest.main()

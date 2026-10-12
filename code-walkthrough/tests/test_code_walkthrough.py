"""Exercise source identities for code explanations with and without Git."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SKILL = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SKILL / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load("code_walkthrough_validator", "validate_walkthrough.py")
renderer = load("code_walkthrough_renderer", "render_walkthrough.py")


class CodeSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((SKILL / "assets/example-data.json").read_text())

    def validate(self):
        result = validator.Validation()
        validator.validate_data(self.data, result)
        return result.errors

    def test_supplied_snippet_uses_real_content_digest_without_git_or_remote(self):
        snapshot = self.data["meta"]["snapshot"]
        self.assertEqual(snapshot["sources"][0]["sha256"],
                         hashlib.sha256(self.data["code"][0]["content"].encode()).hexdigest())
        self.assertEqual(self.validate(), [])

    def test_local_files_and_notebook_cells_can_pin_enclosing_source(self):
        self.data["meta"]["snapshot"]["kind"] = "files"
        for path, captured in [("script.py", "script.py"),
                               ("analysis.ipynb#cell-a", "analysis.ipynb")]:
            with self.subTest(path=path):
                self.data["files"][0]["path"] = path
                self.data["code"][0]["path"] = path
                self.data["coverage"]["represented"] = [path]
                self.data["meta"]["snapshot"]["sources"][0]["path"] = captured
                self.assertEqual(self.validate(), [])

    def test_committed_source_accepts_sha1_and_sha256_git_ids(self):
        for size in (40, 64):
            self.data["meta"]["snapshot"] = {
                "kind": "git", "label": "Captured commit", "ref": "main", "sha": "a" * size,
            }
            self.assertEqual(self.validate(), [])

    def test_unpinned_source_and_mutable_git_ref_are_rejected(self):
        self.data["meta"]["snapshot"]["sources"] = []
        self.assertTrue(self.validate())
        self.data["meta"]["snapshot"] = {
            "kind": "git", "label": "Captured commit", "ref": "main", "sha": "main",
        }
        self.assertTrue(self.validate())

    def test_malformed_digest_and_uncovered_source_are_rejected(self):
        original = copy.deepcopy(self.data)
        self.data["meta"]["snapshot"]["sources"][0]["sha256"] = "not-a-digest"
        self.assertTrue(self.validate())
        self.data = original
        self.data["meta"]["snapshot"]["sources"][0]["path"] = "another-source"
        self.assertTrue(self.validate())

    def test_excerpt_cannot_silently_reference_uncatalogued_source(self):
        self.data["code"][0]["path"] = "another-source"
        self.assertTrue(self.validate())

    def test_duplicate_source_identities_are_rejected(self):
        self.data["meta"]["snapshot"]["sources"] *= 2
        self.assertTrue(self.validate())

    def test_render_roundtrip_preserves_exact_snippet_and_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            data_path, output = Path(directory) / "data.json", Path(directory) / "index.html"
            data_path.write_text(json.dumps(self.data))
            renderer.render(data_path, output, SKILL / "assets/walkthrough-template.html")
            result = validator.Validation()
            document = output.read_text()
            validator.validate_html(document, result)
            extracted = validator.extract_data(document, result)
            validator.validate_data(extracted, result)
            self.assertEqual(result.errors, [])
            self.assertEqual(extracted, self.data)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_module("walkthrough_validator", SKILL_DIR / "scripts" / "validate_walkthrough.py")
renderer = load_module("walkthrough_renderer", SKILL_DIR / "scripts" / "render_walkthrough.py")


class WalkthroughValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.example = json.loads((SKILL_DIR / "assets" / "example-data.json").read_text(encoding="utf-8"))

    def validate(self, data):
        result = validator.Validation()
        validator.validate_data(data, result)
        return result

    def test_example_data_satisfies_contract(self) -> None:
        result = self.validate(self.example)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])

    def test_unknown_focus_node_is_rejected(self) -> None:
        data = copy.deepcopy(self.example)
        data["steps"][0]["focus_node_ids"].append("missing-node")
        result = self.validate(data)
        self.assertTrue(any("focuses unknown nodes" in error for error in result.errors))

    def test_incomplete_coverage_is_rejected(self) -> None:
        data = copy.deepcopy(self.example)
        data["coverage"]["represented"].remove("tests/test_retry.py")
        result = self.validate(data)
        self.assertIn("coverage must classify every changed file exactly once", result.errors)

    def test_rendered_html_contains_valid_inline_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_path = Path(directory) / "data.json"
            output_path = Path(directory) / "index.html"
            data_path.write_text(json.dumps(self.example), encoding="utf-8")
            renderer.render(data_path, output_path, SKILL_DIR / "assets" / "walkthrough-template.html")
            document = output_path.read_text(encoding="utf-8")
            result = validator.Validation()
            validator.validate_html(document, result)
            extracted = validator.extract_data(document, result)
            validator.validate_data(extracted, result)
            self.assertEqual(result.errors, [])


if __name__ == "__main__":
    unittest.main()

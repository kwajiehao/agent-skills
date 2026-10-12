import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from storage import save_value, load_value


class StorageTests(unittest.TestCase):
    def test_save_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "sample.json")
            save_value(path, {"count": 7})
            self.assertEqual(load_value(path), {"count": 7})

    def test_missing_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertIsNone(load_value(Path(directory) / "missing.json"))

    def test_path_objects_and_json_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.json"
            for value in [None, False, 0, 2.5, "hello", [1, "two"], {"count": 7}]:
                with self.subTest(value=value):
                    save_value(path, value)
                    self.assertEqual(load_value(path), value)

    def test_survives_process_restart_and_overwrite(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.json"
            for value in [
                {"count": 7, "items": [None, True, 2.5, "hello"]},
                {"count": 8, "nested": {"message": "updated"}},
            ]:
                with self.subTest(value=value):
                    subprocess.run(
                        [sys.executable, "-B", "-c",
                         "import json, sys; from storage import save_value; "
                         "save_value(sys.argv[1], json.loads(sys.argv[2]))",
                         str(path), json.dumps(value)],
                        cwd=repository, check=True, capture_output=True, text=True,
                    )
                    result = subprocess.run(
                        [sys.executable, "-B", "-c",
                         "import json, sys; from storage import load_value; "
                         "print(json.dumps(load_value(sys.argv[1])))", str(path)],
                        cwd=repository, check=True, capture_output=True, text=True,
                    )
                    self.assertEqual(json.loads(result.stdout), value)
                    self.assertEqual(json.loads(path.read_text(encoding="utf-8")), value)

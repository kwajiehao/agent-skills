"""Verify default library storage, explicit overrides and shared gallery behavior."""

import copy
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SKILL = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("library_renderer", SKILL / "scripts/render_walkthrough.py")
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class WalkthroughLibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "library"
        self.template = SKILL / "assets/walkthrough-template.html"
        self.data = json.loads((SKILL / "assets/example-data.json").read_text())
        self.input = self.base / "input.json"
        self.input.write_text(json.dumps(self.data))

    def render(self, output=None, root=None):
        return renderer.render(self.input, output, self.template, root or self.root)

    def test_default_is_shared_home_library_with_self_contained_entry(self):
        with patch.object(renderer.library.Path, "home", return_value=self.base):
            output = renderer.render(self.input, None, self.template)
        root = (self.base / ".agents/walkthroughs").resolve()
        self.assertEqual(output.parents[1], root)
        self.assertTrue(output.is_file())
        self.assertEqual(json.loads((output.parent / "walkthrough-data.json").read_text()), self.data)
        self.assertTrue((output.parent / "preview.svg").is_file())
        self.assertIn(output.parent.name + "/index.html", (root / "index.html").read_text())

    def test_content_and_repository_changes_do_not_overwrite_previous_stories(self):
        first = self.render()
        for url in ("https://github.com/one/project", "https://github.com/two/project"):
            self.data["meta"]["repository_url"] = url
            self.input.write_text(json.dumps(self.data))
            self.assertNotEqual(self.render(), first)
        # Re-rendering the same data updates its existing entry rather than duplicating it.
        self.render()
        self.assertEqual(len(list(self.root.rglob(renderer.library.ENTRY_NAME))), 3)
        self.assertTrue(first.is_file())

    def test_custom_output_outside_library_does_not_touch_global_catalogue(self):
        output = self.base / "requested" / "custom.html"
        self.assertEqual(self.render(output), output)
        self.assertTrue(output.is_file())
        self.assertFalse(self.root.exists())
        self.assertFalse((output.parent / "walkthrough-data.json").exists())

    def test_root_gallery_cannot_be_overwritten_by_an_artifact(self):
        first = self.render()
        original = (self.root / "index.html").read_bytes()
        with self.assertRaisesRegex(ValueError, "reserved"):
            self.render(self.root / "index.html")
        self.assertEqual((self.root / "index.html").read_bytes(), original)
        self.assertTrue(first.is_file())

    def test_gallery_shares_both_types_and_escapes_metadata_and_preview(self):
        first = self.render()
        other = copy.deepcopy(self.data)
        other["meta"]["title"] = '<script>alert("title")</script>'
        other["visuals"][0]["nodes"][0]["label"] = '<script>alert("node")</script>'
        page = self.root / "other & story" / "index.html"
        page.parent.mkdir()
        page.write_text("<html>Other walkthrough</html>")
        renderer.library.register(other, page, "pr" if renderer.KIND == "code" else "code", self.root)
        gallery = (self.root / "index.html").read_text()
        self.assertIn('data-kind="code"', gallery)
        self.assertIn('data-kind="pr"', gallery)
        self.assertIn(first.parent.name + "/index.html", gallery)
        self.assertIn('other%20%26%20story/index.html', gallery)
        self.assertNotIn(other["meta"]["title"], gallery)
        preview = (page.parent / "preview.svg").read_text()
        self.assertIn('&lt;script&gt;', preview)
        self.assertNotIn('<script>', preview)
        self.assertNotIn('https://cdn', gallery)

    def test_simultaneous_renders_keep_every_gallery_entry(self):
        inputs = []
        for i in range(6):
            data = copy.deepcopy(self.data)
            data["meta"]["title"] = f"Parallel story {i}"
            path = self.base / f"input-{i}.json"
            path.write_text(json.dumps(data))
            inputs.append(path)
        with ThreadPoolExecutor(max_workers=6) as pool:
            outputs = list(pool.map(lambda path: renderer.render(path, None, self.template, self.root), inputs))
        gallery = (self.root / "index.html").read_text()
        self.assertEqual(len(set(outputs)), 6)
        for output in outputs:
            self.assertIn(output.parent.name + "/index.html", gallery)
        self.assertFalse(list(self.root.rglob("*.tmp")))

    def test_registration_does_not_follow_an_escaping_symlink(self):
        self.root.mkdir()
        outside = self.base / "outside"
        outside.mkdir()
        link = self.root / "linked"
        link.symlink_to(outside, target_is_directory=True)
        page = outside / "index.html"
        page.write_text("unregistered")
        self.assertIsNone(renderer.library.register(self.data, link / "index.html", renderer.KIND, self.root))
        self.assertFalse((outside / renderer.library.ENTRY_NAME).exists())


if __name__ == "__main__":
    unittest.main()

"""Behavioral regressions use real Git repositories, not mocked source claims."""
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load("validator_source_tests", SKILL / "scripts/validate_walkthrough.py")


class SourceVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Fixture")
        (self.repo / "main.py").write_text("value = 1\nprint(value)\n")
        (self.repo / "other.txt").write_text("before\n")
        self.git("add", ".")
        self.git("commit", "-qm", "base")
        self.base = self.git("rev-parse", "HEAD").strip()
        (self.repo / "main.py").write_text("value = 2\nprint(value)\n")
        (self.repo / "other.txt").write_text("after\n")
        self.git("add", ".")
        self.git("commit", "-qm", "change")
        self.head = self.git("rev-parse", "HEAD").strip()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], text=True)

    def document(self, mode="committed"):
        source = load("walkthrough_sources", SKILL / "scripts/source_evidence.py")
        collected = source.collect(self.repo, self.base, "HEAD", mode)
        data = json.loads((SKILL / "assets/example-data.json").read_text())
        data["meta"].update(collected["meta"])
        data["files"] = [dict(f, role="story-critical", diff_url="") for f in collected["files"]]
        data["coverage"] = dict(represented=[f["path"] for f in data["files"]], deemphasized=[], unresolved=[], evidence_gaps=[])
        data["code"] = [dict(source.excerpt(self.repo, collected["meta"], "main.py", "new", 1, 2), id="source", label="Changed value", language="python", emphasis=[1], diff_url="")]
        data["steps"] = [copy.deepcopy(data["steps"][1])]
        data["steps"][0].update(code_ids=["source"], claim_status="demonstrated", evidence=[{"label": "Implementation", "code_id": "source"}])
        data["findings"] = []
        return data

    def validate(self, data):
        result = validator.Validation()
        validator.validate_data(data, result)
        validator.validate_sources(data, self.repo, result)
        return result.errors

    def test_exact_pinned_source_passes_and_does_not_mutate_repo(self):
        before = self.git("status", "--porcelain")
        self.assertEqual(self.validate(self.document()), [])
        self.assertEqual(self.git("status", "--porcelain"), before)

    def test_fabricated_excerpt_is_rejected(self):
        data = self.document()
        data["code"][0]["content"] = "fabricated = True\nprint(fabricated)"
        self.assertTrue(any("source text differs" in e for e in self.validate(data)))

    def test_uninitialized_submodule_retains_gitlink_without_parent_discovery(self):
        source = load("walkthrough_submodule_sources", SKILL / "scripts/source_evidence.py")
        self.git("update-index", "--add", "--cacheinfo", f"160000,{self.base},sub")
        self.git("commit", "-qm", "gitlink")
        for present in (False, True):
            with self.subTest(empty_directory_present=present):
                if present:
                    (self.repo / "sub").mkdir()
                before = self.git("status", "--porcelain")
                self.assertEqual(source.collect(self.repo, "HEAD", "HEAD", "working")["files"], [])
                self.assertEqual(self.git("status", "--porcelain"), before)

    def test_nonrepository_content_at_gitlink_is_not_parent_repository_evidence(self):
        source = load("walkthrough_invalid_submodule_sources", SKILL / "scripts/source_evidence.py")
        self.git("update-index", "--add", "--cacheinfo", f"160000,{self.base},sub")
        self.git("commit", "-qm", "gitlink")
        (self.repo / "sub").mkdir()
        (self.repo / "sub" / "unknown.txt").write_text("unverified content\n")
        with self.assertRaisesRegex(ValueError, "submodule.*repository|uninitialized submodule"):
            source.collect(self.repo, "HEAD", "HEAD", "working")

    def test_initialized_submodule_records_own_head_and_rejects_dirty_tree(self):
        source = load("walkthrough_initialized_submodule", SKILL / "scripts/source_evidence.py")
        sub = self.repo / "sub"
        sub.mkdir()
        def subgit(*args):
            return subprocess.check_output(["git", "-C", str(sub), *args], text=True).strip()
        subgit("init", "-q")
        subgit("config", "user.email", "test@example.invalid")
        subgit("config", "user.name", "Fixture")
        subgit("commit", "--allow-empty", "-qm", "sub base")
        initial = subgit("rev-parse", "HEAD")
        self.git("update-index", "--add", "--cacheinfo", f"160000,{initial},sub")
        self.git("commit", "-qm", "gitlink")
        self.assertEqual(source.collect(self.repo, "HEAD", "HEAD", "working")["files"], [])
        subgit("commit", "--allow-empty", "-qm", "sub change")
        self.assertEqual(source.collect(self.repo, "HEAD", "HEAD", "working")["files"],
                         [{"path": "sub", "status": "modified", "additions": 1, "deletions": 1, "binary": False}])
        (sub / "dirty.txt").write_text("dirty\n")
        with self.assertRaisesRegex(ValueError, "dirty submodule"):
            source.collect(self.repo, "HEAD", "HEAD", "working")

    def test_inventory_omission_is_rejected_even_when_coverage_agrees(self):
        data = self.document()
        data["files"] = data["files"][:1]
        data["coverage"]["represented"] = [data["files"][0]["path"]]
        self.assertTrue(any("changed inventory differs" in e for e in self.validate(data)))

    def test_inventory_fabricated_counts_are_rejected(self):
        data = self.document()
        data["files"][0]["additions"] += 100
        self.assertTrue(any("diff statistics differ" in e for e in self.validate(data)))

    def test_demonstrated_claim_without_evidence_is_rejected(self):
        data = self.document()
        data["steps"][0]["evidence"] = []
        self.assertTrue(any("needs evidence" in e for e in self.validate(data)))

    def test_unknown_claim_with_explicit_gap_is_valid(self):
        data = self.document()
        data["steps"][0].update(claim_status="unknown", evidence=[], evidence_gap="No execution evidence available")
        self.assertEqual(self.validate(data), [])

    def test_evidence_cannot_point_to_nonexistent_code(self):
        data = self.document()
        data["steps"][0]["evidence"][0]["code_id"] = "invented"
        self.assertTrue(any("unknown code evidence" in e for e in self.validate(data)))

    def test_working_change_stales_without_head_change(self):
        data = self.document("working")
        (self.repo / "main.py").write_text("value = 3\nprint(value)\n")
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.head)
        self.assertTrue(any("snapshot is stale" in e for e in self.validate(data)))

    def test_staged_change_stales_without_head_change(self):
        data = self.document("staged")
        (self.repo / "main.py").write_text("value = 3\nprint(value)\n")
        self.git("add", "main.py")
        self.assertTrue(any("snapshot is stale" in e for e in self.validate(data)))

    def test_untracked_source_is_included_and_fingerprinted(self):
        (self.repo / "new.py").write_text("new = True\n")
        data = self.document("working")
        self.assertIn("new.py", [f["path"] for f in data["files"]])
        (self.repo / "new.py").write_text("new = False\n")
        self.assertTrue(any("snapshot is stale" in e for e in self.validate(data)))

    def test_index_fingerprint_changes_even_when_working_content_is_restored(self):
        data = self.document("working")
        (self.repo / "main.py").write_text("value = 4\nprint(value)\n")
        self.git("add", "main.py")
        (self.repo / "main.py").write_text("value = 2\nprint(value)\n")
        self.assertTrue(any("snapshot is stale" in e for e in self.validate(data)))

    def test_diff_excerpt_is_exact_and_anchored(self):
        source = load("walkthrough_diff_sources", SKILL / "scripts/source_evidence.py")
        data = self.document()
        data["code"][0].update(source.excerpt(self.repo, data["meta"], "main.py", "diff", 1, 4))
        self.assertEqual(self.validate(data), [])
        data["code"][0]["content"] += "\n+invented"
        self.assertTrue(any("source text differs" in e for e in self.validate(data)))

    def test_path_escape_and_symlink_escape_are_rejected(self):
        data = self.document()
        data["code"][0]["path"] = "../outside.txt"
        self.assertTrue(any("unsafe source path" in e for e in self.validate(data)))
        outside = self.repo.parent / (self.repo.name + "-outside")
        outside.write_text("private\n")
        self.addCleanup(outside.unlink)
        (self.repo / "escape").symlink_to(outside)
        source = load("walkthrough_symlink_sources", SKILL / "scripts/source_evidence.py")
        meta = source.collect(self.repo, self.base, self.head, "working")["meta"]
        with self.assertRaisesRegex(ValueError, "symlink"):
            source.excerpt(self.repo, meta, "escape", "new", 1, 1)

    def test_context_revision_must_be_endpoint_not_arbitrary_ref(self):
        data = self.document()
        data["code"][0].update(side="context", revision="HEAD")
        self.assertTrue(any("immutable endpoint" in e for e in self.validate(data)))

    def test_diff_uses_git_counts_for_literal_diff_marker_source_lines(self):
        (self.repo / "main.py").write_text("++source\n--source\n")
        self.git("add", "main.py")
        self.git("commit", "-qm", "marker-like lines")
        self.head = self.git("rev-parse", "HEAD").strip()
        source = load("walkthrough_diff_count_sources", SKILL / "scripts/source_evidence.py")
        collected = source.collect(self.repo, self.base, self.head)
        actual = next(f for f in collected["files"] if f["path"] == "main.py")
        self.assertEqual((actual["additions"], actual["deletions"]), (2, 2))

    def test_diff_retains_no_final_newline_evidence(self):
        (self.repo / "main.py").write_text("value = 2\nprint(value)")
        source = load("walkthrough_newline_sources", SKILL / "scripts/source_evidence.py")
        meta = source.collect(self.repo, self.head, self.head, "working")["meta"]
        piece = source.excerpt(self.repo, meta, "main.py", "diff", 1, 7)
        self.assertIn("\\ No newline at end of file", piece["content"])

    def test_committed_branch_movement_is_stale(self):
        data = self.document()
        (self.repo / "main.py").write_text("value = 5\nprint(value)\n")
        self.git("add", "main.py")
        self.git("commit", "-qm", "advance head")
        self.assertTrue(any("target ref is stale" in e for e in self.validate(data)))

    def test_committed_pinned_sha_remains_valid_after_unrelated_head_movement(self):
        data = self.document()
        data["meta"]["head_ref"] = self.head
        self.git("commit", "--allow-empty", "-qm", "unrelated later commit")
        self.assertEqual(self.validate(data), [])

    def test_tracked_generated_output_is_not_silently_excluded(self):
        (self.repo / ".walkthrough").mkdir()
        (self.repo / ".walkthrough/source.txt").write_text("tracked source\n")
        self.git("add", ".walkthrough/source.txt")
        data = self.document("working")
        self.assertIn(".walkthrough/source.txt", [f["path"] for f in data["files"]])


if __name__ == "__main__":
    unittest.main()

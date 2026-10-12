"""Exercise the shell installer without writing to personal skill directories."""

import os
import shutil
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "install.sh"


def install(tmp_path):
    checkout = tmp_path / "checkout"
    checkout.mkdir(exist_ok=True)
    shutil.copyfile(SCRIPT, checkout / "install.sh")
    skill = checkout / "sample"
    skill.mkdir(exist_ok=True)
    (skill / "SKILL.md").write_text("---\nname: sample\ndescription: Test fixture\n---\n")
    environment = {
        **os.environ,
        # Isolate the subprocess's home even when an old installer ignores overrides.
        "HOME": str(tmp_path / "isolated-home"),
        "AGENT_SKILLS_CLAUDE_DIR": str(tmp_path / "claude" / "skills"),
        "AGENT_SKILLS_AGENTS_DIR": str(tmp_path / "agents" / "skills"),
        "AGENT_SKILLS_CODEX_DIR": str(tmp_path / "codex" / "skills"),
    }
    result = subprocess.run(["bash", str(checkout / "install.sh")], env=environment,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    return checkout, result


def test_canonical_discovery_directory_created_on_first_install(tmp_path):
    checkout, _ = install(tmp_path)
    assert (tmp_path / "agents" / "skills" / "sample").resolve() == checkout / "sample"
    assert (tmp_path / "claude" / "skills" / "sample").is_symlink()
    assert (tmp_path / "codex" / "skills" / "sample").is_symlink()


def test_idempotent_and_preserves_unrelated_entries(tmp_path):
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "valuable.txt").write_text("preserved")
    destination = tmp_path / "agents" / "skills"
    destination.mkdir(parents=True)
    (destination / "sample").symlink_to(foreign, target_is_directory=True)
    install(tmp_path)
    _, second = install(tmp_path)
    assert (destination / "sample").resolve() == foreign
    assert (foreign / "valuable.txt").read_text() == "preserved"
    assert "already linked" in second.stdout


def test_relinks_dangling_entry(tmp_path):
    destination = tmp_path / "agents" / "skills"
    destination.mkdir(parents=True)
    (destination / "sample").symlink_to(tmp_path / "old-clone" / "sample")
    checkout, result = install(tmp_path)
    assert (destination / "sample").resolve() == checkout / "sample"
    assert "was dangling" in result.stdout

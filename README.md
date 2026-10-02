# agent-skills

Portable [Agent Skills](https://agentskills.io) — compatible with Claude Code, OpenAI Codex CLI, and other tools that read the `SKILL.md` standard. Each directory containing a `SKILL.md` is one skill, invoked as `/<directory-name>`.

## Install

One command, on any machine:

```bash
curl -fsSL https://raw.githubusercontent.com/kwajiehao/agent-skills/main/install.sh | bash
```

That clones this repo to `~/.agent-skills` and symlinks every skill into the agent skill directories it finds. Re-run it any time to pull the latest and link newly added skills — it's idempotent and never overwrites anything it didn't create.

Already have the repo cloned? Just run it from the root:

```bash
./install.sh
```

## Available skills

| Skill | Description |
|-------|-------------|
| `/ai-fuzzing` | Extracts fuzzing requirements, builds and audits fuzz harnesses, runs bounded campaigns, and turns failures into durable feedback |
| `/dep-review` | Reviews dependency bump PRs by auditing codebase usage, analyzing changelog/release changes, and cross-referencing impact to produce a structured risk assessment |
| `/walkthrough` | Builds author-perspective visual PR walkthroughs with synchronized prose, exact code, diagrams, evidence, and a secondary review lens |

## How installing works

`install.sh` symlinks rather than copies, so `git pull` in `~/.agent-skills` updates every installed skill at once. It links into:

| Path | When |
|---|---|
| `~/.claude/skills/` | always |
| `~/.codex/skills/` | only if `~/.codex` exists |
| `~/.agents/skills/` | only if `~/.agents` exists |

The optional paths are skipped when the tool isn't installed, so you don't collect empty config directories.

Existing entries are left untouched: a skill already linked is skipped, a real directory or a symlink pointing somewhere else is reported and left alone. Only a *dangling* symlink — from a clone you moved or deleted — gets repaired automatically.

Overrides, if you need them:

```bash
AGENT_SKILLS_DIR=~/src/agent-skills ./install.sh   # where to clone
AGENT_SKILLS_REPO=git@github.com:me/fork.git ./install.sh
```

## Adding a skill

1. Create a directory — its name becomes the `/slash-command`.
2. Add `SKILL.md` with YAML frontmatter (`name`, `description`) followed by the instructions.
3. Re-run `./install.sh` to link it.

```markdown
---
name: my-skill
description: One line describing when to use this, used to decide relevance.
---

## My Skill

Instructions for the agent...
```

## Requirements

`bash` and `git`. Symlink creation needs no special privileges on macOS, Linux, or WSL; on native Windows use WSL or Git Bash with Developer Mode enabled.

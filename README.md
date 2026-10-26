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
| `/code-walkthrough` | Reads code from its entrypoint, explains each meaningful block, steps into important implementations, and returns to the caller |
| `/walkthrough` | Builds evidence-linked visual explanations of software, systems, architecture, and technical workflows with synchronized prose, diagrams, and source |
| `/pr-walkthrough` | Builds author-perspective visual walkthroughs of PRs, commit ranges, or local changes with exact code, diagrams, evidence, and a secondary review lens |
| `/draft-slack-message` | Drafts any Slack message to colleagues (DMs, replies, channel posts, intros, updates) in the user's voice, pulling relationship, thread and channel context from Slack first; never sends without approval |
| `/research` | Clarifies vague research questions, investigates online, and produces understandable, source-backed reports with useful visuals |
| `/write-commit-message` | Writes accurate commit messages from actual changes, preserving the rationale and following repository conventions |
| `/python-engineering` | Implements and debugs production Python with explicit runtime, ownership, failure, and concurrency models, including threads, async, and processes |
| `/pr-review` | Traces operations across component handoffs, challenges design and failure paths, and verifies consequential requirements with concrete evidence |
| `/pr-description` | Drafts concise PR titles and descriptions grounded in the diff, rationale, validation, and material risks |

Personal Codex context, hooks, and profiles: [personal-setup](personal-setup/README.md).

## How installing works

`install.sh` symlinks rather than copies, so `git pull` in `~/.agent-skills` updates every installed skill at once. It links into:

| Path | When |
|---|---|
| `~/.claude/skills/` | always |
| `~/.codex/skills/` | only if `~/.codex` exists |
| `~/.agents/skills/` | always; canonical shared/Codex discovery path |

The legacy Codex path is skipped when its configuration directory is absent.
An explicit `CODEX_HOME` creates its configured skills path. For isolated or
custom installations, `AGENT_SKILLS_CLAUDE_DIR`, `AGENT_SKILLS_AGENTS_DIR` and
`AGENT_SKILLS_CODEX_DIR` override the individual destinations.

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

## Verification and behavioral evaluations

Run tooling regressions with `python -m pytest -q` in an environment containing
pytest. The fuzz recorder and walkthrough suites also support stdlib unittest.
Tests exercise actual subprocess, Git, source-validation and effect boundaries;
skill-following quality needs independent agent trials as well.

Use [evals](evals/README.md) to prepare isolated project fixtures and organic
requests, record observed actions/artifacts, and grade against hidden outcome
criteria. Trial records identify the skill snapshot and execution environment.
Missing measurements remain unmeasured. Compare matched repeated trials before
claiming higher success or lower cost. Keep failed trials as regression evidence.

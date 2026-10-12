---
id: "workflow-reliability-20261011"
title: "Bind review evidence and evaluate specialist workflows"
allowed_paths:
  - "walkthrough/**"
  - "dep-review/**"
  - "ai-fuzzing/**"
  - "evals/**"
  - "tests/**"
  - "install.sh"
  - "README.md"
  - ".gitignore"
  - "pytest.ini"
  - "agent-docs/**"
test_commands:
  - "/private/tmp/agent-workflow-dev-20261011/bin/python -m pytest -q"
smoke_command: "/private/tmp/agent-workflow-dev-20261011/bin/python evals/run_evals.py verify agent-docs/verification/workflow-reliability-20261011/pilots --require-scenario dep-resolved-default --require-scenario dep-unavailable-notes --require-scenario dep-no-sources --require-scenario fuzz-mature-native --require-scenario fuzz-semantic-gap --require-scenario fuzz-seeded-retry --require-scenario fuzz-interrupted --require-scenario walkthrough-source-integrity"
acceptance:
  - condition: "Walkthrough source, inventory and local snapshot validation rejects fabricated or stale evidence."
    command: "/private/tmp/agent-workflow-dev-20261011/bin/python -m pytest -q"
  - condition: "Dependency review distinguishes resolved versions, compatibility, meaningful verification and inconclusive evidence."
    command: "/private/tmp/agent-workflow-dev-20261011/bin/python evals/run_evals.py verify agent-docs/verification/workflow-reliability-20261011/pilots --require-scenario dep-resolved-default --require-scenario dep-unavailable-notes --require-scenario dep-no-sources --require-scenario fuzz-mature-native --require-scenario fuzz-semantic-gap --require-scenario fuzz-seeded-retry --require-scenario fuzz-interrupted --require-scenario walkthrough-source-integrity"
  - condition: "Behavioral evaluation tooling rejects failed outcomes and records repeated comparable trials without invented measurements."
    command: "/private/tmp/agent-workflow-dev-20261011/bin/python -m pytest -q"
  - condition: "Installer creates documented skill discovery paths without overwriting unrelated existing skills."
    command: "/private/tmp/agent-workflow-dev-20261011/bin/python -m pytest -q"
coordination:
  mode: review
  reviewer:
    characterization: "Independent reviewer of source-bound walkthroughs, dependency evidence, fuzzing pilot validity, installer portability and behavior-based evaluations"
---

# workflow-reliability-20261011: Bind review evidence and evaluate specialist workflows

## Task

Implement the specialist skill, portability and evaluation improvements
authorized after the October 9 review. Add source-aware walkthrough verification,
strengthen dependency review evidence and verdicts, evaluate fuzzing workflows
with real targets and findings, provide isolated repeatable behavior-based agent
evaluations, and test portable installation. Use red-green regressions where
possible. Preserve the user-owned untracked repository-walkthrough skill.
Do not commit, publish or update installed personal skills in this task.

## Acceptance

1. The mapped behaviors above have meaningful regression evidence and real
   independent agent pilots. Browser verification exercises the bundled renderer.
2. `test_commands` pass.
3. `smoke_command` passes, if defined.
4. Required coordination artifacts pass, if `coordination.mode` is `review` or `delegated`.

## Handoff

Initial HEAD: 1fefd1a0bda31ba381fb019d65daa9788761400b.
Pre-existing user work: untracked repository-walkthrough/; outside edit scope.
Development environment: /private/tmp/agent-workflow-dev-20261011.

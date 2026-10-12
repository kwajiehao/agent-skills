---
id: "2026-10-11-trim-greeting"
title: "Trim surrounding whitespace in greetings"
read_first:
  - "README.md"
  - "CODING.md"
  - "TESTING.md"
  - "greeting.py"
  - "tests/test_greeting.py"
allowed_paths:
  - "greeting.py"
  - "tests/**"
  - "agent-docs/**"
test_commands:
  - "/private/tmp/agent-workflow-dev-20261011/bin/python -B -m unittest discover -s tests -v"
coordination:
  mode: solo
acceptance:
  - condition: "greet trims surrounding spaces, tabs and newlines while preserving interior whitespace and the existing greeting format."
    command: "/private/tmp/agent-workflow-dev-20261011/bin/python -B -m unittest discover -s tests -v"
---

# 2026-10-11-trim-greeting: Trim surrounding whitespace in greetings

## Task

Update `greet(name)` to trim surrounding whitespace before formatting its greeting.
Add regression coverage through the existing unittest suite. Keep the change
within greeting.py, tests, and task/run artifacts. Use Python's standard library;
no installs, commits, or external services are authorized.

Use solo coordination because the function and its tests have a clear local seam.
Use the supplied Python environment and disable bytecode output with `-B`.
Complete within the approximately eight-minute budget once the runner verifies
all declared behavior and the final diff is inspected.

## Acceptance

1. Surrounding spaces, tabs and newlines are removed: `greet(" \tAda\n ")`
   returns `"Hello, Ada!"`.
2. Interior whitespace is preserved, and the existing `greet("Ada")` output
   remains `"Hello, Ada!"`.
3. The declared unittest command passes in final runner verification. Retain
   the failing regression output before the fix and inspect final artifacts.

## Handoff

Resume discovery returned `intake_required` without warnings. The worktree was
clean. README.md and TESTING.md declare unittest discovery; CODING.md limits
dependencies to the standard library. Next: prepare a run, add the regression,
retain its failure, implement `str.strip()`, and verify through the runner.

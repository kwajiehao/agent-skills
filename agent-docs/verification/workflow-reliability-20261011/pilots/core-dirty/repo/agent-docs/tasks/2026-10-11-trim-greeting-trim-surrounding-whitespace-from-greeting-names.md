---
id: "2026-10-11-trim-greeting"
title: "Trim surrounding whitespace from greeting names"
read_first:
  - "greeting.py"
  - "tests/test_greeting.py"
  - "CODING.md"
  - "TESTING.md"
allowed_paths:
  - "greeting.py"
  - "tests/**"
  - "agent-docs/tasks/**"
  - "agent-docs/runs/**"
test_commands:
  - "/private/tmp/agent-workflow-dev-20261011/bin/python -m unittest discover -s tests -v"
coordination:
  mode: solo
acceptance:
  - condition: "Greeting names omit leading and trailing spaces, tabs, and newlines."
    command: "/private/tmp/agent-workflow-dev-20261011/bin/python -m unittest discover -s tests -v"
  - condition: "Existing greeting punctuation and internal name whitespace are preserved."
    command: "/private/tmp/agent-workflow-dev-20261011/bin/python -m unittest discover -s tests -v"
---

# 2026-10-11-trim-greeting: Trim surrounding whitespace from greeting names

## Task

Trim leading and trailing whitespace from the name passed to `greet`, using the
existing public function. Preserve greeting punctuation and internal whitespace.
Add regression coverage before implementing and retain the failure evidence.

Work in solo mode within greeting.py, tests, and task/run artifacts. The existing
notes.txt change is unfinished personal work and must be preserved byte-for-byte.
Use the supplied Python environment; no installs, commits, or external services.
Exit when the declared behavioral tests pass in final runner verification, the
task delta is in scope, and notes.txt still matches its original dirty state.
Budget: approximately eight minutes.

## Acceptance

1. Names padded with spaces, tabs, or newlines produce a greeting without that
   surrounding whitespace, proven by tests/test_greeting.py.
2. Ordinary names and internal name whitespace retain existing greeting format,
   proven by tests/test_greeting.py.
3. The declared unittest suite passes under final runner verification.
4. Only authorized implementation and task/run paths are changed; notes.txt
   retains the pre-existing `My unfinished note.` content.

## Handoff

Intake complete: greet currently interpolates names verbatim. Existing unit test
covers Ada. No consuming AGENTS.md was found. Repository instructions specify
standard-library Python and unittest discovery. Resume returned intake_required.
Next: prepare run, add and run regression, implement str.strip(), simplify, then
use the runner for final verification. No services or other resources are owned.

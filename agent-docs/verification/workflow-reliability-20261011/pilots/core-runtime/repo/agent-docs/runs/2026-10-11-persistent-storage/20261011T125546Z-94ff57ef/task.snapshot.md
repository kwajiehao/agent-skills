---
id: "2026-10-11-persistent-storage"
title: "Persist saved values across process restarts"
read_first:
  - "storage.py"
  - "tests/test_storage.py"
  - "README.md"
  - "CODING.md"
  - "TESTING.md"
allowed_paths:
  - "storage.py"
  - "tests/**"
  - "scripts/**"
  - "agent-docs/**"
test_commands:
  - "/private/tmp/agent-workflow-dev-20261011/bin/python -m unittest discover -s tests -v"
coordination:
  mode: solo
acceptance:
  - condition: "A fresh process loading the same path returns the value saved by a previous process, including an overwrite."
    command: "/private/tmp/agent-workflow-dev-20261011/bin/python -m unittest discover -s tests -v"
  - condition: "Existing save/load API and missing-path behavior remain valid using standard-library storage."
    command: "/private/tmp/agent-workflow-dev-20261011/bin/python -m unittest discover -s tests -v"
---

# 2026-10-11-persistent-storage: Persist saved values across process restarts

## Task

Implement durable JSON storage through the existing `save_value(path, value)` and
`load_value(path)` public API. A saving process may exit before a fresh process
loads the caller-selected file. Preserve `None` for missing paths and support
overwriting a saved value. Use the Python standard library only.

Local edits and verification are authorized. Do not commit, install dependencies,
or access external services. Keep changes within storage, tests, optional
verification helpers, and task/run artifacts. Coordinate solo because the public
contract and implementation boundary are explicit and narrow.

## Acceptance

1. Separate saving and loading Python processes round-trip nested JSON values at
   the same path, and a later save replaces the previous value.
2. Same-process save/load behavior remains valid for string and pathlib paths.
3. Loading a missing file returns `None`.
4. The declared unittest command passes and records actual execution evidence.

## Handoff

Resume discovery returned `intake_required` with no warnings. The original
implementation stores values in a module dictionary; that state cannot survive
process exit. Next: prepare the run, add a subprocess regression, capture its
failure, implement JSON file persistence, and let the runner verify completion.

# Handoff: 2026-10-11-persistent-storage Persist saved values across process restarts

## Current State

Implemented JSON file persistence and a fresh-process regression. This run is
preserved as failed workflow evidence; a new run is required for the amended
verification command that disables bytecode generation.

## Commands Run

- Resume discovery returned intake_required without warnings.
- Generated and prepared the solo task with mapped acceptance conditions.
- Ran the declared unittest command against original storage.py plus new tests:
  4 tests executed, with two failing subcases for restart/overwrite.
- Final verifier ran 4 tests successfully. Its diff_scope and snapshot_stability
  gates failed because the command generated untracked Python bytecode.

## Failures Seen

- Fresh reader processes returned None for both nested saved values. Red evidence
  is retained in red-regression.txt. The three same-process/missing-path tests
  passed before the fix.
- Original verification.json retains actual passing behavior and failing
  workflow gates. Do not report this run as complete.

## Next Hypothesis

- The fix passes behavior checks. Amend the verification command and subprocess
  drivers with -B, prepare a new frozen run, and verify stable scope/evidence.

## Notes For Resume

- Run dir: `/private/tmp/workflow-pilots-20261011.jYJEET/core-runtime/repo/agent-docs/runs/2026-10-11-persistent-storage/20261011T125546Z-94ff57ef`
- All subprocesses are synchronous, exited, and use unique temporary directories.
- No dependencies installed, commits created, or external services accessed.
- Standard-library JSONValue types document the existing JSON-compatible API.
- Only run-created bytecode was moved recoverably to core-runtime project parent
  as generated-storage.cpython-313.pyc and generated-test_storage.cpython-313.pyc.
- The pre-existing tracked pytest cache file was not changed.

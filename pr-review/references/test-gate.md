# Diff-time test gate

Load only when the diff adds or modifies tests. Skip this file completely when
no tests changed.

This gate evaluates tests touched by the diff; it does not sweep untouched
legacy suites.

## Gate each added or changed test

1. **Pins changed behavior:** Name the observable behavior, invariant, or
   independent contract this diff changed and the hunk or bug it guards.
2. **Can fail on a real regression:** Name a plausible defect that turns the
   test red. Reject tautological assertions (expected values computed by the
   code under test or its helpers), existence/render-only checks, and tests
   duplicating guarantees the compiler or type checker already enforces.
3. **One owner, no layer duplication:** Check sibling tests and outer suites
   for the same contract. Each behavior or bug gets one primary owner at the
   outermost cheap boundary. Prefer adding a row to an existing parametrized
   table or shared fixture over adding a new test function, and do not replay
   the same regression at every layer it crosses.
4. **Behavior, not internals or mock echoes:** Reject private call-shape
   assertions (`assert_called_with` / `toHaveBeenCalledWith` on internal
   collaborators), rename-sensitive source/copy greps, and mock-only tests
   where a stub supplies the value being asserted. Fake or mock only external,
   slow, or nondeterministic boundaries—not owned collaborators.
5. **No test-only production seams:** Reject new exports, flags, wrappers, or
   injection hooks that have no production caller. Move the test to the real
   boundary and remove the seam.

## Retention bar

- Keep independent contracts: public API, protocol, schema, config, migration,
  storage, security, platform, default, release, or observable ordering.
- Keep focused parametrized edge-case tables for non-trivial pure logic
  (parsers, math, transforms) that an outer test would cover poorly.
- Keep reproduced regressions that failed on pre-fix code for the intended
  reason.
- Static or slow is not a deletion reason. Never weaken or delete a
  pre-existing or failing test to make a build green.

## Dispositions and reporting

Assign each failing test one disposition:

- **Consolidate:** real risk, but belongs as a case in an existing test/table
  or is already covered by a named outer boundary test.
- **Rewrite:** real risk, but asserts mocks, internals, or circular
  expectations; move to the owning boundary with independent literal
  expectations.
- **Delete:** fails check 1 or 2 with no salvageable contract.

In read-only reviews, fold failed checks into the review findings with
`file:line`, the failed check, the stronger remaining proof (or missing
contract), and the smallest fix. When edits are authorized, delete or
consolidate confirmed failures and remove any test-only production seams they
unlocked.

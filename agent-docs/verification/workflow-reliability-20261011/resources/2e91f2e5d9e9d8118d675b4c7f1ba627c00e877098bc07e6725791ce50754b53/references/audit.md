# Auditing a Fuzzer

An audit asks whether the fuzzing system can discover and correctly report the
failure classes it claims to test. Reading the harness is necessary but not
sufficient; challenge it with controlled evidence.

## Inputs

Collect:

- the approved fuzzing specification and open questions;
- target and harness source;
- seed corpus and stored failing examples;
- replay and campaign commands;
- recent campaign ledger entries;
- historical bugs or incidents relevant to the target;
- code/edge coverage and semantic feature reports where available.

If no specification exists, the audit can assess basic safety fuzzing and
harness mechanics, but cannot declare semantic coverage trustworthy.

## 1. Requirement traceability

Build a matrix:

| Requirement ID | Generator/scenario | Oracle | Observable evidence | Replayed or challenged | Status |
|---|---|---|---|---|---|

Flag:

- approved requirements with no oracle;
- oracles with no approved requirement;
- generators that do not exercise the oracle's preconditions;
- public guarantees checked only through mock expectations or internal state
  without validating their externally visible or durable consequences;
- requirements whose only assertion is crash absence.

## 2. Target fidelity

Trace representative generated inputs through the harness into the system under
test. Confirm that the intended production code, configuration, serialization,
persistence, retries, and side effects are reached at the chosen seam.

Look specifically for AI-generated shortcuts:

- fake implementations or locally redefined symbols;
- mocks returning the exact values asserted by the oracle;
- setup that bypasses validation or state transitions;
- exception swallowing and unconditional success;
- test-only behavior that cannot occur in the real system;
- a video, log, or report showing the harness's simulation rather than the real
  target.

Controlled substitutes and internal invariants are legitimate when their scope
is explicit. Apply [side-effects.md](side-effects.md): validate the actual product
logic, observer, isolation, and assumptions not covered by the substitute. For
infrastructure, check recovery under restored conditions as well as safety during
faults. An execution timeout alone does not establish a product liveness bug.

## 3. Generator quality

Inspect and measure:

- boundary, valid, invalid, and almost-valid input production;
- structural constraints and reject/discard rates;
- reachable states and transitions;
- action-sequence lengths and diversity;
- fault points, schedules, retries, duplicates, restarts, and concurrency;
- declared semantic features and important cross-products;
- seed-corpus diversity and redundancy;
- whether mutations preserve enough structure to reach deep behavior;
- whether one dominant case family crowds out the rest.

Do not accept "random" as evidence of diversity. Produce counts for domain
features and demonstrate explicit scenario reachability.
Distinguish generated, observed, and checked histories. Verify that scenario
predicates require the appropriate event order and shared entity/operation, and
that required oracles run after the relevant effects. Challenge missing observers
and traces with the same labels in an incorrect order.

## 4. Oracle strength and independence

For each oracle, ask:

- What exact wrong behavior makes it fail?
- Is that behavior forbidden by an approved requirement?
- Could a plausible product bug occur while the oracle passes?
- Could legitimate unspecified behavior make it fail?
- Is it copied from, or dependent on, the same logic as the target?
- Does it check durable effects as well as immediate return values?
- Does it run after every relevant state transition?

Prefer complementary independent oracles. A reference model should be simpler
than the product, and a differential oracle must account for intentional
differences between implementations or versions.

## 5. Replay, reduction, and determinism

Verify that:

- the exact seed/input and revision reproduce the finding;
- the full command history, schedule, and fault plan are captured;
- unrelated global state, time, network, or randomness is controlled;
- minimization preserves the same failure signature and property violation;
- stored failures remain runnable as the harness evolves;
- flaky results record a reproduction rate rather than a false deterministic
  claim.

## 6. Empirical challenge

Use the safest applicable controls:

1. Replay historical cases: expect a violated check on the affected defective
   revision and a passing regression on its fixed revision.
2. Supply malformed or forbidden inputs and verify contract-compliant rejection
   passes the test. Invalid input is not itself an oracle failure.
3. Exercise a controlled contract violation and verify the intended oracle fails;
   also test legitimate boundary behavior for false positives. Keep these controls
   separate from ordinary product findings and record their expected outcomes.
4. Disable or perturb an isolated test fixture to prove the harness notices an
   unreachable target or broken observer.
5. If authorized, use a mutation-testing tool or isolated temporary/worktree
   change to seed representative defects.

Never leave product mutations in the user's working tree. Prefer a project's
existing mutation framework, a disposable worktree, or build-time substitution.
Obtain authorization before material temporary changes or expensive runs.

Record which seeded defects were killed, survived, or could not be exercised.
A surviving defect is actionable evidence of an oracle or reachability gap, not
proof that the entire fuzzer is worthless.

## 7. Performance and exploration

Measure setup cost, executions per second, timeout/OOM rates, discard rates,
corpus growth, and useful coverage growth over time. Identify blockers such as
checksums, encryption, overly broad targets, slow external dependencies, or
invalid-input rejection before meaningful code.

Follow the principle in LLVM's
[libFuzzer documentation](https://llvm.org/docs/LibFuzzer.html): an in-process
target should be fast, deterministic, and repeatedly callable, while structured
inputs may require seed corpora, dictionaries, or custom mutators.

## Report

Lead with one verdict:

- **Ready for campaign:** critical requirements are traced, representative
  defect controls fail and valid-behavior controls pass correctly, replay works,
  and no material fidelity gap remains for the named target/profile.
- **Useful with gaps:** the harness can find some real bug classes, with named
  limitations and prioritized improvements.
- **Not trustworthy yet:** fake/unreachable behavior, weak oracles, non-replayable
  failures, or uncontrolled false positives prevent reliable use.
- **Blocked:** required access, an authoritative semantic decision, or a viable
  test seam is missing.

Include evidence, not just recommendations:

- commands actually run;
- traceability and semantic-coverage matrices;
- controls and seeded defects attempted;
- failures reproduced or rejected;
- prioritized changes mapped to the specification, generator, oracle, harness,
  corpus, or campaign process.

Use run manifests and measured results, not a mutable ledger summary, as evidence.
State the exact revisions/profile to which the verdict applies. Check that CI
rejects absent/malformed reports, missing required coverage, and interrupted runs.
Scope the verdict to accepted requirements; unresolved required guarantees remain
explicit gaps. Read-only audits may identify missing empirical evidence without
installing tools, modifying product code, or opening a specification interview.

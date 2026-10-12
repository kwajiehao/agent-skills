# Side Effects and Stateful Infrastructure

Read when tests touch files, databases, networks, queues, processes, clocks, or
external actions. Test effects through the real product behavior at the selected
seam; choose an environment that contains their consequences.

## Choose and verify the boundary

Before execution, identify each effect, the owned resource it can reach, how its
actual occurrence is observed, and how state is reset. Record this in the spec.
Reuse applicable environment approval; request only missing scope or access.

| Effect | Useful contained environment | Evidence and common pitfall |
|---|---|---|
| Filesystem | Per-case temporary directory; actual filesystem when rename, locking, permissions, or persistence matter | Read files after operations/reopen; in-memory maps cannot establish filesystem guarantees |
| Database | Disposable database/schema using the relevant engine/version | Query committed state through a fresh connection; rollback-only fixtures cannot establish commit/restart durability |
| Queue or event bus | Isolated broker/namespace and real consumer when delivery is in scope | Observe delivery, acknowledgment, redelivery and consumer effects; a mocked publish call checks none of those |
| HTTP dependency | Local controlled server, emulator, or approved provider sandbox | Observe requests and product response to partial replies/timeouts; emulator results do not establish provider semantics |
| Email, payment, deletion, provisioning | Local sink or explicitly approved sandbox with synthetic identities | Capture attempted actions without contacting real recipients, charging accounts, or changing real resources |
| Clocks/processes/scheduling | Injected clock or scheduler; owned child processes for real restart tests | Record clock moves, process lifecycle and fault timing; a seed alone cannot control OS scheduling |

Check resolved endpoints, database names, filesystem roots, and credentials before
running. Use synthetic data, least-privilege test credentials, and egress controls
where supported. A variable named `TEST_DATABASE_URL` is not evidence of isolation.
Generic command wrappers and this skill are not sandboxes. If the environment
cannot contain the effects, stop only the dependent execution and report why.

Create a fresh baseline between independent cases; retain intended state within
one generated history. Bound resources and clean up only exact resources owned
by that run. Arrange cleanup on ordinary failure and timeout; keep enough state
for investigation before destroying it. On interruption, record any remaining
resources and cleanup instructions. Use rollback for suitable transactional tests,
but use real commits and fresh readers when testing durability or visibility.

## Controlled substitution and observation

Replacing a dependency at an explicit boundary is legitimate when it controls
faults or contains effects while still executing the product logic under test.
Document which claims the substitute supports and which it cannot establish.

For example, a local HTTP server can accept a request then drop the response to
exercise the real client's retry logic. A mock that returns the expected final
result bypasses that behavior. Likewise, a simulated disk may exercise a real
storage algorithm under a declared persistence model; it does not by itself
validate the real filesystem's crash behavior.

Compare substitutes with real isolated dependencies using representative contract
and integration tests when their fidelity matters. Internal invariants may
complement public observations; do not copy implementation algorithms into their
oracles. Record modeled behavior, observed effects, and unchecked real-world
assumptions separately. Side-effect observation must survive the failure: use a
fresh reader, durable sink, or independently captured history when necessary.

## Infrastructure profile

Use for durability, concurrency, distributed consistency, or recovery claims.
Select applicable dimensions; do not impose database machinery on pure functions.

Specify:

- **Safety:** what must never occur, including partial effects, duplicate effects,
  corruption, or invalid histories under the promised consistency model.
- **Durability:** what an acknowledgment commits to, where flush/commit boundaries
  are, and which effects must survive each modeled crash.
- **Uncertain outcomes:** after a timeout, an operation may have committed. Track
  invocation, response and observed durable effects; do not treat timeout as proof
  of failure or absence of effects.
- **Fault assumptions:** tolerated partitions, message loss/duplication/reordering,
  partial writes, disk-full/I/O errors, crashes, and clock movement. Distinguish
  adversarial probes outside those assumptions from contract violations.
- **Recovery/liveness:** conditions under which progress is promised, including
  restored connectivity, sufficient healthy members, scheduling fairness, and
  bounded workload. Define a justified recovery deadline in the chosen clock.

Generate histories with stable operation/resource IDs and explicit fault points.
Keep safety checks running during faults. Then restore the specified healthy
conditions and check recovery and progress; endless fault injection cannot test
that phase. A harness wall-clock deadline is an execution limit, not automatically
a violated product liveness requirement.

Prefer deterministic simulation when the architecture supports controlled clocks,
I/O, randomness and scheduling. Otherwise record the actual history and measure
reproduction rates honestly. Complement simulation with real integration checks
for assumptions outside the model. If controlling the necessary boundary requires
a product change beyond the task, describe that seam instead of claiming a seed
makes the existing system deterministic.

Example contract, requiring domain acceptance: a committed job whose acknowledgment
was lost may be delivered again after restart, but its idempotent business effect
must occur once; eligible jobs must resume processing after the declared recovery
conditions hold. Observe the business effect through durable state, not just the
number of calls to a mock. Generate variations in commit, acknowledgment loss,
restart and retry order, and retain the full trace for reduction and replay.

For concrete examples, see TigerBeetle's
[liveness testing](https://tigerbeetle.com/blog/2023-07-06-simulation-testing-for-liveness/)
and [controlled simulation](https://tigerbeetle.com/blog/2026-08-20-protocol-aware-dst/).

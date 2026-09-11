# Fuzz Harness Design

Turn accepted fuzzing requirements into an executable, falsifiable test
system. Prefer the simplest project-native mechanism capable of exercising the
chosen behavioral seam.

## Choose the testing family

| Target shape | Primary approach | Typical oracle |
|---|---|---|
| Pure or mostly pure function with structured inputs | Property-based generation | Invariant, postcondition, round trip, reference model |
| Parser, decoder, codec, compiler front end, native library | Mutation or coverage-guided fuzzing | Crash, sanitizer, round trip, differential result |
| Structured file or protocol | Grammar- or structure-aware generation | Parser acceptance, semantic invariant, differential result |
| Stateful object, repository, API, or workflow | Rule/state-machine generation | Model comparison and invariants after each action |
| Concurrent or distributed behavior | Generated histories and fault schedules | Consistency/history checker, safety, and conditional recovery/progress checks |
| Existing production traffic | Corpus mutation or trace replay with controlled variation | Existing contract plus metamorphic and differential checks |

These approaches can be combined. Do not introduce a sophisticated framework
when a small deterministic loop will answer the question, and do not hand-roll
an engine when the project already has a suitable maintained tool.

## Harness anatomy

### Target adapter

The adapter must exercise the real code at the approved seam. Keep it fast and
deterministic enough for repeated execution. Make setup and teardown explicit.
For side effects, use [side-effects.md](side-effects.md) to choose isolated real
dependencies or controlled substitutes and document their fidelity limits.

Detect and reject these common AI-generated failures:

- reimplementing or stubbing the target instead of calling it;
- mocking away the persistence, retries, ownership, or ordering under test;
- accepting every input before it reaches meaningful behavior;
- swallowing exceptions or converting all outcomes to success;
- retaining global state that contaminates later cases;
- depending on wall-clock time or uncontrolled randomness;
- generating an artificial reproduction that cannot occur in the real stack.

Google's guide to
[good fuzz targets](https://github.com/google/fuzzing/blob/master/docs/good-fuzz-target.md)
is the baseline for byte-oriented and coverage-guided targets: targets should be
fast, deterministic, tolerant of arbitrary input, and able to reach meaningful
behavior.

### Generator or mutator

Start with the smallest useful input model and improve it from evidence.

1. Generate both valid and invalid or nearly valid structures.
2. Favor boundaries and semantically distinct values rather than uniform noise.
3. Preserve field relationships with constraints or constructors instead of
   generating invalid combinations and rejecting almost all of them.
4. For stateful systems, generate actions as well as values. Model action
   preconditions and allow intentionally invalid transitions where the contract
   defines their result.
5. Create scenario generators for rare multi-step bug ingredients instead of
   hoping independent choices will combine them.
6. Seed mutation-based fuzzers with small, diverse examples and dictionaries
   when appropriate.
7. Record domain-level feature labels for states, actions, faults, and important
   cross-products.
8. Add coverage feedback only after the basic harness is trustworthy. Coverage
   steers exploration; it does not define correctness.

The [Fuzzing Book](https://www.fuzzingbook.org/) provides practical treatments
of random, mutation, grammar, constraint, semantic, API, and greybox generation.

### Oracles

Prefer an oracle that is structurally independent from the target:

1. Accepted external specification or authoritative implementation.
2. Simple, slow reference model.
3. Differential comparison against another implementation or version.
4. Postconditions and invariants over observable state.
5. Metamorphic relations, round trips, idempotence, conservation, or monotonicity.
6. Crash, sanitizer, timeout, leak, or assertion detection.

Use several complementary oracles when they detect different failure classes.
Link every oracle to one or more approved requirement IDs. Mark diagnostic
checks that are not normative so they cannot create false product failures.

Avoid these oracle anti-patterns:

- duplicating the production algorithm line for line;
- asserting only that a value is non-null or has the expected type;
- snapshots whose contents were generated from the current broken behavior;
- comparing two paths that share the same faulty dependency;
- assertions so restrictive that legitimate unspecified behavior fails;
- assertions disabled for the inputs most likely to expose a bug.

### Execution, persistence, and replay

The runnable harness must expose:

- one documented smoke command;
- ordinary build/CI integration and a deterministic retained-regression command;
- one deterministic seed or input replay command;
- bounded case size, step count, memory, and execution time;
- the complete generated input or command history on failure;
- target, harness, specification, and dependency revisions;
- relevant sanitized environment configuration;
- a persistent corpus or failing-example store where the selected tool supports it.

Capture machine-readable results using the project's runner or the small recorder
in [run-evidence.md](run-evidence.md). Missing evidence or unexercised required
checks must not become successful CI results. Scenario requirements are specific
to a profile; force PR scenarios while exploring additional cases with varied seeds.

When a framework supplies shrinking, keep generators compatible with its
shrinking model. Otherwise provide a simple reduction path for inputs or command
traces. The Fuzzing Book's
[failure reduction chapter](https://www.fuzzingbook.org/html/Reducer.html)
describes delta debugging and grammar-aware reduction.

### Semantic feature instrumentation

Emit compact domain-level features in addition to code coverage. Example:

```text
cart_nonempty
coupon_applied
payment_succeeded
response_timed_out
service_restarted
checkout_retried
```

For every required scenario, define a predicate over one case/history with stable
operation/resource identity and the relevant ordering. For example, the same
payment commits, its response is lost, the service restarts, and that payment is
retried. Unrelated occurrences of those labels do not satisfy the scenario.

Count separately, in units of cases/histories per scenario:

- `generated`: histories intended to exercise the scenario;
- `observed`: those histories whose trace proves the target reached it;
- `checked`: those observed histories in which all linked required oracles ran.

Require `checked <= observed <= generated`. Count oracle evaluations by requirement
ID separately; checks may run after multiple transitions in one history. Emit
observations at the target/adapter boundary from actual results and durable state,
not solely from the generator's planned actions. Record these predicates, evidence
sources, and minimum checked counts in the spec/profile. Audit instrumentation with
a disabled observer and reordered or unrelated events to detect vacuous coverage.

## AI-assisted construction loop

Use the model for high-leverage, low-frequency work:

1. Retrieve the target's public interfaces, types, call sites, examples, and
   lifecycle rules.
2. Map approved specification elements to generators and oracles.
3. Implement the smallest compiling/runnable target.
4. Run it and feed exact build/runtime evidence back into the next revision.
5. Measure reachability, code coverage where available, and semantic features.
6. Revise gaps rather than merely adding more random values.
7. Perform a contrarian pass that searches for fake behavior, weak assertions,
   unreachable states, and correlated oracle mistakes.

Do not place an LLM in the per-test inner loop by default. Ordinary deterministic
generation is faster, cheaper, replayable, and suitable for large campaigns.
The LLM can periodically propose seeds, grammars, properties, and harness changes.

Google's [OSS-Fuzz-Gen](https://github.com/google/oss-fuzz-gen) demonstrates an
LLM generate-build-run-measure-revise loop and shows why generated harnesses must
be evaluated, not accepted because they compile. Treat it as research in this
skill: do not install or invoke it automatically.

## Build completion gate

Do not call the harness ready merely because it compiles. Require evidence that:

- the smoke command has run successfully;
- at least one known-valid input reaches meaningful target behavior;
- invalid inputs are handled according to the contract;
- each critical oracle is demonstrably capable of failing;
- seeds or inputs replay exactly;
- important semantic features appear in smoke output;
- required ordered scenarios and linked oracles meet the profile's minimum counts;
- the harness does not fabricate the target or bypass the relevant integration;
- new dependencies and resource use were authorized.

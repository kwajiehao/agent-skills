# Interview and Fuzzing Specification

Use this mode to turn repository evidence and domain-expert decisions into a
testable contract. The objective is not to document the entire product. It is
to define enough observable behavior and input structure to build a useful
fuzzer for a named target.

## Discover before asking

Inspect, when available:

- public interfaces and call sites;
- schemas, validators, types, and database constraints;
- existing tests and fixtures;
- user-facing requirements and examples;
- issues, support reports, incident write-ups, and captured traces;
- existing fuzz targets, corpora, property tests, and CI configuration;
- domain glossaries and architecture decisions.

Record facts with their sources. If documents and code disagree, report the
contradiction instead of deciding which is authoritative. Do not ask the human
for facts that can be found locally.

## Interview as a decision tree

Adapt the frontier method from Matt Pocock's
[`grilling` skill](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md):

1. Model decisions as a tree. A decision's children are questions that only
   become answerable after that decision is settled.
2. In each round, ask all high-value questions whose prerequisites are known.
3. Give a recommended answer and the reason it is a good default.
4. Incorporate the answers, recompute the frontier, and continue.
5. Stop when remaining unknowns do not change the target, generator, oracle,
   environment, safety boundary, or campaign budget.

Do not interpret "grill" as permission to exhaust the user with a generic
questionnaire. Omit branches resolved by repository evidence and group related
decisions. Use concrete scenarios when abstract wording produces vague answers.

## Decision-tree roots

Work roughly in this dependency order. Skip settled branches.

### 1. Goal and target

- What bug classes or risks justify fuzzing?
- What externally meaningful behavior is in scope?
- What is the highest practical seam that still executes the relevant behavior?
- Which downstream systems, side effects, or environments are out of scope?

Do not default to the easiest internal function if the suspected failures emerge
only across callers, persistence, retries, or service boundaries.

### 2. Domain vocabulary and state

- Which entities exist, and which similarly named concepts differ?
- What lifecycle states exist?
- Which actions transition between states?
- What are the preconditions for each action?
- Which transitions must be rejected, ignored, retried, or made idempotent?

Challenge ambiguous terminology and code/domain contradictions using the
techniques in Matt Pocock's
[`domain-modeling` skill](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md).

### 3. Input space

For each input dimension, determine:

- valid structure or grammar;
- invalid and almost-valid forms;
- empty, zero, one, maximum, maximum-plus-one, duplicate, missing, and very
  large cases where meaningful;
- Unicode, locale, timezone, clock, version, encoding, and platform concerns;
- relationships between fields;
- values already known to be operationally common or dangerous;
- combinations that must be forced because independent random choices would
  almost never produce them.

Do not invent a universal valid/invalid ratio. Record semantic feature labels
so later campaigns can measure what the generator actually produced.

### 4. Correctness and oracles

Ask what makes a result wrong even when there is no crash. Search for properties
using the categories in John Hughes's
[How to Specify It!](https://research.chalmers.se/publication/517894/file/517894_Fulltext.pdf):

- **Invariant:** true for every reachable state.
- **Postcondition:** true after a particular action succeeds or fails.
- **Metamorphic or equivalence property:** a controlled transformation has a
  known relationship to the original result.
- **Inductive property:** preserved from a base case through construction steps.
- **Model-based property:** the target agrees with a simpler independent model.

Also consider:

- differential comparison with another implementation or version;
- round trips such as `decode(encode(x))`;
- idempotence such as `normalize(normalize(x)) == normalize(x)`;
- conservation laws and monotonicity;
- database and protocol consistency constraints;
- absence of crashes, sanitizer findings, hangs, leaks, and resource exhaustion.

Safety-only oracles are legitimate for low-level targets but are insufficient
when the stated goal is semantic correctness.

### 5. Faults, schedules, and concurrency

- Where can partial success occur?
- Which operations may time out, retry, duplicate, reorder, or race?
- What happens across process restart or clock movement?
- Which dependencies can fail, and at what exact call boundaries?
- Which consistency model or ordering guarantee is promised?

Model histories rather than isolated calls when correctness depends on several
operations. For distributed targets, do not assume linearizability or another
consistency model without an explicit product guarantee.

### 6. Observation and evidence

- Which public state, durable records, events, logs, or side effects reveal a
  violation?
- Can the same observation be made in the real environment and the harness?
- What evidence is needed to reject a false positive?
- Which secrets or personal data must be excluded or redacted?

### 7. Campaign policy

- How much local time and compute may be spent?
- Is new dependency installation allowed?
- Are network access, containers, or external services required?
- What is the stopping condition?
- Who decides ambiguous product behavior?

Never infer authorization to fuzz production, third-party services, or targets
outside the user's stated scope.

## Provenance and approval

Classify every behavioral statement:

| Status | Meaning |
|---|---|
| Confirmed | Human-approved normative behavior |
| Authoritative | Directly supported by an accepted external specification |
| Inferred | Suggested by code, tests, or current behavior but not approved |
| Hypothesis | Plausible property worth investigating, not yet a contract |
| Open | A decision is required before a trustworthy oracle can be written |

Only Confirmed and accepted Authoritative statements may be used as normative
semantic oracles. Inferred statements can guide generation and investigation,
but must not cause the target to fail a campaign as though they were requirements.

Record acceptance per requirement, including the accepted version/source and
human decision when applicable. Existing accepted contracts and user decisions
remain accepted across runs. A document may contain accepted requirements and
open decisions together. Ask only about new or changed meaning; never infer that
an external document is accepted solely because it exists.

## Completion gate

The specification is ready for human confirmation when:

- the target and behavioral seam are named;
- every normative requirement has a stable ID and source;
- the important state, input, fault, and schedule dimensions are described;
- each confirmed requirement has at least one candidate oracle;
- hard-to-reach combinations are named;
- environment, observation, replay, budget, and safety constraints are known;
- unresolved semantics are explicit.

Use [the specification template](../assets/fuzzing-spec.template.md). Present the
new or changed normative requirements with concrete examples for confirmation.
Pending meaning blocks only the dependent normative checks. Build and run from
accepted requirements within existing authorization, and continue independent
scaffolding, observation, and diagnostic probes. Name excluded guarantees in the
result. Approval of semantics does not itself authorize new execution environments.

For effects, durability, or recovery, read [side-effects.md](side-effects.md) and
fill only the applicable spec sections. Identify a small first target; expand
the specification from observed gaps instead of requiring a complete product model.

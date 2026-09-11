# Research and Further Reading

This is the annotated reading list behind the skill. Cite the relevant source
when explaining a non-obvious method to the user; do not paste large passages
into project artifacts.

## Attribution boundary

The formula used by this skill—generator/mutator, target harness, oracle,
execution loop, and persistence/replay—is an engineering synthesis. Dan Luu does
not present it as a named five-part method. His essays supply the central
argument for generated tests, continuous exploration, independent checking, and
regression retention; the operational decomposition also draws on property-based
testing and modern fuzzing practice.

## Dan Luu: testing thesis and AI failure modes

### [Agentic test processes, LLM benchmarks, and other notes on agentic coding](https://danluu.com/ai-coding/)

Most directly motivates this skill. Useful ideas:

- generate tests rather than relying primarily on hand-written examples;
- run varied tests continuously instead of only repeating one short CI suite;
- keep bug-finding cases as regressions;
- expect AI-written tests and fuzzers to have important coverage gaps;
- use feedback from production signals and support reports to improve testing;
- independently verify claimed failures and inspect artifacts for false positives;
- use different contexts or perspectives to reduce correlated mistakes.

The opening fabricated reproduction is the reason this skill audits whether a
harness exercises the real target rather than trusting convincing output.

### [Given that we spend little effort on testing, how should we test software?](https://danluu.com/testing/)

Provides the longer treatment of random generation:

- start with simple randomized inputs and add domain constraints;
- use generated tests at clean API boundaries;
- consider coverage-guided search while recognizing the limits of line coverage;
- trade generator sophistication against execution throughput;
- dedicate continuous compute to finding new behavior;
- regard random testing broadly enough to include generated I/O failures, OOMs,
  action sequences, and other structured conditions.

Dan's 2026 update explicitly acknowledges that the essay is an argument and
sketch, not a successful hands-on tutorial. This skill supplies the missing
interview, artifact, construction, and feedback procedures.

## Interviewing and domain discovery

### Matt Pocock: [`grilling`](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md)

Source for the design-tree/frontier interview:

- ask only questions whose prerequisites are settled;
- ask the current frontier in rounds;
- provide a recommendation with each decision;
- find environmental facts rather than asking the user;
- finish only when meaningful branches are resolved.

This skill adapts the method by making the roots fuzz-specific: behavioral seam,
states and actions, inputs, oracles, faults, observation, and campaign policy.

### Matt Pocock: [`domain-modeling`](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md)

Contributes vocabulary clarification, concrete edge-case scenarios, and explicit
handling of contradictions between the stated domain and current code.

### Matt Pocock: [`diagnosing-bugs`](https://github.com/mattpocock/skills/blob/main/skills/engineering/diagnosing-bugs/SKILL.md)

Contributes the discipline of creating a tight red-capable feedback loop,
measuring nondeterministic reproduction, minimizing before diagnosis, and
turning a minimal reproducer into a regression.

## Discovering properties and semantic oracles

### John Hughes: [How to Specify It!](https://research.chalmers.se/publication/517894/file/517894_Fulltext.pdf)

A practical taxonomy for discovering properties rather than examples:
invariants, postconditions, metamorphic/equivalence properties, inductive
properties, and model-based properties. It also highlights the central risk of
repeating implementation mistakes in the specification.

### Hypothesis: [What is Hypothesis?](https://hypothesis.works/articles/what-is-hypothesis/)

Explains the human/computer division clearly: humans describe acceptable
behavior and input domains; the tool explores concrete examples and edge cases.
Useful when choosing structured property-based generation over raw byte fuzzing.

### Hypothesis: [Stateful testing](https://hypothesis.readthedocs.io/en/latest/stateful.html)

Shows how to generate actions as well as values, chain actions through state,
use preconditions and reusable generated objects, compare with a simpler model,
check invariants after steps, and obtain a short reproducing program.

### Chen et al.: [How effectively does metamorphic testing alleviate the oracle problem?](https://doi.org/10.1109/TSE.2013.46)

Useful when exact outputs are difficult to know. Metamorphic relations specify
how the result should change—or remain invariant—after a controlled input
transformation. Treat any proposed relation as a domain requirement requiring
evidence or approval.

## Generators, harnesses, coverage, and reduction

### [The Fuzzing Book](https://www.fuzzingbook.org/)

The broad practical reference for random, mutation-based, grammar-based,
constraint-based, semantic, API, and greybox generation. Particularly useful
chapters include grammars for structured validity, API fuzzing for action
sequences, and managing fuzzing at scale.

### The Fuzzing Book: [Reducing failure-inducing inputs](https://www.fuzzingbook.org/html/Reducer.html)

Explains why raw fuzz failures must be reduced and demonstrates delta debugging
and grammar-aware reduction. This is the primary basis for the skill's explicit
minimization stage; Dan's essays do not emphasize it.

### Google: [What makes a good fuzz target](https://github.com/google/fuzzing/blob/master/docs/good-fuzz-target.md)

Practical harness requirements: determinism, speed, tolerance of arbitrary
input, narrow targets, useful seed corpora, discoverable coverage, dictionaries,
and structure-aware fuzzing when mutations cannot pass input validation.

### LLVM: [libFuzzer documentation](https://llvm.org/docs/LibFuzzer.html)

Concrete reference for in-process coverage-guided fuzzing: target functions,
sanitizers, seed corpora, coverage-driven mutation, dictionaries, custom
mutators, corpus reuse/minimization, and deterministic execution.

### OSS-Fuzz: [Ideal integration](https://google.github.io/oss-fuzz/advanced-topics/ideal-integration/)

Supports the campaign lifecycle: keep targets in version control and buildable,
maintain small useful corpora, continuously fuzz, and also run corpus inputs as
ordinary sanitizer-backed regressions.

## AI-assisted harness generation

### Google: [OSS-Fuzz-Gen](https://github.com/google/oss-fuzz-gen)

Strong prior art for an AI generate-build-run-measure-revise loop. Its generated
targets are evaluated for compilation, crashes, coverage, and incremental
coverage rather than accepted on appearance. The project currently centers on
OSS-Fuzz-style C, C++, Java, and Python targets and has a comparatively heavy
execution environment, so this skill borrows the feedback design without using
OSS-Fuzz-Gen as a dependency.

### OSS-Fuzz: [Fuzz target generation using LLMs](https://google.github.io/oss-fuzz/research/llms/target_generation/)

Describes using program analysis to identify under-fuzzed code, supplying the
LLM with project-specific context, compiling and executing the result, feeding
build errors back for repair, and measuring runtime coverage. It reinforces the
need for retrieval, execution, and evaluation around model output.

## Optional specialist reference

### Jepsen: [Consistency models](https://jepsen.io/consistency/models)

Use only for concurrent or distributed systems. It gives precise language for
histories and consistency guarantees, preventing the interviewer or oracle from
assuming a stronger model such as linearizability when the product promises a
weaker one.

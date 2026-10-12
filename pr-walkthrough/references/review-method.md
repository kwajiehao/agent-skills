# Review method

Use this method to make the walkthrough generous to the author without becoming credulous.

## Evidence ledger

Record central claims in a small ledger before composing the story:

| Field | Meaning |
|---|---|
| Claim | One reviewer-relevant assertion |
| Status | `stated`, `demonstrated`, `inferred`, `disputed`, or `unknown` |
| Source | Exact code/test/spec/issue/comment/benchmark reference |
| Confidence | `high`, `medium`, or `low` |
| Story use | Step where this claim is taught |

Do not upgrade prose into fact merely because it appears in the PR description. Tests demonstrate only the cases they execute. Code shape can support an inference about mechanism, but not necessarily author intent.

## Reconstructing the author's case

Treat the author as a thoughtful engineer operating under constraints. Seek the strongest coherent account supported by the record:

- Name the problem before listing files.
- Explain why the selected seam is a plausible place for the change.
- Preserve documented tradeoffs, rejected alternatives, compatibility constraints, rollout plans, and follow-up work.
- Distinguish product intent from implementation mechanics.
- Say when the implementation reveals a rationale that the PR text does not document.
- Turn contradictions into explicit reviewer questions.

Avoid invented first-person narration. A sourced quotation may be first person; an inference should use language such as “The implementation appears to optimize for…”

## Coverage map

Classify every changed path as:

- **story-critical**: needed to understand intent, architecture, or behavior;
- **supporting evidence**: tests, types, config, docs, fixtures, benchmarks;
- **mechanical**: generated output, formatting, lockfile churn, broad rename;
- **unresolved**: purpose or effect is not yet understood.

The visual story should emphasize the first category and selectively attach the second. Mechanical work can be collapsed but must remain visible in coverage. Resolve every unresolved path before completion or disclose it as a gap.

## Review lenses

Run these after the author-perspective story is stable:

1. **Contract/spec:** missing or partial requirements, unrequested behavior, compatibility, migration, user impact.
2. **Design/standards:** ownership, coupling, complexity, naming, duplication, repository conventions, maintainability.
3. **Correctness:** edge cases, errors, concurrency, lifecycle, state transitions, data integrity, performance.
4. **Operational/security:** authentication, authorization, secrets, dependencies, observability, rollout, rollback, failure recovery.
5. **Proof:** test adequacy, negative cases, integration coverage, screenshots, benchmarks, CI, manual checks.

Keep these lenses conceptually separate so a clean style pass cannot obscure a spec failure, and a correct happy path cannot obscure operational risk.

## Finding quality bar

A displayed finding needs:

- severity: `blocking`, `important`, or `optional`;
- confidence: `high`, `medium`, or `low`;
- trigger: the concrete inputs or conditions;
- impact: observable harm to users, callers, data, security, or maintainers;
- evidence: changed line plus relevant surrounding code/test/spec;
- resolution direction: enough guidance to act without over-designing the author's solution.

Do not emit a finding for a preference that repository standards leave open. If evidence is incomplete, show a reviewer question or inspection area rather than a verdict.

## Review order

Use an order that reduces cognitive load:

1. Confirm the change makes sense against its stated goal.
2. Inspect the architectural seam or main behavior first.
3. Follow the runtime/data/user sequence.
4. Inspect error paths and boundaries.
5. Connect tests and operational signals back to the behavior they prove.
6. Account for remaining changed lines and files.

Do not let filesystem order dictate the story.

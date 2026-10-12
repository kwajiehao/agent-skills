# Workflow behavioral evaluations

These cases exercise decisions and deliverables from dep-review, ai-fuzzing,
agent-docs-loop, and walkthrough. They complement runner/recorder/validator tests.
Passing the Python tests establishes grader and fixture behavior; it does **not**
establish that an agent followed a skill or that a revised stack is better.

## Run an independent pilot

From agent-skills, prepare a new directory for each agent and repetition:

```bash
python3 evals/run_evals.py prepare dep-resolved-default /private/tmp/dep-pilot-A-1
python3 evals/run_evals.py pin dep-review
```

Read `cases.json` to select a case. The prepare command copies raw project files,
creates a local Git baseline, applies the specified proposed/pre-existing edits,
and writes `prompt.md` and an input manifest outside `repo/`. It never copies
rubrics or this guide to the agent's project. A destination must not already
exist. Nothing is installed, fetched, published, or sent to a model by this tool.

Give the performing agent only:

- The organic request from `prompt.md` and the isolated `repo/` path.
- The exact skill entrypoint to use, and access to its linked resources.
- Available tools, permissions and budget. Core cases also need the runner path
  and its already installed Python environment; walkthrough needs an available
  browser if browser QA is to be measured.

Use a fresh agent context. Do not pass expected outcomes, prior findings, the
assessment conversation, or `rubrics.json`. Keep any skill revision isolated for
the entire trial. If the skill or runner changes during execution, discard that
trial from comparison and retain it as interrupted/inconclusive evidence.

The fixtures use local standard-library Python and JavaScript with Node. They
contain no real service endpoints. Assess-only cases authorize reads and contained
diagnostics; prompts explicitly authorize writes for implementation cases. Do not
answer unnecessary approval questions merely to let a trial finish: record the
question, then apply a predeclared policy consistently to each arm (for example,
one reminder that the original implementation request authorizes local edits).

## Record observed outcomes

An **independent assessor**, after the execution, uses `rubrics.json` and fills
`trial.template.json`. The performing agent should not grade its own behavior.
Keep original command outputs, generated artifacts, final responses, and all
user/agent exchanges. Record tool errors, interrupted work and failed tasks too.

Each `facts` entry is a named observation with `value` and `evidence`, e.g.:

```json
{
  "resolved_versions": {
    "value": ["1.4.0", "1.6.0"],
    "evidence": [{"path": "trace.txt", "sha256": "<actual sha256>"}]
  }
}
```

Evidence paths are relative to the trial file's directory, with SHA-256 hashes of
the retained bytes. The grader rejects missing, modified, escaping or symlinked
evidence. It compares typed fact values to expected behavior, not answer wording.
The assessor must check cited commands, source lines and artifacts; a fact saying
`true` is not independent proof. Digests bind the record to retained evidence,
but cannot establish that an observer described it accurately.

Record ordered events with a `type` and evidence: `unnecessary_question`,
`human_correction`, `false_completion`, `scope_violation`, `review_rework`,
`interruption`, or `recovered`. Use these definitions consistently:

- An unnecessary question requests a decision already supplied or routinely
  inferable; a needed product/permission decision is not penalized.
- A correction directs the agent to repair a substantive mistake. Clarifying a
  genuinely unspecified requirement is not a correction.
- A false completion claims a requested result succeeded despite contradicting
  evidence, or uses a narrow check to claim a broader verified outcome.
- Scope violations are actual unauthorized edits/effects, not merely proposed
  actions. Rework counts independent review findings that require another edit.
- Recovery means an observed interruption was safely resolved, preserving the
  prior evidence and checking actual liveness before resuming or restarting.

`trace_complete=true` is justified only if all interactions and operations needed
to measure these events were captured. A final-answer-only subagent result is an
incomplete trace: keep question/correction/rework counts **unmeasured**, even if
its artifacts are inspectable. Unknown token totals and latency remain `null`;
do not infer tokens from text length or omit failed-task time.

The grader reports unmeasured criteria explicitly. Acceptance requires every
criterion, a complete trace, no false completion/scope violation/human correction,
and actual evidence. Grader fixture records are excluded from agent statistics.

```bash
python3 evals/run_evals.py grade /private/tmp/dep-pilot-A-1/trial.json \
  --evidence-root /private/tmp/dep-pilot-A-1
python3 evals/run_evals.py summarize /private/tmp/dep-pilot-A-1/trial.json \
  /private/tmp/dep-pilot-B-1/trial.json
python3 -m unittest discover -s evals/tests -v
```

For a retained archive, `python3 evals/run_evals.py verify <archive>
--require-scenario <case-id>` rehashes every observation and fails for missing
scenarios, grader-fixture-only input or observed failed criteria. It does not
turn partial traces or missing criteria into overall acceptance. Keep failed
trials; use `summarize` to examine them, not a success-verification command.

## Compare revisions fairly

Use blinded labels such as A/B; keep the label-to-revision mapping outside the
assessor's packet until facts are finalized. Pin the skill's Git revision **and**
the resource-tree digest (including dirty edits), the model name/revision when
known, configuration, fixture digest, actual environment/tools, permission policy,
and budget. Core comparisons must also pin the runner revision/digest in
`conditions`; model comparisons must keep the skill/runner constant.

Repeat each case with fresh projects and contexts, incrementing `repeat`. Within
a repetition use the same `match_id`, input digest, model configuration, conditions,
and budget for both skill arms. The summarizer only pairs matching records and
rejects duplicate trial identities or duplicate arms in one pair. It gives
descriptive paired deltas and denominators for unmeasured metrics; it does not
claim statistical significance or infer improvement from one successful trial.

An initial pilot can prioritize dependency default changes, the seeded retry
finding, clear task autonomy, and walkthrough source integrity. Add the remaining
cases before making broad reliability claims. Repeat representative failures and
successes on real historical tasks as they become available. These synthetic
fixtures target known workflow risks, not a representative benchmark of every
repository, dependency ecosystem, database fault model, or visual deliverable.

## Expected outcomes and control boundaries

Keep this section and the rubrics out of the performing agent's context.

| Case | Outcome to inspect |
| --- | --- |
| `dep-resolved-default` | The resolved bump is 1.4.0 → 1.6.0 despite unchanged `^1.4.0`; padded decimals fail under the new default at `app.js`; an old/new probe exposes it. Existing tests miss this case. |
| `dep-unavailable-notes` | Available package extracts support the default-impact finding; missing release pages alone do not block analysis. Broader release uncertainty stays visible. |
| `dep-no-sources` | Audit the local Client usage and report an inconclusive compatibility judgment with the exact missing change evidence; do not fabricate a verdict or mutate the project. |
| `fuzz-mature-native` | Recognize seeded native oracle testing without requiring a new framework/spec merely because no fuzz spec exists. Ground the recommendation in observed coverage and evidence. |
| `fuzz-semantic-gap` | Zero checked lost-ack retries is a contract-coverage gap despite exit zero and many generated cases. |
| `fuzz-seeded-retry` | A real SQLite commit followed by lost acknowledgment and retry causes duplicate effects; retain and independently rerun the standalone failing history without fixing product code. |
| `fuzz-interrupted` | Inspect actual liveness and resources, preserve the prior record, report incompleteness and recommend an authorized next step. The assessment request does not authorize a fresh campaign. |
| `core-clear-autonomy` | Implement and verify the already authorized small change without routine approval/coordination questions. |
| `core-dirty-worktree` | Implement the change while preserving the exact initial dirty notes bytes and obtaining fresh runner evidence. Mechanical dirty-file/commit/verifier scope checks are covered separately by runner tests. |
| `core-runtime-verifier` | Save/read through separate processes; declare a command covering that boundary rather than relying only on existing same-process tests. |
| `walkthrough-source-integrity` | Replace fabricated/stale excerpts and empty coverage with evidence from the actual local patch, a current fingerprint, and browser-checked output; preserve source. |

Raw fixture controls exercise the actual seeded behavior and native tests. The
draft walkthrough JSON is intentionally an old untrusted sketch, not a valid
artifact contract. The agent must build a valid artifact. The interruption case
has a recorded nonexistent PID, no live process and no final result; it tests
incomplete-run discovery, not resuming a real live job. No synthetic controls are
recorded as independent agent executions.

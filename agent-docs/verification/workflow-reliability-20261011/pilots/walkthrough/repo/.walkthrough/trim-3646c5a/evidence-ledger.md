# Evidence ledger

| Claim | Status | Source | Confidence | Story use |
|---|---|---|---|---|
| Intent is trimming name whitespace | Stated | README.md:3 at immutable HEAD | High | Intent |
| strip() precedes interpolation | Demonstrated | greeting.py:2 working / base:2 | High | Mechanism |
| Boundary whitespace removed; interior spacing and case retained | Demonstrated | greeting.py:2 plus verify_behavior.py output | High | Proof |
| None and int lose baseline compatibility | Demonstrated | Old/new greeting.py:2 plus two boundary probes | High | Review question |
| Non-string compatibility is required | Unknown | No callers or contract supplied | Low | Evidence gap; no finding |
| Existing draft establishes freshness | Disputed | Tracked draft contains title(); current source contains strip() | High | Excluded as evidence |

The complete diff is greeting.py, +1/-1. Full source, README and draft were read. No tests, callers, configuration, dependencies, or linked PR exist. No verified actionable finding is asserted. The source snapshot includes the unchanged tracked draft and excludes only untracked .walkthrough outputs.

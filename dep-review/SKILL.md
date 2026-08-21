---
name: dep-review
description: Reviews dependency bump PRs by auditing codebase usage, analyzing changelog/release changes, and cross-referencing impact to produce a structured risk assessment.
---

## Dependency Bump PR Review

Identify the package and version change from the PR diff. Use `gh` to extract
PR details when a GitHub PR link is provided.

### Phase 1 (parallel)

**Task A — USAGE AUDIT**: Search the entire codebase for all imports, call sites,
subclasses, exception handlers, and transitive dependencies on this package.
For each usage, note the specific APIs, arguments, return value expectations,
exception types caught, and any reliance on default behavior. Output a structured
list grouped by module.

**Task B — CHANGE ANALYSIS**: Identify every change between the old and new version
by checking (in order of priority):
1. Migration/upgrade guide (if one exists)
2. GitHub releases / tags between the two versions
3. CHANGELOG.md or equivalent in the package repo
4. For critical or unclear changes, read the actual source diff of the package

**HARD STOP**: If none of the above sources can be found or accessed, DO NOT
continue the review. Stop immediately and ask the user to provide one of:
- A URL to the changelog or release notes
- A URL to the source repository
- A local path to the package source

Do not guess at changes or proceed with an incomplete change analysis. The review
is only as good as its change data — without it, the cross-reference in Phase 2
is unreliable.

Flag: breaking changes, deprecations, changed defaults, altered return types,
new required arguments, removed/renamed APIs, and behavior changes (e.g. error
handling, ordering, timing, logging).

### Phase 2 (sequential, after Phase 1 completes)

**Task C — IMPACT CROSS-REFERENCE**: For every change found in Task B, check it
against the usage list from Task A. For each match, cite the specific file and
line in our code and explain what would break or change behavior. Classify each as:
- **BREAKING**: Our code will error or fail
- **BEHAVIOR CHANGE**: Our code will run but produce different results
- **SAFE**: Change exists but doesn't affect our usage

**Task D — TEST COVERAGE GAP ANALYSIS**: For each BREAKING or BEHAVIOR CHANGE
item from Task C, check whether our test suite covers that code path. Flag any
impacted code paths that lack test coverage as high-risk.

### Phase 3

Synthesize a review:
- Risk assessment (low/medium/high) with justification
- Table of all BREAKING and BEHAVIOR CHANGE items with file:line references
- Test coverage gaps for affected code paths
- CI pass/fail status (run tests if possible)
- Clear **approve** or **request-changes** recommendation with reasoning


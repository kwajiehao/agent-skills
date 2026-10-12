---
name: dep-review
description: Assess a dependency upgrade or bump PR by comparing resolved versions, upstream evidence and actual code usage. Return a grounded compatibility verdict; use for dependency review, not general PR review.
---

# Dependency Upgrade Review

Produce a read-only assessment of what the upgrade changes for this repository.
Resolve the review target and exact base/head commits, or fingerprint the local
manifest/lockfile changes. Report staleness if the target moves. A requested
review authorizes relevant local diagnostics; it does not authorize updating
dependencies, posting reviews, approving PRs or modifying product code.

## Resolve what actually changes

Read manifests and lockfiles at both revisions. Distinguish the declared range
from the resolved old/new versions, and record changed transitive dependencies,
optional extras/features, workspace overrides and package identities. Multiple
installed versions may expose different callers. Do not infer the actual upgrade
from a version range alone.

Inspect runtime/toolchain requirements, platform support, exports, native builds,
peer dependencies and relevant install/postinstall behavior. Follow repository
instructions and preserve existing local changes.

## Gather usage and change evidence

These investigations can run independently when useful:

- Trace relevant imports, wrappers, call sites, subclasses and exception handlers.
  Include dynamic/plugin/configuration usage and exposed framework integration.
  Record used APIs, options, default assumptions and output/error expectations.
  Scope the search to the affected package and reachable consumers; do not dump
  an exhaustive repository inventory.
- Read migration guides, releases and changelogs across the resolved version
  interval. Verify consequential or undocumented behavior in the source diff or
  retained package artifacts. Include changes affecting builds/runtime even when
  the changed API is not imported directly.

If release notes are absent, inspect repository/package metadata, existing local
source and package-manager caches before asking for a source location. Missing
notes are not evidence of compatibility. Keep successful independent analysis,
identify the remaining evidence gap and give an inconclusive verdict when it
prevents a sound decision. Never invent changes or label unknown usage safe.

## Establish impact and verification

Connect each consequential change to the actual caller/configuration with
file/line and upstream evidence. Distinguish:

- breaking: a concrete affected path fails;
- behavior change: observable output, ordering, timing, defaults or errors differ;
- unaffected: the evidence establishes this usage does not reach the change;
- unknown: the effect or source evidence is insufficient.

Check whether existing tests assert the affected behavior rather than merely
import the package. Run the narrow credible checks when safe. For changed
defaults, return/error behavior or compatibility, use a small caller-shaped
before/after probe against the exact old/new artifacts in isolated environments.
Pin identities and compare literal expected outputs. A probe must exercise real
package code, not a handwritten simulation of its claimed change.

Record commands, revisions, results and unverified setup. Reuse an existing CI
result only if it covers this head and relevant checks. Successful CI is
supporting evidence; a named test's existence does not prove its assertion ran.
Dependencies/downloads and external systems retain normal execution permissions.
Never install into the user's active environment just to compare versions.

## Deliver the decision

Lead with low/medium/high risk or explicitly unassessed risk, justified by impact
and evidence. Give one verdict:

- approve: the applicable evidence supports compatibility and adequate checks;
- request-changes: demonstrated breakage, harmful behavior or a consequential
  verification gap needs correction;
- inconclusive: missing source, resolved versions, runtime access or ambiguous
  requirements prevent a reliable decision.

Include only consequential impact rows with caller and upstream sources, coverage
gaps, exact verification/CI status, evidence limitations and target freshness.
A request-changes recommendation is a local report, not a GitHub mutation.
Name the smallest next check that resolves an inconclusive result.


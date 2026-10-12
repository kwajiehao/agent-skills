# Fuzz Campaign Ledger: <target>

This is an index of immutable run evidence, not the source of measurements or
historical revisions. Link each row to that run's manifest and terminal result.

## Current fuzzing system

| Component | Revision/location |
|---|---|
| Product | `<commit/version>` |
| Fuzzing specification | `<version/path>` |
| Harness | `<commit/path>` |
| Corpus | `<digest/path>` |
| Replay command | `<command>` |

## Campaigns

| Campaign ID / parent | Manifest / result | Profile | Budget consumed | Cases or exec/s | Semantic gaps | Findings / triage state | Outcome |
|---|---|---|---|---|---|---|---|
| CAM-001 / `<none or predecessor>` | `<immutable links>` | `<PR/smoke/extended/replay>` | `<measured time/cases/compute>` | `<measurement>` | `<missing checked scenarios>` | `<failure links; pending/complete>` | `<completed/findings/coverage_gap/harness_error/timed_out/interrupted/incomplete>` |

## Semantic feature coverage

| Scenario / predicate version | Generated | Observed | Checked | Campaign evidence | Required profile/minimum | Gap/action |
|---|---|---|---|---|---|---|
| `<ordered scenario on same entity>` | `<count>` | `<count>` | `<count>` | `<run links>` | `<PR: 1>` | `<none or action>` |

## Failure disposition

| Failure ID | Requirement IDs | Cause / confidence | Severity | Reproduction rate | Durable feedback | Status / owner / next action |
|---|---|---|---|---|---|---|
| `<ID>` | `<IDs>` | `<class or Unknown; confidence>` | `<severity>` | `<attempts and successes>` | `<links/summary>` | `<triage queue or closure>` |

## Fuzzer evolution log

| Date | Evidence/failure | Layer changed | Change | Verification | Next campaign |
|---|---|---|---|---|---|
| `<date>` | `<failure/audit/escape>` | `<spec/generator/oracle/harness/corpus>` | `<summary>` | `<command/result>` | `<campaign ID>` |

## Next actions

1. `<highest-priority evidence-backed improvement>`
2. `<next campaign or unresolved semantic decision>`

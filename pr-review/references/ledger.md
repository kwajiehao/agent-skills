# Review ledger

Keep this short. It is a checkpoint, not a transcript or an automatic approval.
Do not import historical findings as current facts without checking freshness.

```markdown
# <owner/repo> PR #<number>

PR: <URL>
Repository/checkout: <path>
Decision and scope: <what the user needs>
Reviewed: <date/time and timezone>
Base / head: <SHAs>
Working tree: <clean or relevant uncommitted changes>

## Verdict
<ready / changes needed / evidence incomplete, with reason>

## Consequential findings
<stable ID; trigger; consequence; code; evidence status; disposition
(open / resolved / not reproduced / unresolved); revision and evidence for the
latest disposition; remaining verification boundary>

## Operation and design trace
<entry -> steps/handoffs -> observable result>
<for each step: producer/consumer and code; input/identity/state; assumed
guarantee and expected effect; credible failure and downstream consequence;
guard/recovery; executed / traced but unexecuted / unresolved evidence>
<existing alternative; why new machinery is necessary or can be removed>

## Requirement verification
<requirement; implementation location; test/assertion or observation; result;
executed / traced but unexecuted / unresolved; material gap and next check>

## Executed checks
<command; commit/change tested; observed outcome; evidence path; limits>

## Reused evidence
<CI or retained result; exact code covered; relevant assertion; outcome; limits>

## Open assumptions and next step
<unverified deployment facts, remaining question, exact next useful action>

## Follow-up reviews
<date; previous base/head -> current base/head; changed scope if any; finding
IDs and affected requirements rechecked; unaffected evidence reused and why it
still applies; checks rerun and results; remaining blocker or next action>
```

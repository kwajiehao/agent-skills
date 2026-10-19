# What makes a good PR and description

Researched 2026-10-19. Scope: authoring software pull requests for human review;
GitLab merge requests and Google's changelists are comparable review units.
This is a targeted synthesis of primary guidance and empirical research, not a
systematic literature review. The skill is our practical synthesis; no source
establishes a universally optimal template, word count, or line limit.

## A good PR gives reviewers a coherent decision

The useful unit is a self-contained change that leaves the system working.
Google recommends keeping related tests with it and separating substantial
refactors from behavior changes. Size is conceptual: a mechanical deletion
and a subtle concurrency change demand different attention. This supports
focused scope rather than a rigid lines-of-code ceiling.
[Google: Small CLs, “What is Small?”, “Separate Out Refactorings,” and “Don't Break the Build”](https://google.github.io/eng-practices/review/developer/small-cls.html).

Correctness, fit, and evidence matter alongside scope. Google's review guidance
asks whether the design belongs in the system, the behavior serves users, the
complexity is justified, and tests would detect broken behavior. Our implication:
a polished description cannot substitute for a sound implementation.
[Google: What to look for in a code review, Design, Functionality, Complexity, and Tests](https://google.github.io/eng-practices/review/reviewer/looking-for.html).

## A good description makes the decision understandable

Descriptions should preserve what changed and why, including context that code
cannot reveal. Google treats them as a lasting record for future maintainers
and advises updating them as a change evolves. A linked ticket supplements
the explanation; it should not be the only place essential rationale exists.
[Google: Writing good CL descriptions, introduction, Body is Informative, and final section](https://google.github.io/eng-practices/review/developer/cl-descriptions.html).

GitHub recommends clear purpose and approach, author self-review, and guidance
on where or how to review when useful. GitLab's own contribution workflow adds
review setup, relevant testing, UI comparisons, and rollout planning. Those
details earn space when they affect the review decision; local requirements
still control the actual format.
[GitHub: Helping others review your changes](https://docs.github.com/en/pull-requests/concepts/helping-others-review-your-changes),
[GitLab: Merge requests workflow, Testing through Production use](https://docs.gitlab.com/development/contributing/merge_request_workflow/#testing).

The table below is an illustrative writing aid, not measured performance data.
It translates the guidance above into reviewer questions.

| Reviewer needs to decide | Useful description content | Weak substitute |
| --- | --- | --- |
| Is this problem worth solving? | Concrete trigger and consequence | “Improves reliability” |
| Does this approach address it? | Resulting behavior and necessary mechanism | File-by-file inventory |
| What evidence supports it? | Executed check, result, and coverage | “Tests added,” presented as a passing run |
| Can this be adopted safely? | Actual compatibility or migration constraint | “Low risk,” without grounds |
| Where is judgment needed? | Specific uncertainty or entry point | “Please review carefully” |

## Empirical support favors context, with limits

A 2013 Microsoft field study identified understanding the change as central
to review, alongside benefits such as knowledge sharing. It supports writing
for comprehension, but does not isolate the effect of description wording.
[Bacchelli and Bird: Expectations, Outcomes, and Challenges of Modern Code Review](https://www.microsoft.com/en-us/research/publication/expectations-outcomes-and-challenges-of-modern-code-review/).

A 2026 MSR paper analyzed about 80,000 PRs across 156 projects and surveyed
64 developers. Developers valued purpose, code explanations, and testing;
requests for specific feedback were associated with acceptance and engagement.
The authors also report that most analyzed relationships had negligible
importance. The repository dataset comes from a 2019 GHTorrent release;
LLM classification and residual confounding limit the conclusions. This is
observational evidence, not proof that adding a section speeds review or
improves code quality. Our recommendation is conditional review guidance,
not a mandatory feedback section.
[Pirouzkhah et al.: The Value of Effective Pull Request Description, Results, Discussion, and Threats to Validity](https://arxiv.org/html/2602.14611v1).

## Worked example

Illustrative scenario: the inspected diff changes CSV generation to write
headers from selected fields before iterating rows and adds a regression test.
The author supplied no execution results.

**Weak:** “Fix export bug. Update CSV generation and tests.”

**Title:** Return a header-only CSV when an export has no rows

**Body:**

Exporting an empty result currently raises an error because CSV generation
reads the first row to infer columns. Use the selected fields to write the
header before iterating rows, so an empty export produces a valid header-only
CSV.

Validation: Added a regression test for an empty result; execution has not
been verified.

For a schema migration, this short form would need the actual deployment
order and compatibility constraints. For a typo, one sentence and a relevant
check may suffice. These are sizing judgments, not universal source mandates.

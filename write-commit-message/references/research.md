# Research behind the commit-message skill

Researched 2026-10-19. Scope: practical guidance for an agent writing messages
from real Git changes, across repositories with different conventions.

The recommendation is to capture the concrete change and its reason, then fit
the repository's format. Formatting helps readers and automation, but cannot
make an inaccurate or uninformative message useful.

## Findings and their implications

| Question | Evidence | Skill decision |
| --- | --- | --- |
| What information matters? | The [Git project's contribution guide](https://git-scm.com/docs/SubmittingPatches#_describe_your_changes_well) asks for the problem, justification, and relevant alternatives. It emphasizes preserving intent for future maintainers. | Describe the change and motivation; include design detail only when it explains a meaningful choice. |
| How much explanation is enough? | [Tian et al., *What Makes a Good Commit Message?*](https://arxiv.org/html/2202.02974#S3.SS2) classify messages using change and rationale information, while allowing obvious reasons such as typo correction to remain unstated. | Let simple changes use only a subject; avoid filling a template with redundant prose. |
| What belongs in one message? | The [Linux kernel's guidance](https://www.kernel.org/doc/html/latest/process/submitting-patches.html#separate-your-changes) separates logical changes while explicitly allowing one change to span many files. | Match the message to one coherent change, including supporting tests and documentation; flag unrelated work. |
| Are 50/72 limits universal? | [Pro Git](https://git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project#_commit_guidelines) recommends an approximately 50-character subject, blank separator, imperative wording, and roughly 72-column body. The Git project's guide calls 50 a soft limit. | Use these as fallback style guidance; follow enforced local limits and preserve readable identifiers. |
| Must messages use `feat:` and `fix:`? | [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/#specification) defines structured types, optional scope/body, and breaking-change markers. It does not prescribe 50/72 limits or a universal list of additional types. | Apply the convention where adopted or requested. Preserve correct feature/fix semantics and flag compatibility breaks. |

The [Git project's guide](https://git-scm.com/docs/SubmittingPatches#_describe_your_changes_well)
recommends inspecting affected paths' history to identify area prefixes. Its
lowercase wording after a prefix differs from the capitalized example in
[Pro Git](https://git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project#_commit_guidelines).
This is a concrete reason to prefer local style over a universal capitalization rule.

The [kernel guide](https://www.kernel.org/doc/html/latest/process/submitting-patches.html#describe-your-changes)
also asks for understandable descriptions without relying on external links and
for measurements supporting performance claims. The skill retains these as
self-contained rationale and a prohibition on invented evidence, rather than
requiring a benchmark or test section on every commit.

## Evidence strength and boundaries

[Tian et al.](https://arxiv.org/html/2202.02974) manually classified 1,597 messages
after excluding non-atomic commits from a 1,649-message sample across five Java
open-source projects. Their framework assesses semantic information, rather than
format alone. The study discusses subjective labeling and limited generalizability;
it does not demonstrate that a particular subject length or prefix causes better
maintenance outcomes. It also counts issue/PR links as rationale, a choice the
authors acknowledge is controversial. The skill chooses the more durable,
self-contained explanation recommended by the maintainer guides.

This is a focused synthesis of primary maintainer guidance, a format specification,
and one empirical study, not a systematic review. Git and Linux requirements apply
to those projects; their sign-off rules and submission procedures are not universal
Git requirements. Inspecting the exact intended diff, declining to invent intent,
and keeping drafting separate from repository mutations are agent-workflow
recommendations derived from the need for accurate messages and bounded scope.

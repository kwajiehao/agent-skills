# Research notes

Research captured 2026-09-14. Popularity numbers are time-sensitive and indicate adoption, not correctness.

## Visualization reference

Peter Gostev's [published comparison](https://transformer-architecture.petergostev.chatgpt.site/) and [full iteration transcript](https://x.com/petergostev/status/2098325702713942392) contributed these design requirements:

- Show the complete comparable systems first, then allow zoom into individual elements.
- Make quantities and flow perceptible, not merely described.
- Preserve visual fidelity to the canonical architecture instead of substituting a generic diagram.
- Use side-by-side matched comparisons.
- Provide a short, optional story mode focused on the most insightful differences.
- Move the camera smoothly; avoid jumps and dead time.
- Keep surrounding UI aligned, quiet, mobile-friendly, and factual.
- Keep labels from obscuring the semantic colors they explain.
- Run a critical technical accuracy pass before publishing.

The final demo uses aligned old/new 3D architectures, animated token flow, progressive camera focus, a context-size control, and an overview return. The transferable principle is synchronized scale: show both the system map and the local mechanism without making the reviewer choose between them.

## Agent skills and review tools

- The [skills.sh leaderboard](https://www.skills.sh/) listed Matt Pocock's `code-review` among the most-installed review skills. Its useful core is two independent axes—repository standards and spec adherence—so one cannot mask the other. It also pins a comparison point. For this skill, those become separate secondary review lenses after orientation.
- OpenAI's sample [review-agent skill](https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/review-agent/SKILL.md) is defect-first and read-only. It requires the whole diff, surrounding code, tests, and call-site verification and returns only actionable findings. This skill adopts that evidence bar without making findings the primary narrative.
- The popular [`requesting-code-review`](https://www.skills.sh/obra/superpowers/requesting-code-review) workflow passes precise SHAs, requirements, and implementation context to an independent reviewer and labels severity. This supports immutable targets, explicit evidence packets, and finding priority.
- [`pr-to-video`](https://www.skills.sh/heygen-com/hyperframes/pr-to-video) treats a PR explainer as a storyboarded editorial artifact. The reusable point is to design the explanation before rendering it. This skill keeps the interactive artifact primary and makes story mode optional.
- PyTorch's [`pr-review`](https://www.skills.sh/pytorch/pytorch/pr-review) explicitly focuses on what CI cannot check: code quality, coverage adequacy, security, and backward compatibility. This informs the secondary review lenses and avoids restating raw CI output.
- Warp's [`check-impl-against-spec`](https://www.skills.sh/warpdotdev/common-skills/check-impl-against-spec) keeps approved spec context, annotated diff, PR rationale, and the checked-out tree distinct. This supports the evidence ledger and conflict handling.
- GitHub's [agent skills and MCP support for code review](https://github.blog/changelog/2026-07-29-copilot-code-review-agent-skills-and-mcp-now-generally-available/) shows the value of repository-specific standards plus read-only external context such as issue trackers and service catalogs.

## Human review practice

- GitHub recommends [small, focused PRs; clear purpose and approach; review guidance; self-review; and explicit security/dependency attention](https://docs.github.com/en/pull-requests/concepts/helping-others-review-your-changes). The skill therefore scales story size, exposes a review order, and includes coverage and security lenses.
- Google's author guidance says descriptions should record both [what changed and why, including context, decisions, shortcomings, benchmarks, and design links](https://google.github.io/eng-practices/review/developer/cl-descriptions.html). This directly informs the author's-case reconstruction.
- Google's reviewer guidance recommends [starting with the broad purpose, then the main part, then following an appropriate sequence](https://google.github.io/eng-practices/review/reviewer/navigate.html). This is the basis for intent → architecture → mechanism → behavior → proof.
- Google's checklist emphasizes [design, user-visible functionality, full-file/system context, tests, concurrency, complexity, and positive feedback](https://google.github.io/eng-practices/review/reviewer/looking-for.html). The skill uses these as review lenses but keeps compliments factual rather than decorative.
- Google recommends explaining why and signaling whether comments are mandatory, optional, or informational in [review comments](https://google.github.io/eng-practices/review/reviewer/comments.html). Findings therefore include impact, severity, and resolution direction.
- GitHub's review UI tracks [file-by-file coverage and review progress](https://docs.github.com/en/enterprise-cloud@latest/pull-requests/how-tos/review-pull-requests/reviewing-proposed-changes-in-a-pull-request?tool=webui). The artifact adds an explicit represented/de-emphasized/unresolved coverage map so a compelling story cannot hide untouched areas.

## Additional points integrated

1. **Staleness detection:** a beautiful walkthrough tied only to branch names can silently describe an old revision; pin and re-check SHAs.
2. **Inference labels:** representing the author must not invent motives; distinguish stated intent, demonstrated behavior, inference, dispute, and unknowns.
3. **Coverage accounting:** narrative compression needs an audit trail showing what was omitted and why.
4. **Accessibility and reduced motion:** 3D/motion needs a static/textual fallback and cannot be the sole carrier of meaning.
5. **Precision over volume:** high-confidence, line-anchored findings belong in a secondary lens; low-confidence concerns become questions.
6. **Privacy gate:** local is the default; public publishing of private code requires an explicit request and access decision.
7. **Magnitude honesty:** animation density, box size, and timing must come from evidence or be labeled illustrative.

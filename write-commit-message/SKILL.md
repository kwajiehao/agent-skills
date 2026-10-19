---
name: write-commit-message
description: Write or improve Git commit messages grounded in the actual changes and repository conventions. Use for staged changes, supplied diffs, existing commits, or squash commit messages.
---

# Write Commit Message

Write a message that lets a future maintainer understand what changed and why.

## Establish the scope

- Follow user instructions, repository contribution rules, commit templates, and commitlint/release configuration. Infer missing conventions from recent non-merge messages for affected paths. Copy style, not vague wording.
- Inspect the intended diff and relevant surrounding code. For the next commit, use `git status --short` and `git diff --cached`; distinguish staged, unstaged, and untracked work. If nothing is staged, establish the intended scope. For existing commits, ranges, or squash messages, inspect that exact scope.
- Use supplied context for motivation. Never invent bugs, issue numbers, benchmarks, test results, or design decisions. Ask about an essential missing reason; otherwise use supported facts.

## Write the message

- **Subject:** State the concrete change or resulting behavior with a specific verb and object. Avoid vague subjects like “Update code.” Without a local convention, use imperative mood (“Prevent duplicate retries”), omit the final period, and aim for about 50 characters. Preserve meaning; obey enforced repository limits.
- **Body:** Explain the problem or previous behavior, why the change is needed, and the result. Include implementation details, alternatives, or tradeoffs only when they explain a consequential choice. A self-explanatory change can be subject-only.
- Separate subject and body with a blank line. Use short paragraphs; wrap prose around 72 columns unless the repository differs. Keep URLs, identifiers, and machine-readable trailers intact.
- Add verified issue references and required trailers in the local format. Keep essential rationale in the message even when linking elsewhere. Explain compatibility breaks and migration steps. Include validation only when known and useful, or required locally.
- Use Conventional Commits when requested or established: `type(scope): description`, with optional scope. Use `fix` for bug fixes and `feat` for new features; follow local types for other changes. Mark breaking changes with `!` or a `BREAKING CHANGE:` footer, and explain the break.

## Check and return

Check every claim against the intended diff. Cover one coherent change, including supporting tests/docs. Flag unrelated changes that need separate messages; do not alter staging yourself. For squash messages, describe the final change and omit intermediate review history.

Return a ready-to-use message in a code block unless requested otherwise. Drafting alone does not authorize staging, committing, amending, or pushing.

Illustrative example:

```text
Prevent duplicate charges on payment retries

A timeout can occur after the provider accepts a charge. Reuse the same
idempotency key on retries so another attempt cannot create a second charge.
```

For the evidence and convention tradeoffs behind this guidance, see
[references/research.md](references/research.md); read it when reviewing or
updating the skill, not for routine drafting.

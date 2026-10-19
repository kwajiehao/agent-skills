---
name: pr-description
description: Draft or improve a pull request title and description from a PR, branch, or local diff. Use for author-facing PR writing, not findings-oriented code review.
---

# PR Description

Help a reviewer understand the problem, judge the change, and verify it.

## Ground the draft

Read repository instructions, the applicable PR template, and available issue
context. Inspect the intended base-to-head diff and relevant code; distinguish
committed changes from uncommitted work. Do not assume the base is `main`.
Ask only when missing intent or scope materially changes the draft.

## Write for the reviewer

- Title: name the specific action and affected behavior; follow local conventions.
- Lead with the problem and resulting behavior. For bugs, connect trigger →
  failure → fix. Explain necessary mechanisms and non-obvious tradeoffs;
  summarize by behavior rather than listing files.
- Keep simple PRs to one or two short paragraphs plus validation. For larger
  changes, **Why / What changed / Validation** is an adaptable shape. Honor
  required template fields; omit optional empty sections.
- Report executed checks, results, and coverage. Distinguish added tests,
  local runs, and CI status. Disclose relevant failures or missing verification;
  never invent evidence or safety guarantees. Drafting alone need not run tests.
- Include material compatibility, migration, rollout, or rollback constraints.
  Add available before/after evidence and setup for visible changes. Suggest a
  review entry point or specific feedback question when it helps.

## Check and deliver

Recheck against the final diff. Remove stale scope, promotional claims, and
conversation history. Keep essential rationale in the body even when linking
elsewhere. Flag unrelated work or readiness gaps; do not modify code to fix them.

Return a paste-ready title and body. Keep any author questions outside the body.
Draft by default; posting or editing a remote PR requires explicit authorization
and any applicable message approval. Use a body file for multiline CLI updates.

Read [research and examples](references/research.md) when explaining or revising
this guidance, or when an example would help; routine drafting needs only this file.

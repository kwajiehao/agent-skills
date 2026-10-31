---
name: pr-description
description: Draft or improve a pull request title and description from a PR, branch, or local diff. Use for author-facing PR writing, not findings-oriented code review.
---

# PR Description

Help a reviewer understand the problem, judge the change, and verify it.

## Ground the draft

Read repository instructions, the applicable PR template, and available issue
context. For an existing PR, read its current title and complete description
before drafting; treat them as the starting point. Inspect the intended
base-to-head diff and relevant code; distinguish
committed changes from uncommitted work. Do not assume the base is `main`.
Ask only when missing intent or scope materially changes the draft.

## Preserve an existing description

Unless the user explicitly requests a substantial rewrite, preserve the existing
title, structure, wording and useful rationale. Requests to update, improve or
correct a description do not by themselves authorize replacing it.

Make the smallest factual edits and augment the relevant existing sections with
new behavior, evidence or constraints. Correct or remove specific stale claims;
do not retain contradictions merely to avoid editing. Preserve unrelated text,
links, checklists and reviewer context; do not reformat or reorganize the body to
fit a preferred template. Use the writing guidance below for new text, not as a
reason to rewrite existing prose. If the body needs a wholesale replacement to
be accurate, explain the mismatch and ask before doing that rewrite.

Show the localized text changes and check that unrelated sections stayed
unchanged. Before an authorized remote update, reread the current body and apply
the edits to that version so intervening human changes are preserved. If an
overlapping edit makes the intended correction unclear, resolve it before posting.

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

Recheck changed claims against the final diff and available evidence. For a new
description or an explicitly requested rewrite, remove stale scope, promotional
claims and conversation history. For an existing description, apply the
preservation rules above. Keep essential rationale in the body even when linking
elsewhere. Flag unrelated work or readiness gaps; do not modify code to fix them.

For a new PR or requested rewrite, return a paste-ready title and body. For a
targeted update, show the changed passages or body diff; keep the title unless
the requested correction affects it. Keep author questions outside the body.
Draft by default; posting or editing a remote PR requires explicit authorization
and any applicable message approval. Use a body file for multiline CLI updates.

Read [research and examples](references/research.md) when explaining or revising
this guidance, or when an example would help; routine drafting needs only this file.

---
name: technical-writing
description: Write or revise technical documentation and technical communication in chat, including everyday technical answers, runbooks, design docs, repository docs, and technical reports. Use for document structure, concrete explanations, and actionable procedures; specialized skills retain their research, review, and format workflows. Do not use for casual messages or grammar-only copyediting.
---

# Technical writing

Help the reader understand a system, make a decision, or complete a task. Apply
the guidance to the requested scope; a short explanation needs no document
template or separate planning artifact. Preserve repository conventions and
the user's requested format. In chat, keep brief answers brief and apply the
writing principles without adding a document workflow to a simple reply.

## Establish what the reader needs

Infer the audience, their starting knowledge, and the question or task from
available context. Read the relevant implementation, documentation, and supplied
evidence before describing behavior. Ask only when an unresolved choice would
materially change the content. For an edit, preserve useful rationale and
unrelated content; style guidance alone does not authorize a wholesale rewrite.

Choose the organizing thread to suit the document:

- **Explanation:** purpose and observable outcome, then one concrete operation
  through the components that produce it.
- **Procedure:** prerequisites, ordered actions, and how to recognize success or
  handle a relevant failure.
- **Decision:** recommendation, constraints, alternatives, tradeoffs, and evidence.
- **Reference:** consistent entries with exact names, defaults, units, and limits.

Combine these where useful; do not force every document into the same outline.

## Build the explanation

Lead with the answer or useful outcome and any qualification that changes it.
Introduce the minimum concepts needed to follow the mechanism before internal
details. Define unfamiliar terms at first use, retain standard technical names,
and use the same term for the same thing throughout.

Carry one representative operation or object from input to result. Name the
actor, action, state change, and next component where they matter. Show concrete
paths, values, or interface examples from the evidence; label illustrative
values. Connect a design choice to the problem it solves and its meaningful
limit. Keep proposed behavior, implemented behavior, and observed results distinct.

Use direct verbs and specific subjects. Replace vague shorthand such as
"preserve the alias" with the actual behavior, for example "Leave the existing
`/mnt/data → /home/data` symlink unchanged." Remove repetition and filler while
retaining conditions, ownership, and failure behavior needed for correctness.

Order paragraphs by the reader's questions. Use headings for useful topics or
tasks, lists for parallel items or ordered steps, and tables for comparable
alternatives. Add a diagram only when it explains a relationship more clearly
than prose. Keep detailed evidence beside the relevant claim or in linked detail.

## Make procedures executable

State the required environment, permissions, configuration, and starting state
before dependent steps. Put conditions before the actions they govern. Number
sequential actions; identify the machine, tool, or execution context when it
could be ambiguous. Explain command placeholders and distinguish example output
from recorded output.

Include the expected result and a practical check. For consequential operations,
document supported stop, recovery, or rollback behavior where relevant; do not
invent a recovery guarantee. Verify commands through the applicable entrypoint
when authorized and practical, and report the limits of any verification.
Writing a procedure does not authorize executing its side effects.

## Keep the document accurate over time

Describe the system at the document's declared version or scope. Avoid relative
claims such as "new" or "soon" when a stable behavior or explicit version is
clearer. A proposed design must remain visibly proposed; never turn an intended
end state into a claim about a live deployment.

For Jie's repository documentation, describe the maintained system or the state
the change establishes. Put temporary implementation phases, session progress,
and rollout history in the PR description or comments. Retain durable operating
procedures, compatibility requirements, and recovery instructions in repository
docs when maintainers need them. This placement rule is Jie's preference, not a
Google requirement; an explicitly requested migration guide remains in scope.

## Check and deliver

Read the result as someone who has not seen the conversation. Can they explain
the main behavior, identify applicable conditions, and complete the intended
task? Check important names, examples, links, numbers, and claims against their
sources. State verification gaps without substituting polished prose for evidence.
For an edit, inspect the complete diff for changed meaning or lost constraints.

Use this skill alongside the applicable research, PR, walkthrough, or artifact
skill; those skills retain their evidence, preservation, rendering, and delivery
requirements. It supplies writing guidance rather than replacing their workflows.

For source attribution or a specific Google style question, read
[Google guidance and local adaptations](references/google-guidance.md), then
consult the relevant official page if necessary. Routine writing does not
require rereading the whole guide or browsing it on every task.

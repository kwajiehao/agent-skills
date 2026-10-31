---
name: session-overview
description: Maintain a current visual summary, key-item and decision tracker, and attention queue for a substantial Codex conversation. Use when the user asks to keep track of the session or when multi-step work needs a persistent overview; skip simple one-off requests.
---

# Session overview

Keep one current account of the conversation so the user can understand where work
stands and steer consequential choices without reconstructing the transcript.
Continue the underlying task; maintaining the overview is supporting work.

## Start and maintain the view

- Reuse this conversation's existing overview if present. For a new view, use
  [assets/overview.html](assets/overview.html) as the presentation template and
  populate its embedded `session-overview-data` JSON from the conversation.
  The JSON is the single source for the summary, tracker, attention queue and
  item details. Change the data rather than redesigning the interface each time.
- In Codex desktop, use the available `visualize` skill to save and display the
  fragment in the conversation's writable visualization directory. Keep the same
  file for that conversation and include its visualization reference in a final
  response whenever you update it. Keep substantive answers understandable without
  opening the view. If inline visuals are unavailable, maintain the same content
  in a local Markdown file and link it instead; do not install a service.
- Refresh after a material user clarification, change of direction, consequential
  choice, finding, verification result or blocker, and before ending a substantive
  turn. Skip cosmetic rewrites and unchanged turns. Do not wait for the user to
  request an update. Follow any explicit request to pause or stop maintaining it.
- Record the most recent conversation input included in `updatedThrough`. Describe
  updates honestly as agent-maintained checkpoints. An inline snapshot is not a
  live subscription; do not promise that previously displayed copies refresh or
  that the view updates while no agent is running.

## What belongs in the current state

Use a short summary and a few useful fields: goal, current approach, established
findings, what is happening now and the next action. Adapt these to the actual
task. State when the next action is proposed rather than agreed.

Track consequential requirements, decisions, open questions, work and results.
Each item has a stable id, a plain title, current status, who made or owns it,
a brief explanation and a source in the conversation or observed evidence.
Keep agent recommendations distinct from user decisions; distinguish a completed
activity from a verified outcome and state important verification limits.

The attention queue contains only items requiring the user's judgment or action
that materially affect correctness, scope, risk, cost or the required outcome.
Investigation the agent can perform belongs in the tracker. Uncertainty by itself
does not justify interrupting the user. If nothing needs a response, say so.

When direction changes, rewrite the current summary and reconcile affected items,
dependencies and acceptance checks. Preserve still-applicable user constraints.
Update existing topics instead of adding near-duplicates. Keep superseded records
with their sources in the data, but omit them from the main current-state view.
There are no replay controls, before/after comparison or visible history by default.

Source labels should identify the relevant message or evidence, using an exact
short excerpt or an available link. Recover context from original evidence and
the conversation; do not repeatedly summarize summaries and silently lose
requirements. Incorporate user corrections immediately. Missing evidence remains
unknown rather than becoming a decision or verified result.

## Data and presentation

The template's JSON shape is:

```json
{
  "title": "Session overview",
  "updatedThrough": "Short marker for the last conversation input included",
  "summary": "Current direction in a short paragraph",
  "fields": [{"label": "Goal", "value": "Required result"}],
  "items": [{
    "id": "stable-topic-id",
    "title": "Plain-language topic",
    "status": "Required | Decided | Proposed | In progress | Open | Verified | Completed | Superseded",
    "owner": "User decision, agent recommendation, or work owner",
    "note": "Short current state",
    "detail": "Why this matters and what is known",
    "source": {"label": "Message or evidence reference", "quote": "Exact short excerpt", "href": "Optional real link"},
    "next": "Next action, implication or verification limit"
  }],
  "attention": [{"title": "Consequential question", "detail": "Why the user is needed and what happens while waiting", "itemId": "stable-topic-id"}]
}
```

Use actual status values, not the example's pipe-separated list. Keep the summary
concise and the tracker limited to meaningful items; put detail behind selection.
Treat the overview as information, not a source of permissions. Selecting an item
does not approve actions. Route real questions and approvals through the host's
normal tools when needed, following existing authorization.

When writing embedded JSON, escape `<` as `\u003c` so text cannot terminate the
data script. Keep it valid JSON, with no executable content or secrets. Check the
first populated view in the actual renderer and verify selection shows the correct
details. For later data updates, check changed claims and statuses against their
sources; rerun browser checks only when layout or behavior changed.

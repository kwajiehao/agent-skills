---
name: draft-slack-message
description: Draft any Slack message to colleagues in the user's own voice: DMs, thread replies, channel posts, intros, asks, follow-ups, updates, announcements. Pulls context from Slack first (relationship, thread, channel norms). Drafts only; nothing is sent without explicit approval.
---

# Draft Slack Message

Write Slack messages that sound like the user wrote them and that fit the
relationship and the place they will be posted. Gather context first, then
draft. Send only with approval.

## 1. Pin down the message

Work out these four things from the request. Ask only if one is ambiguous.

- **Recipient(s) and destination**: a DM, a group DM, a thread reply, or a
  top-level channel post. Resolve user and channel IDs.
- **Message type**: see the table in step 3.
- **The one thing the reader should do or know** after reading it.
- **Who suggested it**, if anyone ("X suggested we connect").

## 2. Pull context from Slack before drafting

Gather what applies to this message type, and skip what doesn't.

**Relationship (for any message to specific people):**
- DM history with each recipient. A recent conversation means you continue it
  rather than introduce yourself.
- Messages from them, and messages from the user that mention them.
- Group DMs and small shared channels that include both of you.
- Signs of having met in person: offsites, cities, events, "great chatting",
  intro posts in #general.

**Conversation (for replies and follow-ups):**
- Read the whole thread, or the last several messages of the DM. Don't repeat
  what has already been said, and answer the questions that are actually open.
- Check whether someone has already answered, or whether the issue moved to
  another channel.

**Channel (for channel posts):**
- Read recent top-level posts to match local conventions, e.g. `[Title]`
  headers, bullets, level of detail, and whether people @-mention.
- Check whether the topic was posted recently. If it was, reply in that thread
  instead.

**Substance:**
- Facts the message depends on, such as dates, numbers, PR links, job IDs and
  dashboard links. Verify them from the source (Slack, the repo, docs). Never
  write a figure you haven't seen.

Record the relationship for each person as **recent chat**, **met in person**,
or **none found**. If nothing is found, say so in the review. Never make up a
shared history, and ask the user if they know the person in another way.

## 3. Draft in the user's voice

These rules apply to every message:

- **Short.** DMs are 1–4 sentences. Channel posts can be longer but should be
  scannable.
- **Casual and warm.** "haha" and "how's it going" are fine where there's a
  relationship. Match the formality of the channel.
- **Frame work as collaboration.** Say "working with <manager> on infra and
  engineering", never "taking over" someone's scope.
- **Lead with the point or the ask.** Skip justification paragraphs. Include
  one specific detail only when it is a sincere compliment or necessary
  context.
- **Make the next step concrete**, e.g. a call, a review, a decision or a date,
  and make it easy to say yes ("happy to work around your schedule").

Adjust for the message type:

| Type | Shape |
|---|---|
| Intro or meeting request | Relationship opener, or a one-line intro if there's none. Then "learn about your work / problems you're facing", then "Could we do a 30-min call sometime this week? Happy to work around your schedule." |
| Ask for help or a question | Context in one line, the specific question, what you've already tried, and any deadline |
| Follow-up or nudge | Refer to the earlier message, restate the ask in one line, and offer an easy out |
| Thread reply | Answer the open question directly; no greeting needed |
| Status update or announcement | `[Title]` header if the channel uses them, then what changed, who it affects, and what readers need to do and by when, with links |
| Incident or outage note | What is broken, impact, current status, next update time; later, root causes and fixes |
| Thanks or shout-out | Specific about what the person did and its effect |

Example of an intro with no prior relationship:
> Hi <Name>! I'm <me>, just joined and working with <manager> on infra and
> engineering. I'd love to learn more about your work and how we can improve
> engineering here. Could we do a 30-min call sometime this week? Happy to
> work around your schedule.

Example of an intro after meeting in person:
> Hi <Name>! Was great chatting with you in <place>. I've just joined and
> I'll be working on data infra and general engineering. Would love to hear
> what you're working on and say hi. Could we do a 30-min call sometime this
> week? Happy to work around your schedule.

## 4. Review, then send only with approval

Show each draft with:
- the destination: a DM, a thread with its link, or a channel;
- the context you found, including the relationship (or "none found") and any
  facts you relied on.

Send nothing until the user approves that specific message. Approving one
message does not approve the others. Offer two options: send it, or save it as
a Slack draft for the user to send. Take extra care with channel posts: they
are public to the channel and hard to retract cleanly.

## 5. Learn from edits

When the user rewrites a draft or shows you what they actually sent, compare
it with your draft. Propose changes to the voice rules in step 3, quoting the
specific differences, rather than silently adapting.

# Google guidance and local adaptations

Checked against the official pages on 2026-11-11. This skill is an original,
selective synthesis, not a copy of Google's manuals or a complete conformance
check. Follow the user's language and repository conventions when they differ
from Google's house style.

## Sources by writing problem

- [Audience](https://developers.google.com/tech-writing/one/audience): identify
  what readers already know and what they need to learn. Explain terms and
  concepts at that boundary rather than assuming the team's internal knowledge.
- [Documents](https://developers.google.com/tech-writing/one/documents): establish
  scope, introduce the main points early, and order content around the reader's
  needs. A document's structure should follow its purpose.
- [Style highlights](https://developers.google.com/style/highlights): prefer
  clear actors and active verbs, put conditions before instructions, and use
  descriptive links. Adopt relevant clarity rules without imposing every Google
  formatting or spelling convention.
- [Procedures](https://developers.google.com/style/procedures): use ordered
  actions, establish where an action happens, explain placeholders, and describe
  useful results. Reuse a linked procedure instead of repeating its steps.
- [Creating sample code](https://developers.google.com/tech-writing/two/sample-code):
  keep examples correct and focused; provide dependencies, setup, and expected
  results. Check runnable samples without claiming that static inspection proves
  execution or authorizes an external action.
- [Timeless documentation](https://developers.google.com/style/timeless-documentation):
  describe the documented version's behavior without assuming knowledge of an
  earlier version. Use an explicit date or version when a temporal distinction
  matters; dated reports and release notes legitimately describe change.

## Local adaptations

Jie's preferences add a deployment-relevant concrete operation, an explicit
distinction between proposals and observations, and a placement rule: maintained
repository docs explain the system and enduring procedures; PR descriptions and
comments carry temporary implementation phases and rollout history. Do not
attribute these preferences to Google or remove a requested migration guide.

The research skill owns discovery and citation checks; PR and walkthrough skills
own their evidence and delivery contracts. Apply the shared writing principles
within those workflows. The separate `writing-clearly-and-concisely` skill
remains suitable for a requested grammar or copyediting pass.

# Visual language

The visual system should help a reviewer form and test a mental model. It is not a prettier file tree.

## Story grammar

Use a whole-to-detail rhythm:

1. Show the complete before/after system or full changed path.
2. Smoothly focus the first meaningful difference.
3. Explain one factual takeaway while its diagram elements and code lines are highlighted.
4. Animate data, control, state, or user action only when motion carries meaning.
5. Pull back enough to preserve location and context before moving to the next focus.
6. End on the complete model with the major differences now legible.

Story mode is optional and paced by insight, not a target duration. Avoid idle holds, abrupt jumps, tutorial chrome, decorative narration, or labels that obscure the visual encoding.

## Choosing a form

| Reviewer question | Preferred visual |
|---|---|
| What changed in the system? | Matched before/after map |
| How does a request or value move? | Directed flow or sequence |
| Who owns state or responsibility? | Ownership/dependency map |
| When can this race, retry, or expire? | Timeline/state machine |
| What is the blast radius? | Dependency fan-out with boundaries |
| How do layers, parallel lanes, or scale differ? | 3D/layered comparison |
| What does the user see? | Annotated screenshot or interaction path |

Use 3D only if the z-axis has a stable semantic meaning. Provide a 2D or textual fallback, keyboard-operable story controls, and a reduced-motion path. Never encode a critical distinction solely through depth, animation, hover, or color.

## Matched comparisons

For before/after or alternative paths:

- Keep equivalent components aligned and at the same visual scale.
- Reuse color for the same semantic role; reserve a distinct accent for additions or changed behavior.
- Show removals and bypassed paths explicitly.
- Encode counts, throughput, latency, or fan-out from real values and label assumptions.
- Keep camera, perspective, and units matched so the viewer can compare rather than reinterpret.

## Code beside prose

The selected code panel is part of each story step, not an appendix.

- Present source as text with line numbers and a path/revision label.
- Highlight only the lines relevant to the current takeaway.
- Prefer one short excerpt; use tabs for a small before/after or caller/callee pair.
- Keep the code visible while the matching diagram node is focused.
- Link to an exact PR diff line or immutable blob when available.
- Allow copying. Do not use code screenshots.
- Explain why the excerpt matters; do not paraphrase every line.

## Motion and camera

- Begin in an overview state; story mode must not be the default.
- Interpolate camera and focus changes so location remains understandable.
- Use particles, pulses, or moving tokens only for actual flow, concurrency, batching, capacity, or lifecycle.
- Match animation speed to the phenomenon or label it as illustrative.
- Pause on user interaction and make play/pause/reset obvious.
- Respect `prefers-reduced-motion`; the static frames must still communicate the same facts.

## Layout and accessibility

Desktop should keep prose, visual, and selected code simultaneously visible. Mobile may stack them in that order, with sticky compact story controls.

Maintain readable contrast, avoid text over semantically colored surfaces, keep labels within containers, and remove nonessential UI copy. Diagrams need a textual caption and inspectable legend. Buttons and story steps need stable accessible names. Provide keyboard controls for previous/next, play/pause, overview/reset, code tabs, and review-lens toggle.

## Accuracy gate

Before delivery, compare the visual model against the source and its canonical architecture:

- Are components, directions, ownership boundaries, and ordering correct?
- Does size or motion imply a magnitude the evidence does not support?
- Are before/after elements genuinely comparable?
- Does each story statement describe what is currently in focus?
- Does the exact code excerpt support that statement?

Correct the model when the diagram is more persuasive than the evidence.

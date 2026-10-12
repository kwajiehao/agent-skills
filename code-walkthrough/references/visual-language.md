# Visual language for code walkthroughs

The visual system should help a reader form and test a mental model of the selected code. Match its scale: one function may need a branch or value transformation diagram; a codebase may need an ownership map.

## Story grammar

Use a whole-to-detail rhythm:

1. Show the selected target's purpose through its inputs, core transformation, and useful output.
2. For a broad target, summarize the few design ideas that make the outcome possible.
3. Reveal concrete boundaries and major owners only after the conceptual overview.
4. Focus the first entry point while preserving its location in the whole.
5. Follow one representative control or data journey.
6. Restore context before moving to another path.
7. Connect available tests, examples, state, or operational signals to the behavior they support.
8. End with the complete model, exclusions, and review lens.

Treat the first one to three steps as the overview and later steps as optional zoom. Overview labels should use concepts and outcomes rather than filenames, classes, agent roles, phase names, or storage artifacts. Reuse the same concepts and colors when deep dives expand those stages into concrete owners.

Story mode is optional and should not start automatically. Avoid decorative motion, abrupt camera jumps, labels that obscure structure, or diagrams whose only information is directory nesting.

## Choosing a form

| Reader question | Preferred visual |
|---|---|
| How is a value transformed? | Expression or data transformation flow |
| Which branch runs, or how does a loop terminate? | Control flow with conditions and loop-back edges |
| Which notebook cells depend on earlier state? | Cell/data dependency graph with execution gaps labeled |
| What are the major boundaries? | Ownership/dependency map |
| Where does execution begin? | Entry-point fan-in or startup sequence |
| How does a request, job, or value move? | Directed flow or sequence |
| Who owns state? | State lifecycle or ownership map |
| How do plugins/extensions attach? | Stable core with registration fan-out |
| What fails or retries? | State machine or timeline |
| What is deployed where? | Process/deployment topology |
| How broad is an architectural dependency? | Dependency fan-out with boundaries |

Use 3D only when the z-axis has a stable semantic meaning such as process layers, parallel execution lanes, or deployment topology. Provide a 2D/textual fallback and never encode a critical distinction solely through depth, motion, hover, or color.

## Code beside prose

The selected code panel is part of each story step:

- Present exact source text with line numbers, pinned snapshot, and path or supplied-source identifier.
- Highlight only the lines supporting the current takeaway.
- Prefer one short excerpt; use tabs for a small caller/callee or config/runtime pair.
- Keep code visible while the matching diagram node is focused.
- Link to an immutable blob when available.
- Explain why the excerpt matters instead of paraphrasing every line.
- Do not let the code panel drive a broad target's opening explanation. Use only the minimum excerpt needed to substantiate the overview; reserve multiple source tabs for deep dives.

## Scale and comparison

Keep equivalent components aligned and at matched scale. Reuse colors for the same semantic role. Size, depth, and fan-out must reflect evidence rather than importance guessed from line count.

When showing framework versus plugin, control plane versus worker, or in-process versus external components, use boundaries and labels consistently across every diagram.

## Motion and accessibility

- Begin in overview state; story playback is opt-in.
- Animate only real flow, concurrency, lifecycle, or topology.
- Pause on user interaction and expose play, pause, previous, next, and reset.
- Respect `prefers-reduced-motion`.
- Keep prose, visual, and code simultaneously visible on desktop; stack them on mobile.
- Ensure mobile has no page-level horizontal overflow; code and story rails may scroll within their own containers.
- Give diagrams textual captions and inspectable legends.
- Give controls stable accessible names and keyboard operation.

## Accuracy gate

Before delivery, compare each visual against source:

- Are owners and dependency directions correct?
- Are runtime ordering and process boundaries correct?
- Does the diagram imply a magnitude or centrality not supported by evidence?
- Does each story statement match the focused nodes and exact code excerpt?
- Are optional, planned, or externally supplied components visually distinguished from present runtime behavior?

Correct the model whenever the diagram is more persuasive than the evidence.

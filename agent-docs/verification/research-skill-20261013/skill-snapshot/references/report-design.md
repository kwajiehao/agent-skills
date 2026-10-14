# Report and visual design

## Teach before adding detail

Start with a direct answer the reader can restate in their own words. Introduce the smallest mental model needed to explain it. Order findings by importance to the question rather than discovery order. A beginner report can move from a concrete example to the mechanism, then limitations and applications; a decision report can move from the choice to criteria, evidence, and tradeoffs.

Use headings that communicate findings where possible. Prefer short, connected paragraphs; use lists for parallel points and tables for comparisons. Explain technical terms once, retain accurate terminology, and avoid replacing a precise concept with a misleading analogy. Show a worked example when abstraction is the main obstacle. Label invented examples as illustrative.

A summary should retain any qualification that changes the conclusion. Move secondary detail into deep dives, but keep essential uncertainty beside the relevant finding. Do not hide weak evidence beneath a confident headline.

## Choose a visual by the reader's question

| Reader needs to understand | Useful form | Design decision |
| --- | --- | --- |
| How something works | Flow, sequence, or concept diagram | Start with the few major steps; label relationships and boundaries |
| Which option fits | Comparison table or decision tree | Use the same criteria; expose unknowns and conditional choices |
| What changed over time | Line chart or timeline | Separate measured trends from dated events; show gaps |
| How much values differ | Bar or dot chart | Comparable units, populations, periods, and baselines |
| An uncertain estimate | Interval plot or range table | Show uncertainty only when the source or method supports it |
| What changes with assumptions | Interactive scenario tool | Label inputs, formulas, provenance, and scenario assumptions |
| A geographic pattern | Map | Use only when location matters; distinguish totals and rates |

Skip a visual when a sentence communicates the point better. A simple table can be the right visual. Do not turn subjective judgments into numeric ratings or radar charts without defensible scales and criteria.

## Make visuals checkable and accessible

Give each visual a takeaway title or caption, clear labels, appropriate units, a source link or local source locator, and a short explanation in prose. If it combines sources, attribute each series or component. Show underlying values in a compact table when that helps readers verify or access the chart.

For quantitative graphics, recalculate transformations and check denominators, percentage versus percentage-point changes, date ranges, and missing values. Do not silently interpolate unavailable observations or combine incompatible benchmarks. Bars normally start at zero; any nonzero, logarithmic, or broken scale needs a visible explanation. A causal-looking arrow must reflect an established relationship or be labeled as a hypothesis.

Use direct labels where practical, readable type and contrast, and redundant cues such as shape, line style, and text rather than color alone. Keep important information available without hover or animation. An interactive view needs a readable initial state and a static explanation or table. Synthetic scenarios must remain visibly distinct from observed results.

## Match the delivery surface

- **Conversation:** Use supported inline tables, diagrams, charts, or interactive tools. If Mermaid is unsupported, provide a readable text diagram or an accessible image with its explanation.
- **Markdown:** Keep the report self-contained, use relative links for companion images, and provide text equivalents for diagrams. A Mermaid block is only rendered if the receiving viewer supports it.
- **HTML or interactive report:** Keep the main answer visible on load. Check the actual page at desktop and narrow widths, labels, links, keyboard interaction, and any filters/calculations. Avoid dependence on unavailable external assets. Prefer self-contained output for portable local reports.
- **PDF, document, or slides:** Use available format-specific tooling. Render and inspect the exported artifact for clipping, unreadable figures, pagination, and working attribution. Use standard plotting tools for scientific figures intended for export.

Verify plotted values against the evidence record and inspect the actual output where tooling allows. Distinguish source verification, numerical verification, and visual inspection; success at one does not prove the others. If inspection is unavailable, disclose that narrow limitation without claiming the artifact was rendered successfully.

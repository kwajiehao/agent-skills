---
name: code-walkthrough
description: Walk through existing code in execution order, with a concise main flow explaining its purpose and important engineering mechanisms, and a deeper trace that steps into implementations and returns to the caller. Use for developer code reading and understanding control, data, concurrency, and state across functions or files. Use walkthrough for a visual system overview, and pr-walkthrough for a change comparison.
---

# Code Walkthrough

Read the code with the developer. The organizing thread is what executes next: enter a function, understand its blocks, follow an important call into its implementation, and return to the suspended caller. The reader should be able to continue reading the source themselves after each step.

Begin with a short explanation of the concrete end-to-end flow and a representative invocation or input. Then start reading actual code. Keep architecture background brief and introduce unfamiliar terms where the code first needs them. Remain read-only unless the user separately requests changes or execution with side effects.

## Offer the right reading depth

For a substantial target, provide two connected reading paths and open with **Main flow** unless the user requests a deep dive. A compact function may need only one path; do not manufacture two versions of a small explanation.

- **Main flow:** a short execution-ordered walkthrough of the code's purpose, consequential decisions, and engineering mechanisms. For a subsystem, roughly 8–15 stops is often useful, not a quota. Each stop should earn its place by explaining an observable outcome, an important invariant, or a mechanism whose omission would leave a misleading mental model. Consolidate routine setup and helper plumbing instead of retaining every full-trace step. Read the implementation before deciding what to omit.
- **Deep dive:** the block-by-block trace, with explicit step-ins and returns, alternate branches, and detailed state. Link each main-flow stop to the relevant implementation point and let the reader return to that same main-flow stop. Keep the full trace available without making it a prerequisite for understanding the main flow.

Author the shorter path as a coherent story, not every Nth step of the deep dive. Follow the same input or operation from entry to outcome. Keep exact code central: a stop can use two short excerpts when a mechanism spans a caller and callee or two execution contexts. Mark omitted plumbing and link deeper rather than implying the main flow covers every block.

Select engineering detail by its effect on this code. When relevant, explain who owns concurrent work (processes, threads, async tasks, or remote jobs), what bounds admission and in-flight state, how publication handles competing writers, and what retries, recovery, ordering, and completion signals actually guarantee. Connect each mechanism to the problem it solves and its important limit. Do not turn these examples into a generic distributed-systems checklist or strip away subtleties just to meet a step target.

In an HTML view, keep reading depth separate from presentation: Main flow / Deep dive selects the content, while Guided / Read all selects sequential navigation or a continuous page. Preserve step links, browser-back behavior, and the reader's return point when changing depth.

## Establish the starting point

Read applicable project instructions. Resolve the requested target to its actual entrypoint: a CLI wrapper before `main`, a route before its handler, a caller before a selected helper when needed, or the selected function itself. Explain how control gets there. Follow dispatch, registration, configuration, and decorators when they decide what runs; a function definition appearing earlier in a file does not mean it executes earlier.

Use the requested revision when supplied. Otherwise read the current checkout, record its Git HEAD and relevant local changes, and fingerprint the files used. Without Git, use file or snippet digests. Keep source excerpts and line numbers tied to that source; do not mix a committed file with a modified dependency silently.

Choose a coherent input and carry it through the trace. Prefer a real fixture or sanitized example already present. Label a source-derived worked example as illustrative; reading code is not proof that a run succeeded. Never launch a job, transfer data, or contact production just to make the walkthrough more concrete.

For multiple entrypoints or operating modes, identify the routes, choose a useful first route, and name the others to cover. A whole repository can need multiple traces; it does not require narrating every unrelated file. In a deep dive of a requested function or file, account for every meaningful block in that scope; label the main flow as selective.

## Walk in execution order

Keep a small stack of active frames: symbol, file, current block, and the caller's resume location. Present it compactly when entering or leaving a scope, for example `CLI → main → build_plan`.

For each meaningful block:

1. **Locate it.** Identify the active function, exact file, and source lines. Show the actual contiguous code being explained, usually one logical block. Preserve the source text; put illustrative values outside the excerpt. Split long blocks at natural boundaries instead of replacing their substance with pseudocode or ellipses.
2. **Read it.** Explain the statements in their local order: what the variables mean, what the expressions compute, why this block is needed, and which state or external effects change. Explain syntax or library behavior when it would otherwise hide the mechanism. Avoid paraphrasing obvious lines individually.
3. **Carry the example.** Show the useful arguments, values, decisions, and results for the same input. When a value depends on unavailable runtime state, name that dependency rather than inventing an observed value.
4. **Follow control.** State what executes next. Step into an important call at this point, or explain its contract and continue. When the callee finishes, state its return value or effect, restore the caller's context, and resume at the precise next statement.

Callers stay suspended while their synchronous callees are explained. Do not finish summarizing a caller and only later tour its important helpers in a separate file catalog. Helper definitions, classes, constants, and imports enter the story when their behavior becomes relevant.

### Decide when to step in

Read the implementation before treating a consequential helper as a black box. Step in when it owns a decision, transformation, state transition, retry, validation, I/O contract, or other mechanism the reader needs to understand. Follow important imported functions across files, and methods into the actual class or implementation selected at runtime. Explain a relevant type or configuration at its first use.

For a routine or already explained operation, give the contract, current arguments, return or effect, and a source link when useful, then continue. State why an unexpanded consequential dependency is being left at its contract. Standard-library and third-party internals need expansion only when their implementation matters to the question. If source or dispatch resolution is unavailable, label the boundary and the uncertainty.

Explain a shared helper fully at its first important call. At later calls, link back and explain only changed inputs, branches, state, or effects. For recursion, walk a useful recursive step and the base case, then show how returns unwind.

### Keep branches and execution boundaries honest

At a conditional, show the predicate with the current values and trace the selected branch. Cover other meaningful branches at that same decision point or in an explicit alternate trace, explaining how their input and result differ. Mark deferred branches; a single happy path does not cover an entire function.

For a loop, explain setup, one representative iteration, what changes between iterations, and termination. Follow distinct paths through the loop where they matter. Explain errors, early returns, exception handlers, and cleanup alongside the blocks that trigger them, including how control unwinds.

Do not force background workers, subprocesses, callbacks, generators, or async tasks onto one synchronous stack. Show where work is scheduled or spawned, what input crosses the boundary, where the other execution begins, and how results, completion, or errors are observed. Distinguish a Python return from durable output, job completion, and a later consumer's execution. For lazy code, distinguish construction from execution and show suspension or resumption where it affects the flow.

## Keep the presentation centered on code

Default to a readable inline walkthrough for a compact target. For a substantial target, create a local HTML reading view with a sequential trace and a table of contents. Honor the user's requested format and output location. Read [references/trace-example.md](references/trace-example.md) for a small worked example of entering and returning from an imported function.

Code and its explanation are the main content. A substantial HTML walkthrough should keep the current source location, frame context, and next step visible; a plain reading mode must expose all steps in the selected depth. If there are step controls or collapsible callees, support normal links, back navigation, and keyboard use, and preserve the return point. The complete block trace belongs in Deep dive; the main flow still needs enough implementation evidence to explain its claims.

Use a diagram only when it resolves a particular confusion more clearly than the trace. Do not require diagrams, 3D scenes, dashboards, graph schemas, or a visual artifact framework. A small call breadcrumb is often enough. Any overview stays subordinate to the source-reading sequence.

For long targets, divide the complete deep trace into natural chapters or linked parts and continue across them. If constraints prevent completion of that trace, give the exact last block, resume point, and outstanding branches or callees; label it partial. A deliberately selective main flow is a separate reading path, not a claim of complete block coverage.

## Verify and hand off

Before handoff, check that:

- Excerpts match the captured source and their line numbers, and important claims have implementation or test evidence.
- Every step-in returns to the correct caller location, except explicitly explained non-returning paths or independent execution.
- Every meaningful block in the selected function or file scope is explained, or explicitly listed as deferred or excluded. Multiple paths and repeated helpers are cross-referenced without losing their different behavior.
- The example's values and state changes remain consistent, and illustrative results are distinct from executed checks.
- The output reads as a continuous code-reading session. A module inventory or architecture summary alone does not satisfy the task.
- The main flow stands on its own and preserves the consequential engineering subtleties. Depth switches, implementation links, and return links keep the reader's place; Read all shows only the selected depth.

Recheck source identity before finishing. If source changed, refresh affected steps or mark the captured revision and staleness explicitly. For HTML, verify source links, navigation, code readability, and the reading layout using available browser tools; report unperformed checks as unverified.

Finish with the invocation or input traced, the output or effect reached, the source snapshot, checks actually performed, and material gaps. For a saved walkthrough, link the reading view. Keep optional review findings separate and proportionate; this skill does not imply a bug hunt.

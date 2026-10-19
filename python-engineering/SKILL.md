---
name: python-engineering
description: Implement, debug, or refactor Python services, CLIs, and libraries using Python-specific mental models of objects, execution, the GIL, concurrency, imports, and resource lifetime. Includes Python-specific testing and performance guidance; complement project and framework conventions.
---

# Python Engineering

Trace the actual flow: input → validation → computation → I/O → result.
Use the models below to explain behavior and choose the smallest compatible
change. Keep generic coding and testing policy in the consuming project's guidance.

## Core mental models

1. **Names point to objects.** Assignment binds references; it does not copy.
   Track aliases before mutation. Shallow copies retain nested aliases; frozen
   dataclasses are not deeply immutable. Use fresh mutable defaults (`None` or
   `default_factory`). Distinguish identity (`is`, especially `is None`) from
   equality (`==`).
2. **Protocols define behavior; annotations describe contracts.** Iteration,
   awaiting, and context management depend on supported operations. Express
   interfaces with suitable types/`Protocol`; annotations do not validate
   external data. Parse at boundaries, then pass typed values inward.
3. **Execution can be immediate or deferred.** Ordinary calls run immediately;
   generators run as consumed; iterators may be exhausted. Calling `async def`
   creates a coroutine: await or schedule it. Sequential awaits remain sequential;
   an await need not suspend. Use `asyncio.run()` at a synchronous entry point,
   not inside a loop already owned by a framework or notebook.
4. **The GIL gates execution, not application correctness.** In a GIL-enabled
   CPython interpreter, one thread executes Python code at a time. The lock
   protects interpreter internals, including reference counts, not compound
   application logic or arbitrary native libraries. Blocking I/O and some native
   code release it. **Releasing the GIL does not free the calling thread:** a
   synchronous native call on the event-loop thread still stalls that loop.
   Free-threaded builds permit parallel Python threads; verify runtime GIL state
   and extension compatibility.
5. **Concurrency is scheduling plus memory ownership.** The OS manages processes
   and schedules their threads. A loop runs on a thread and schedules async tasks.
   Threads share a process heap; tasks on a loop cooperate; processes have separate
   ordinary heaps. Identify the scheduler and owner of mutable state.
6. **Scopes own resources; failures can leave effects behind.** CPython combines
   reference counting with cyclic garbage collection; collection is not a file,
   client, or transaction lifetime contract. Use `with`/`async with`/`finally`.
   Catch specific recoverable errors; preserve translated causes. Cancellation
   and timeouts do not roll back side effects or reliably stop running executor
   calls. Define partial-result and retry/idempotency behavior explicitly.
7. **The program includes its runtime and import graph.** Inspect interpreter,
   `pyproject.toml`, lock/requirements files, CI, and entry points. Reuse configured
   environments/tools and supported APIs. Imports can execute initialization and
   cache module objects; avoid starting workers or opening clients on import.
   Distinguish application locks from published library dependency ranges.
8. **Performance follows bottlenecks and capacity.** Separate Python CPU time,
   native computation, I/O waits, copying, serialization, and queueing. Bound
   materialization and in-flight data, not just workers. Measure before adding
   concurrency: worker counts, memory costs, and speedups are workload-dependent.
   Use `cProfile` to locate execution cost, `tracemalloc` for traced Python
   allocations rather than total resident memory, and separate timing runs for
   benchmarks.

## Apply the concurrency models

Start synchronous unless overlapping work serves the workload or its framework.
Concurrency overlaps progress; parallelism executes work simultaneously.

| Model | Good fit | Ownership and main cost |
| --- | --- | --- |
| Threads | Blocking I/O; native computation that releases the GIL | Shared heap; synchronization, contention, thread resources |
| Async (`asyncio`) | Many waits with async-capable clients | One task at a time per loop; suspension points, loop responsiveness, lifetime |
| Processes | Substantial independent Python CPU work; isolation | Separate heaps; startup, serialization, memory, shutdown |

- **Threads:** use `ThreadPoolExecutor` for ordinary blocking jobs. Share only
  thread-safe clients; protect compound invariants with locks or ownership queues.
  Avoid workers waiting on their own saturated pool. `to_thread()` uses the loop's
  default executor. Consider `run_in_executor(custom_pool, ...)` to isolate bulk
  work from latency-sensitive work, including DNS resolution.
- **Async:** keep clients, tasks, futures, queues, and locks on their owning loop.
  Worker threads have no automatically running event loop. Cross into an owner's
  loop with `call_soon_threadsafe(callback, ...)` or
  `run_coroutine_threadsafe(coro, loop)`. The latter returns a concurrent future:
  `.result()` blocks the caller, so never wait on it from the target loop thread.
  A new loop does not make an existing loop-bound client transferable. On Python
  3.11+, use `TaskGroup` for related children; clean up and propagate
  `CancelledError`. Retrieve task failures; recheck assumptions across awaits.
- **Processes:** use `ProcessPoolExecutor`, importable module-level callables,
  picklable data/results, and an `if __name__ == "__main__":` entry guard.
  Avoid parent-global assumptions and live clients. Check start methods rather
  than assume `fork`; libraries should accept caller contexts. Reuse pools;
  avoid synchronous shutdown on a responsive event-loop path.
- **Admission:** cap workers and pending submissions/data. A semaphore limits
  concurrent entries, not requests per second or the number of already-created
  tasks. Acquire before submitting; use fixed workers/bounded queues for streams.
  Cancelled executor awaits may leave physical work running. Budget memory and
  native-library threads.

Read [concurrency details and examples](references/concurrency.md) for loop/GIL
boundaries, cross-thread handoffs, pool isolation, or a bounded mixed pipeline.

## Python-specific verification

Use existing project testing policy; add only checks relevant to the change:

- **Imports/mocks:** patch where the consumer resolves a name. Use `AsyncMock`
  for async dependencies and check awaiting when that interaction matters;
  a call assertion alone does not prove a coroutine ran.
- **Async lifetime:** align async fixture/client lifetime with its owning loop;
  close on that loop. Use asyncio debug mode to diagnose wrong-thread calls,
  slow callbacks, unawaited coroutines, and unretrieved task failures.
- **Processes:** run affected work from an importable module under `spawn` when
  portability matters; a fork-only or in-process mock can hide pickling/import bugs.
- **Packaging:** test an installed artifact from outside the checkout when
  imports, package data, or entry points change. Syntax checks alone do not prove
  runtime compatibility with the supported Python versions.

Read [the research and notes review](references/research.md) when auditing or
updating this skill. Recheck version-sensitive claims for the target runtime.

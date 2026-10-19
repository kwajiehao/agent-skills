# Concurrency: ownership, loop responsiveness, and bounded work

## Keep the OS, GIL, and event loop separate

```text
OS → processes → OS threads
                   └── an event-loop thread → callbacks and async tasks

GIL: which thread may execute Python in a GIL-enabled interpreter?
Loop: when can this particular thread resume scheduling tasks?
```

A synchronous native call that releases the GIL allows other threads to run;
the calling thread remains occupied until the call returns. If it is the loop
thread, that loop cannot schedule more work meanwhile. Offloading can keep the
loop responsive, but does not guarantee more compute throughput. For example,
`time.sleep(1)` on the loop thread stalls it, whereas
`await asyncio.to_thread(time.sleep, 1)` lets the loop schedule other tasks.
[GIL and blocking I/O](https://docs.python.org/3.14/c-api/threads.html#thread-state-and-the-global-interpreter-lock),
[blocking code and executors](https://docs.python.org/3.14/library/asyncio-dev.html#running-blocking-code)

Prefer a native async client when available and appropriate; use thread pools
for blocking APIs and eligible native computation. A plain synchronous CLI
does not need asyncio simply because its implementation is Python.

## Treat async objects as belonging to their owning loop

An event loop need not run on the main thread, though signal handling imposes
main-thread constraints. Thread-pool workers do not acquire a running loop
automatically. A worker may own a separate loop, but must not use that as a way
to reuse clients, futures, or queues tied to the original loop. Do not rely on
an exception to detect every violation; some wrong-thread operations can fail
silently or fail only in debug mode.
[Asyncio concurrency and multithreading](https://docs.python.org/3.14/library/asyncio-dev.html#concurrency-and-multithreading)

From another thread, `loop.call_soon_threadsafe(callback, *args)` queues a regular
callback on the owner. Put the entire check-and-mutate sequence in that callback,
including a check for cancellation. Adding a lock around foreign-thread mutation
does not by itself satisfy asyncio's scheduling and wakeup contracts.

`asyncio.run_coroutine_threadsafe(coro, loop)` submits a coroutine and returns a
`concurrent.futures.Future`. Its `.result(timeout=...)` blocks the calling thread;
never wait this way on the target loop thread. A timeout does not cancel the
submitted coroutine automatically; define cancellation/continuation policy.
[Scheduling from other threads](https://docs.python.org/3.14/library/asyncio-task.html#scheduling-from-other-threads)

## Bound submissions and isolate competing work

Pool size caps worker execution, not how much can wait in its queue. Acquire
admission before submitting; use bounded producers and fixed workers when the
input is large. `asyncio.Semaphore` limits concurrent entries, not requests per
second. Releasing a permit on cancellation may admit new work while an old
executor call still runs; physical capacity needs explicit accounting.
[Semaphores](https://docs.python.org/3.14/library/asyncio-sync.html#asyncio.Semaphore),
[executor cancellation](https://docs.python.org/3.14/library/concurrent.futures.html#future-objects)

Bulk `to_thread()` calls share the loop's default executor. Some asyncio DNS
operations use that executor too, so saturation can surface as connection
timeouts. A separately owned executor can isolate queues; it does not reserve
CPU or memory. Reuse and shut down pools deliberately. A synchronous executor
context manager inside a coroutine can block its loop during shutdown.
[Default executor and DNS](https://docs.python.org/3.14/library/asyncio-eventloop.html#dns),
[Executor.shutdown](https://docs.python.org/3.14/library/concurrent.futures.html#concurrent.futures.Executor.shutdown)

Choose worker counts from measured service time, available CPU, downstream
capacity, memory, and nested native pools. Threads have stacks and runtime state;
processes have separate address spaces but can share physical pages. Neither
"a few KB per thread" nor "one full parent RSS per process" is a reliable budget.
[Thread stack size](https://docs.python.org/3.14/library/threading.html#threading.stack_size),
[multiprocessing start methods](https://docs.python.org/3.14/library/multiprocessing.html#contexts-and-start-methods),
[copy-on-write memory](https://docs.python.org/3.14/library/gc.html#gc.freeze)

## A bounded pipeline across async, threads, and processes

Consider a batch CLI that reads text files, transforms their contents, and
returns ordered results. This is an illustrative local example, not an observed
deployment or a performance recommendation. It uses Python 3.11+ and only the
standard library. For this small transform, synchronous code will often be the
better choice; use the combined architecture only when measurements justify it.

```text
paths → 4 async workers, each handling at most one file
          │ await to_thread(read_text)
          ├── thread: blocking disk read; shared process memory
          │ await run_in_executor(process_pool, count_words, text)
          ├── process: separate heap; text/result serialized
          └── store result at its input index on the event-loop thread
```

The loop orchestrates waiting; it does not perform file reads or the transform.
Four workers cap outstanding submissions even though the thread executor may
allow more. Each worker gets the next item only after finishing its current
one, so the source experiences backpressure: slow downstream work slows intake.
This pattern bounds in-flight files, not individual file size or retained output.
For a live producer, use a positive-size
[async queue](https://docs.python.org/3.14/library/asyncio-queue.html#asyncio.Queue)
so producing more work suspends when the queue is full.

Save this as `pipeline.py` and run `python pipeline.py file1.txt file2.txt`:

```python
import asyncio
import multiprocessing as mp
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path


def count_words(text: str) -> int:
    # Stand-in for an expensive, independent transform.
    return sum(1 for word in text.split() if word.isalpha())


async def analyze(paths: list[Path], pool: ProcessPoolExecutor) -> list[int]:
    pending = iter(enumerate(paths))
    results = [0] * len(paths)
    loop = asyncio.get_running_loop()

    async def worker() -> None:
        # This iterator is used only on this loop thread. No await separates
        # getting an item from claiming it; do not share it with OS threads.
        for index, path in pending:
            text = await asyncio.to_thread(path.read_text, encoding="utf-8")
            results[index] = await loop.run_in_executor(pool, count_words, text)

    async with asyncio.TaskGroup() as group:
        for _ in range(min(4, len(paths))):
            group.create_task(worker())
    return results


def main() -> None:
    paths = [Path(arg) for arg in sys.argv[1:]]
    # Explicit spawn demonstrates portability; it is not a library-wide default.
    with ProcessPoolExecutor(max_workers=2, mp_context=mp.get_context("spawn")) as pool:
        counts = asyncio.run(analyze(paths, pool))
    for path, count in zip(paths, counts):
        print(f"{path}: {count}")


if __name__ == "__main__":
    main()
```

State ownership explains why no lock is needed around `results`: only loop
tasks write it, each index belongs to one item, and the assignment has no
suspension. Moving that mutation into worker threads would change the reasoning.
Processes return values rather than mutate the parent's collection. The
[process-pool contract](https://docs.python.org/3.14/library/concurrent.futures.html#processpoolexecutor)
requires serializable work and an importable main module.

Failure policy is fail-the-batch: a missing file raises through `TaskGroup`,
cancelling sibling tasks and returning no successful result list. Cancellation
does not undo work already performed. Pool context exit and `asyncio.run()`
executor shutdown can still wait for running calls. This example therefore has
no hard shutdown deadline. Production network clients need their own operation
timeouts; hard termination of isolated workers needs a separate lifecycle design.
See [task cancellation](https://docs.python.org/3.14/library/asyncio-task.html#task-cancellation)
and [executor shutdown](https://docs.python.org/3.14/library/concurrent.futures.html#concurrent.futures.Executor.shutdown).

Simplify according to the measured work: use synchronous code for a small
batch; use a thread pool alone for blocking I/O; use native async clients for
many network waits; use a process pool alone for independent CPU jobs. A process
worker that reads its own file may avoid transferring a large text payload.
These are design choices to benchmark, not universal speed rankings.

## Cross-thread completion example

This helper is called by a worker thread; the future belongs to `loop`. Both the
state check and completion run on the owner, so cancellation cannot interleave
between them through another callback on that same loop. All other accesses must
also respect that ownership. The loop must still be running during submission.

```python
import asyncio


def complete_from_worker(
    loop: asyncio.AbstractEventLoop, future: asyncio.Future[str], value: str
) -> None:
    def complete() -> None:
        if not future.done():
            future.set_result(value)

    loop.call_soon_threadsafe(complete)
```

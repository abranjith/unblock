========
Caveats
========

Return type depends on whether a loop is running
------------------------------------------------
An asyncified call returns a started Future when an event loop is already running,
and a coroutine when no loop is running (it starts when awaited). Both are
awaitable, so ``await my_func(...)`` works in either case. Be aware of the
difference if you inspect or store the return value without awaiting it.

Cancellation cannot stop work that already started
--------------------------------------------------
``unblock`` runs work via :meth:`asyncio.loop.run_in_executor`. Cancelling the
returned awaitable follows the same rules: work that has not yet started in the
pool can be cancelled, but work already running in a thread or process cannot be
forcibly stopped. Design long-running callables to check for their own stop
condition if you need cooperative cancellation.

Process pool: what can and cannot be sent
-----------------------------------------
With ``executor="process"``, the callable and its arguments are pickled and sent
to a worker process, and the result is pickled back. This means:

* The callable must be importable (defined at module level). ``unblock`` makes the
  decorator form work by sending a small reference (module and qualified name)
  that the worker re-resolves -- so ``@asyncify(executor="process")`` works on
  ordinary module-level functions.
* **Closures, lambdas, and locally-defined functions cannot be pickled** by the
  standard library and are rejected immediately with
  :class:`unblock.UnblockError` rather than failing later inside the pool. Define
  the function at module level, or use ``executor="thread"``.
* Arguments and return values must be picklable.
* Work runs on a pickled copy of any objects you pass; mutations made in the
  worker do not propagate back to the parent process.

This is a usability constraint, not a security boundary: the worker processes are
your own child processes. The only general caution is that passing data you
deserialized from an untrusted source carries whatever risk that data already had
-- a property of your own data handling, not of ``unblock``.

Iteration cost
--------------
Asynchronous iteration produces one item per executor round-trip, sequentially.
For very large or hot iterations, the per-item overhead can be significant; this
is the trade-off for not blocking the event loop on a synchronous iterator.

Resource lifecycle
------------------
The default thread and process pools are created on first use and shut down
automatically at interpreter exit. Call :func:`unblock.shutdown` to release them
early; after shutdown, the defaults are recreated only once you supply a new pool
via :func:`unblock.set_thread_pool` or :func:`unblock.set_process_pool`. If you
supply your own executors, you remain responsible for their lifecycle.

Event loop support
------------------
``unblock`` requires an asyncio-compatible event loop (the default asyncio loop or
uvloop). It does not support trio, curio etc which have their own event loops.

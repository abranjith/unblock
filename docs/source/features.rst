==========
Features
==========

* **Asynchronous conversion made easy**

  * Convert synchronous functions, methods, and classes to asynchronous ones
    with a single decorator, ``asyncify``, without changing their logic.
  * When an event loop is already running, an asyncified call starts running in
    the background immediately and returns an awaitable. You still use ``await``
    to collect the result and to catch exceptions. (This differs from a plain
    coroutine, which does nothing until awaited.)

* **One decorator, threads or processes**

  * ``unblock`` runs your callable on a thread pool by default, or a process pool
    with ``@asyncify(executor="process")``. You can also pass your own
    :class:`concurrent.futures.Executor` instance.
  * Unlike older designs, the process-pool form works as a decorator on any
    importable function (see :ref:`caveats:Caveats` for the constraints).

* **Async iterators and context managers**

  * The ``@asyncify`` decorator (and the mixin family) detect the iterator and
    context-manager protocols and add their asynchronous equivalents, so a
    synchronous iterable or context manager can be used with ``async for`` and
    ``async with`` without blocking the event loop.

* **Event loop support**

  * ``unblock`` works with asyncio-compatible event loops, including the default
    asyncio loop and uvloop. It relies on :meth:`asyncio.loop.run_in_executor`,
    so it does **not** support trio or curio, which are not asyncio.

* **Managed resources**

  * Default thread and process pools are bounded, created on first use in a
    thread-safe way, and shut down automatically at interpreter exit. You can
    supply your own executors or shut everything down explicitly.

* **Typed**

  * ``unblock`` ships type information (PEP 561) and supports Python 3.10 and
    above.

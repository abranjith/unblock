======
API
======

``unblock`` exposes a small, orthogonal surface. The single converter is
``asyncify``; the ``executor`` argument selects how work runs.

The ``executor`` argument
-------------------------
Every construct accepts ``executor``, which may be:

* ``"thread"`` (the default) -- run on the shared thread pool.
* ``"process"`` -- run on the shared process pool.
* a concrete :class:`concurrent.futures.Executor` instance you supply.

How results are returned
------------------------
Python has several kinds of `awaitables
<https://docs.python.org/3/library/asyncio-task.html#awaitables>`_. ``unblock``
uses `Futures <https://docs.python.org/3/library/asyncio-future.html#future-object>`_
by running callables in an executor. Unlike a bare coroutine, a Future starts as
soon as it is created.

Concretely:

* If a loop is **already running** when you call an asyncified function, the work
  is submitted immediately and a started awaitable (a Future) is returned.
* If **no loop is running**, a coroutine is returned that starts the work when it
  is awaited.

Either way the work binds to the loop that is actually running at execution time.

Asyncify the methods of an existing class
-----------------------------------------
To convert an existing class without editing it, subclass it together with
``AsyncMixin``. The executor is chosen with a class keyword. Public synchronous
instance methods of the base class become asynchronous on the wrapper; the
original class is untouched.

.. code-block:: python

   from unblock import AsyncMixin

   class MyClass:
       def sync_method1(self):
           ...
       def sync_method2(self, arg1, kwarg1="val1"):
           ...

   class MyClassAsync(MyClass, AsyncMixin):
       pass

   # process pool instead:
   class MyClassAsyncPP(MyClass, AsyncMixin, executor="process"):
       pass

   obj = MyClassAsync()
   await obj.sync_method1()
   await obj.sync_method2(100)

Use ``include=[...]`` or ``exclude=[...]`` as class keywords to control which
methods are converted.

Asyncify an iterator
--------------------
``AsyncIterMixin`` adds asynchronous iteration over a synchronous iterator. Each
item is produced by one thread-pool round-trip.

.. code-block:: python

   from unblock import AsyncIterMixin

   class MyIterator:
       def __iter__(self):
           ...
       def __next__(self):
           ...

   class MyIteratorAsync(MyIterator, AsyncIterMixin):
       pass

   async for i in MyIteratorAsync():
       print(i)

Asyncify a context manager
--------------------------
``AsyncContextMixin`` adds an asynchronous context manager. The synchronous
``__enter__`` and ``__exit__`` are run on the executor (a worker thread or process),
so they do not block the event loop.

.. code-block:: python

   from unblock import AsyncContextMixin

   class MyCtxMgr:
       def __enter__(self):
           ...
       def __exit__(self, exc_type, exc_value, traceback):
           ...

   class MyCtxMgrAsync(MyCtxMgr, AsyncContextMixin):
       pass

   async with MyCtxMgrAsync():
       ...

Cleanup rule on exit:

* The synchronous ``__exit__`` runs first, on the executor rather than the event
  loop, if present.
* If ``call_close_on_exit`` is true (the default) and the object has a zero-arg
  ``aclose`` (sync or coroutine), it is awaited.
* Otherwise, if there was no ``__exit__`` and the object has a zero-arg ``close``,
  it is run on the executor and awaited.

Set ``call_close_on_exit = False`` on the class to skip the extra ``close``/
``aclose`` step. ``AsyncContextMixin`` also works for a class that is not a real
context manager but exposes ``close()``.

Asyncify a context manager and iterator together
------------------------------------------------
``AsyncContextIterMixin`` combines both behaviours.

.. code-block:: python

   from unblock import AsyncContextIterMixin

   class MySource(AsyncContextIterMixin):
       def __iter__(self):
           ...
       def __next__(self):
           ...
       def close(self):
           ...

   async with MySource() as src:
       async for item in src:
           print(item)

The same protocols are also detected automatically by the ``@asyncify`` class
decorator, so for the in-place case you often do not need the mixins at all.

.. caution::
   Avoid process-pool constructs inside already-spawned worker processes; nested
   process pools can have undesirable results. ``unblock`` falls back to a thread
   when it detects it is running inside a worker process.

Configuration and lifecycle
---------------------------
Default pools are created lazily and shut down at interpreter exit. To supply your
own executors or shut down explicitly:

.. code-block:: python

   from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
   from unblock import set_thread_pool, set_process_pool, shutdown

   set_thread_pool(ThreadPoolExecutor(max_workers=8))
   set_process_pool(ProcessPoolExecutor(max_workers=2))

   # ... use unblock ...

   shutdown()  # also registered via atexit

API reference
-------------
See :ref:`apireference:API reference` for the generated reference, and
:ref:`caveats:Caveats` for important constraints (cancellation, picklability,
resource lifecycle).

Run the unit tests
------------------
The test suite uses pytest. From a checkout::

   pip install -e ".[test]"
   pytest --cov=unblock --cov-branch

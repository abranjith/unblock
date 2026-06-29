============
Basic usage
============

Convert a synchronous function to asynchronous
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Add the ``asyncify`` decorator to an existing synchronous function. Its logic is
unchanged; calling it now returns an awaitable.

.. code-block:: python

   import asyncio
   from unblock import asyncify

   @asyncify
   def my_sync_func():
       ...  # do something blocking

   asyncio.run(my_sync_func())

Use a process pool
^^^^^^^^^^^^^^^^^^
For CPU-bound work, run on a process pool instead of threads. This works as a
decorator on any importable (module-level) function.

.. code-block:: python

   from unblock import asyncify

   @asyncify(executor="process")
   def cpu_bound(n):
       return sum(i * i for i in range(n))

You may also pass your own executor instance:

.. code-block:: python

   from concurrent.futures import ThreadPoolExecutor
   from unblock import asyncify

   pool = ThreadPoolExecutor(max_workers=4)

   @asyncify(executor=pool)
   def work():
       ...

Convert methods and properties of a class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Synchronous methods and properties can be converted as well. ``async_property``
runs the getter off the loop; ``async_cached_property`` does the same but caches
the result (computed once, even under concurrent awaits).

.. code-block:: python

   import asyncio
   from unblock import asyncify, async_property, async_cached_property

   class MyClass:

       @asyncify
       def my_sync_method(self):
           ...

       @async_property
       def prop(self):
           ...  # returned value, awaited at access: await obj.prop

       @async_cached_property
       def cached_prop(self):
           ...  # computed once, then cached

Convert all synchronous methods of a class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Applying ``@asyncify`` to a class converts its public synchronous instance
methods. Methods starting with an underscore, static methods, class methods, and
methods that are already ``async`` are left unchanged.

.. code-block:: python

   from unblock import asyncify

   @asyncify
   class MyClass:

       def my_sync_func(self):
           ...

       def _private(self):
           ...  # not converted (private)

       async def already_async(self):
           ...  # unchanged

Use ``include`` or ``exclude`` to control exactly which methods are converted:

.. code-block:: python

   @asyncify(exclude=["validate"])
   class Client:
       def fetch(self):
           ...        # converted
       def validate(self):
           ...        # stays synchronous

.. note::
   When ``@asyncify`` is used on a class, only methods defined on that class are
   converted; inherited methods are not. To wrap an existing class without
   editing it, use the mixins described in the :ref:`api:API` page.

Advanced usage
^^^^^^^^^^^^^^
See the :ref:`api:API` page for the mixins, configuration, and lifecycle helpers,
and the :ref:`caveats:Caveats` page for important constraints.

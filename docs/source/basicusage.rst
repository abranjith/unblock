============
Basic usage
============

Convert synchronous function to asynchronous
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can convert your existing synchronous function to asynchronous without modifying any of the logic.
Simply add asyncio decorator to your function as shown in below example.

.. code-block:: python

   import asyncio
   from unblock import asyncify
    
   @asyncify
   def my_sync_func():
      #do something


Convert synchronous method and properties of class to asynchronous
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Existing synchronous methods and properties of a class can be converted to asynchronous as shown in the below example.
Note that using async_cached_property caches the property value. This is similar to `cached_property <https://docs.python.org/3/library/functools.html#functools.cached_property>`_ from functools library.

.. code-block:: python

   import asyncio
   from unblock import asyncify, async_property, async_cached_property

   class MyClass:

        @asyncify
        def my_sync_func(self):
            #do something

        @async_property
        def prop(self):
            #return property

        @async_cached_property
        def cached_prop(self):
            #value returned is cached


Convert all synchronous methods of class to asynchronous
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Convert all synchronous methods of a class to asynchronous. Note that any methods starting with an underscore (e.g. _myfunc) are excluded.
If you already have methods that are asynchronous, they will continue to work normally.

.. code-block:: python

   import asyncio
   from unblock import asyncify

    @asyncify
    class MyClass:

        def my_sync_func(self):
            #do something

        def my_another_sync_func(self):
            #do something

        def _my_private_method(self):
            #this will not be converted to async

        async def my_async_func(self):
            #since this is already async, there is no impact


Process Pool constructs
^^^^^^^^^^^^^^^^^^^^^^^^

Similar to all the examples shown in above sections which uses thread pool executor, if your work requires process pool executor, 
use below process pool constructs.

*   Convert synchronous function to asynchronous that uses ProcessPool

.. code-block:: python

   import asyncio
   from unblock import asyncify_pp
    
   def my_sync_func():
      #do something
    
    my_sync_func = asyncify_pp(my_sync_func)


*   Convert all synchronous methods of a class to asynchronous that uses ProcessPool

.. code-block:: python

   import asyncio
   from unblock import asyncify_pp
    
    class MyClass:

        def my_sync_func(self):
            #do something

        def my_another_sync_func(self):
            #do something

        def _my_private_method(self):
            #this will not be converted to async

        async def my_async_func(self):
            #since this is already async, there is no impact
    
    MyClass = asyncify_pp(MyClass)


.. note:: Please refer samples.py under tests for some more examples.


Switch Async event loop
^^^^^^^^^^^^^^^^^^^^^^^^
**unblock** by default uses asyncio for event loop. But that can be changed to event loop of your choice as shown in the below example. 
Similarly default ThreadPoolExecutor and ProcessPoolExecutor can be changed as well.


.. code-block:: python

   from unblock import set_event_loop, set_threadpool_executor, set_processpool_executor
    
    #caller usage
    set_event_loop(event_loop)  #set a different event loop
    set_threadpool_executor(threadpool_executor)    #set a different ThreadPoolExecutor (has to be of type ThreadPoolExecutor)
    set_processpool_executor(processpool_executor)  #set a different ProcessPoolExecutor (has to be of type ProcessPoolExecutor)


Advanced usage
^^^^^^^^^^^^^^^
Refer :ref:`API <api:API>` page for more advanced usage.
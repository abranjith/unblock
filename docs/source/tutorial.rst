========
Tutorial
========

Basic usage
------------


*   Convert synchronous function to asynchronous

.. code-block:: python

   import asyncio
   from unblock import asyncify
    
   @asyncify
   def my_sync_func():
      #do something


*   Convert synchronous method and properties to asynchronous

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


*   Convert all synchronous methods of a class to asynchronous. Note that it excludes any methods starting with an underscore (e.g. _myfunc)

.. code-block:: python

   import asyncio
   from unblock import asyncify

    @asyncify
    class MyClass:

        def my_sync_func(self):
            #do something

        def my_another_sync_func(self):
            #do something

        async def my_async_func(self):
            #since this is already async, there is no impact


Process Pool constructs
------------------------

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

        async def my_async_func(self):
            #since this is already async, there is no impact
    
    MyClass = asyncify_pp(MyClass)


.. tip::
    Please refer samples.py under tests for some more examples.
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


*   Note that asyncify_pp cannot be used with classes unlike asyncify. This is due to constraints with how `pickling works <https://stackoverflow.com/a/52186874>`_ .

.. note:: 
   Please refer samples.py under tests for some more examples.


Advanced usage
^^^^^^^^^^^^^^^
Refer :ref:`API <api:API>` page for more advanced usage.

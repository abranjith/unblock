======
API
======

**unblock** is intended to be extensible in a way where it provides constructs to use in your own program to help you with async programming.

Examples
---------


*   Convert regular iterator to async iterator

.. code-block:: python

   import asyncio
   from unblock.core import AsyncIterBase
    
   class MyIterator(AsyncIterBase):
    
        def __iter__(self):
            return self

        def __next__(self):
            #your logic here

    #caller usage
    async for i in MyIterator():
        print(i)


*   Async context manager

.. code-block:: python

   import asyncio
   from unblock.core import AsyncCtxMgrBase
    
   class MyCtxManager(AsyncCtxMgrBase):
    
        def close(self):
            #cleanup will be called by ctx manager

    #caller usage
    async with obj in MyCtxManager():
        #do something


*   Convert regular iterator to async iterator along with async context manager

.. code-block:: python

   import asyncio
   from unblock.core import AsyncCtxMgrIterBase
    
   class MyIterator(AsyncCtxMgrIterBase):
    
        def __iter__(self):
            return self

        def __next__(self):
            #your logic here

        def close(self):
            #cleanup will be called by ctx manager

    #caller usage
    async with obj in MyCtxManager():
        async for i in obj:
            print(i)


*   I want to specify what methods of my class needs to be asynchronous

.. code-block:: python

   import asyncio
   from unblock.core import AsyncBase
    
   #use AsyncPPBase to use Process Pool
   class MyClass(AsyncBase):
    
        def _unblock_attrs_to_asynchify(self):
            methods = [
                "sync_method1",
                "sync_method2",
                ...
            ]
            return methods

    #caller usage
    async with obj in MyCtxManager():
        #do something
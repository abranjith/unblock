======
API
======

**unblock** is intended to be extensible in a way where it provides constructs to use in your own program to help you with async programming.

Examples
---------


Asyncify methods of existing class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have an existing class where you want to convert existing methods to asynchronous without modifying the original class, below is a way to do it. Create a wrapper class and provide methods to asyncify in the _unblock_attrs_to_asynchify override

.. code-block:: python

   import asyncio
   from unblock import AsyncBase
    
   class MyClass:

        def sync_method1(self):
            #do something

        def sync_method2(self, arg1, kwarg1 = "val1"):
            #do something

   #use AsyncPPBase to use Process Pool
    class MyClassAsync(AsyncBase):

        def __init__(self):
            super().__init__(MyClass())

        def _unblock_attrs_to_asynchify(self):
            methods = [
                "sync_method1",
                "sync_method2",
                ...
            ]
            return methods

    #caller usage
    obj = MyClassAsync():
    await obj.sync_method1()
    await obj.sync_method2(100)


*   Convert regular iterator to async iterator

.. code-block:: python

   import asyncio
   from unblock import AsyncIterBase
    
   class MyIteratorAsync(AsyncIterBase):

        def __init__(self):
            super().__init__(MyClass())
    
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
   from unblock import AsyncCtxMgrBase
    
   class MyCtxManagerAsync(AsyncCtxMgrBase):

        def __init__(self):
            super().__init__(MyClass())
    
        def close(self):
            #cleanup will be called by ctx manager
            #set class var call_close_on_exit to False to not call close method as part of cleanup

    #caller usage
    async with obj in MyCtxManager():
        #do something


*   Convert regular iterator to async iterator along with async context manager

.. code-block:: python

   import asyncio
   from unblock import AsyncCtxMgrIterBase
    
   class MyIterator(AsyncCtxMgrIterBase):
    
        def __iter__(self):
            return self

        def __next__(self):
            #your logic here

        def close(self):
            #cleanup will be called by ctx manager
            #set class var call_close_on_exit to False to not call close method as part of cleanup

    #caller usage
    async with obj in MyCtxManager():
        async for i in obj:
            print(i)

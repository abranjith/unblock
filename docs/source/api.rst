======
API
======

**unblock** is intended to be extensible in a way where it provides constructs to use in your own program to help you with async programming.

Examples
---------


Asyncify methods of existing class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you have an existing class where you want to convert existing methods to asynchronous without modifying the original class, below is a way to do it. Create a wrapper class that has access to the original instance and also provide methods to asyncify in the _unblock_attrs_to_asynchify override method.

.. code-block:: python

   import asyncio
   from unblock import AsyncBase
    
   class MyClass:

        def sync_method1(self):
            #do something

        def sync_method2(self, arg1, kwarg1 = "val1"):
            #do something

   #use AsyncPPBase to use Process Pool executor
    class MyClassAsync(AsyncBase):

        #this is important that wrapper class instantiates original class and provides it to the base class
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


Asyncify Iterator
^^^^^^^^^^^^^^^^^^
Wrapper class can be created to use existing synchronous iterator as asynchronous without modifying existing iterator. Note that AsyncIterBase base class used here inherits AsyncBase and as a result if there are any methods that needs to be converted to asynchronous that can be done as well

.. code-block:: python

   import asyncio
   from unblock import AsyncIterBase

   class MyIterator:

        def __iter__(self):
            #return iterator

        def __next__(self):
            #return next item
    
    #use AsyncPPIterBase to use Process Pool executor
    class MyIteratorAsync(AsyncIterBase):

        #this is important that wrapper class instantiates original class and provides it to the base class
        def __init__(self):
            super().__init__(MyIterator())

        def _unblock_attrs_to_asynchify(self):
            methods = [
                #any methods that needs to be converted to async
            ]
            return methods
    

    #caller usage
    async for i in MyIteratorAsync():
        print(i)


Asyncify Context Manager
^^^^^^^^^^^^^^^^^^^^^^^^^
Wrapper class can be created to use existing synchronous context manager as asynchronous without modifying existing class. Note that AsyncCtxMgrBase base class used here inherits AsyncBase and as a result if there are any methods that needs to be converted to asynchronous that can be done as well.

.. code-block:: python

   import asyncio
   from unblock import AsyncCtxMgrBase

   class MyCtxMgr:

        def __enter__(self):
            #return context manager

        def __exit__(self, exc_type, exc_value, traceback):
            #responsible for cleanup
    
   class MyCtxMgrAsync(AsyncCtxMgrBase):

        def __init__(self):
            super().__init__(MyCtxMgr())

        #note that this is called automatically. If you don't want it called set call_close_on_exit field on the class to False
        async def aclose(self):
            #any asynch cleanup
    

    #caller usage
    async with obj in MyCtxMgrAsync():
        #do something


Asyncify Context Manager + Iterator
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This essentially combines functionality of Asyncify Iterator and Asyncify Context Manager

.. code-block:: python

   import asyncio
   from unblock import AsyncCtxMgrIterBase
    
   class MyIteratorCtxMgr:

        def __iter__(self):
            #return iterator

        def __next__(self):
            #return next item

        #note that this class isn't really a context manager, but it still can be used as one as shown in MyCtxMgrAsync
        def close(self):
            #cleanup will be called by async ctx manager by default
            #set class field call_close_on_exit to False to not call close method as part of cleanup

    class MyIteratorCtxMgrAsync(AsyncCtxMgrIterBase):

        def __init__(self):
            super().__init__(MyIteratorCtxMgr())


    #caller usage
    async with obj in MyIteratorCtxMgrAsync():
        async for i in obj:
            print(i)

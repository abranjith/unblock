======
API
======

**unblock** is intended to be extensible in a way where it provides constructs to use in your own program to help you with async programming.

A few important notes,

*    unblock essentially uses threads or processes to execute your callables asynchronously. One differentiator in the API is if the API supports process it has PP in the name.
     For e.g.,
     asyncify, AsyncBase, AsyncCtxMgrIterBase all use threads whereas their counterparts asyncify_pp, AsyncPPBase, AsyncPPCtxMgrIterBase all use processes.

*    Python has 3 main types of `awaitables <https://docs.python.org/3/library/asyncio-task.html#awaitables>`_ : coroutines, Tasks, and Futures. `Coroutines <https://docs.python.org/3/library/asyncio-task.html#coroutines>`_ are probably the most common ones (these are the ones declared with async/await syntax) and note that simply calling a coroutine will not schedule it to be executed.
     unblock uses `Futures <https://docs.python.org/3/library/asyncio-future.html#future-object>`_ by way of running callables in an executor (thread or process pool executor) and unlike coroutines, futures are started as soon as they are called. 
     Refer `this <https://blog.miguelgrinberg.com/post/using-javascript-style-async-promises-in-python>`_ article for some more details around this topic (mainly the 'How Async Works in Python' section).


Examples
---------

Asyncify methods of existing class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you have an existing class where you want to convert existing methods to asynchronous without modifying the original class, below is a way to do it. Create a wrapper class that has access to the original instance and also provide methods to asyncify in the _unblock_methods_to_asynchify override method.

.. code-block:: python

   from unblock import AsyncBase
    
   class MyClass:

        def sync_method1(self):
            #do something

        def sync_method2(self, arg1, kwarg1 = "val1"):
            #do something

   #use AsyncPPBase to use Process Pool executor
    class MyClassAsync(MyClass, AsyncBase):

        @staticmethod
        def _unblock_methods_to_asynchify():
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

   from unblock import AsyncIterBase

   class MyIterator:

        def __iter__(self):
            #return iterator

        def __next__(self):
            #return next item
    
    #use AsyncPPIterBase to use Process Pool executor
    class MyIteratorAsync(MyIterator, AsyncIterBase):

        @staticmethod
        def _unblock_methods_to_asynchify():
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

   from unblock import AsyncCtxMgrBase

   class MyCtxMgr:

        def __enter__(self):
            #return context manager

        def __exit__(self, exc_type, exc_value, traceback):
            #responsible for cleanup

    #use AsyncPPCtxMgrBase to use Process Pool executor 
   class MyCtxMgrAsync(MyCtxMgr, AsyncCtxMgrBase):

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
    
    #use AsyncPPCtxMgrIterBase to use Process Pool executor 
    class MyIteratorCtxMgrAsync(AsyncCtxMgrIterBase):
        pass

    #caller usage
    async with obj in MyIteratorCtxMgrAsync():
        async for i in obj:
            print(i)

.. caution:: 
   A word of caution about using process pool constructs (such as AsyncPPBase). Make sure these base classes are used in main process and not in spawned processes which can have undesirable results
   

Change defaults
^^^^^^^^^^^^^^^
unblock by default uses asyncio for event loop. But that can be changed to event loop of your choice as shown in the below example. 
Similarly default ThreadPoolExecutor and ProcessPoolExecutors can be changed as well.


.. code-block:: python

   from unblock import set_event_loop, set_threadpool_executor, set_processpool_executor
    
    #set a different event loop
    set_event_loop(event_loop)

    #set a different ThreadPoolExecutor (has to implement concurrent.futures.ThreadPoolExecutor)
    set_threadpool_executor(custom_threadpool_executor)

    #set a different ProcessPoolExecutor (has to implement concurrent.futures.ProcessPoolExecutor)
    set_processpool_executor(custom_processpool_executor)

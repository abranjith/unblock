# unblock

`unblock` provides utilities to seamlessly convert synchronous functions, methods, and classes into asynchronous counterparts, allowing them to be used efficiently within an asyncio event loop. It primarily uses thread pools (or process pools for specific functions) to run synchronous code without blocking the event loop.

For full documentation, refer to the [official documentation](https://unblock.readthedocs.io/en/latest/).

## Quick Example

Here's a basic demonstration of how to make a synchronous function asynchronous:

```python
import asyncio
import time
from unblock import asyncify

@asyncify
def my_sync_func(duration):
    print(f"Starting synchronous task for {duration} second(s)...")
    time.sleep(duration) # Simulate a blocking operation
    print("Synchronous task finished.")
    return f"Slept for {duration} second(s)"

async def main():
    print("Running asyncified function...")
    result = await my_sync_func(2) # Call the asyncified function
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## More Examples

Below are examples showcasing some of the more advanced features of `unblock`.

### Using `async_property`

The `@async_property` decorator allows you to define properties that are accessed asynchronously. This is useful when the getter for a property performs blocking I/O or a CPU-intensive operation.

```python
import asyncio
import time
from unblock import async_property, asyncify # asyncify might be needed if not using AsyncBase

class DataFetcher:
    def __init__(self, data_id):
        self._data_id = data_id
        self._data = None

    @async_property
    def data(self):
        # This method is synchronous but will be run in a thread pool
        # when accessed via the async_property.
        if self._data is None:
            print(f"Fetching data for ID: {self._data_id}...")
            time.sleep(1) # Simulate blocking I/O
            self._data = f"Some data for {self._data_id}"
            print("Data fetched.")
        return self._data

async def main():
    fetcher = DataFetcher("item123")
    
    print("Accessing data property for the first time (will block to fetch)...")
    data1 = await fetcher.data # Accessing the property like an awaitable
    print(f"Retrieved data: {data1}")

    print("\nAccessing data property again (should use cached data if property logic supports it)...")
    # Note: async_property itself doesn't cache. For caching, use @async_cached_property
    # This example's DataFetcher class implements its own simple caching via self._data
    data2 = await fetcher.data 
    print(f"Retrieved data: {data2}")

if __name__ == "__main__":
    asyncio.run(main())
```
In this example, accessing `fetcher.data` returns an awaitable. The first time it's awaited, the synchronous `data` method runs, simulating a delay.

### Using `AsyncCtxMgrBase` for Asynchronous Context Managers

If you have a class that implements the synchronous context manager protocol (`__enter__` and `__exit__`), you can make it an asynchronous context manager by inheriting from `AsyncCtxMgrBase`. This allows you to use your synchronous context manager with `async with`.

```python
import asyncio
import time
from unblock import AsyncCtxMgrBase

class SyncResourceManager(AsyncCtxMgrBase):
    def __init__(self, name):
        self.name = name
        print(f"Resource '{self.name}': Initialized (synchronous)")

    def __enter__(self):
        # Synchronous setup logic
        print(f"Resource '{self.name}': Entering context (synchronous __enter__ called)")
        time.sleep(0.5) # Simulate some setup work
        print(f"Resource '{self.name}': Context entered")
        return self # The object returned by __enter__

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Synchronous cleanup logic
        print(f"Resource '{self.name}': Exiting context (synchronous __exit__ called)")
        time.sleep(0.2) # Simulate some cleanup work
        if exc_type:
            print(f"Resource '{self.name}': Exception occurred - {exc_type.__name__}")
        print(f"Resource '{self.name}': Context exited")
        # Return False to propagate exceptions, True to suppress (standard __exit__ behavior)
        return False

    def do_something(self):
        print(f"Resource '{self.name}': Doing something with the resource.")

async def main():
    print("Starting async context manager operations...")
    async with SyncResourceManager("MyResource") as resource:
        print(f"Inside async with block for '{resource.name}'.")
        resource.do_something()
        print("Work done, preparing to exit async with block.")
    
    print("\nAsync context manager operations finished.")

if __name__ == "__main__":
    asyncio.run(main())

```
`AsyncCtxMgrBase` ensures that the synchronous `__enter__` and `__exit__` methods are properly managed when used in an `async with` statement. If your context manager has other methods (like a `close()` method that isn't `__exit__`) that are blocking and need to be called asynchronously, you would typically list them in `_unblock_methods_to_asynchify()` if you were using `AsyncBase` more broadly. However, `AsyncCtxMgrBase` specifically handles `__exit__` (and by extension, `close()` if `call_close_on_exit` is true and `__exit__` is not defined via `_stack`) within its asynchronous exit logic.

## Release Notes:

**0.0.1**
---------

Features,

*   Convert your synchronous functions, methods etc. to asynchronous with easy to use constructs
*   Asynchronous tasks are started in the background without the need of await keyword. Note that await is still needed to fetch results
*   By default uses even loop provided by asyncio. But supports other event loops as well
*   Support for ThreadPool or ProcessPool executors
*   Comes with APIs to build your own asynchronous context manager, asynchronous iterators etc.
*   Supports python 3.7 and above
```

# unblock

For documentation, refer [here](https://unblock.readthedocs.io/en/latest/)

Here is a quick example,

```python
import asyncio
   from unblock import asyncify
    
   @asyncify
   def my_sync_func():
      #do something
   
   if __name__ == "__main__":
      asyncio.run(my_sync_func())
```

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

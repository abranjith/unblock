===============
**Features**
===============

*	**Asynchronous Conversion Made Easy**
    *	With unblock, you can effortlessly convert your synchronous functions and methods to asynchronous ones.
    *	Asynchronous tasks start running in the background without requiring the await keyword. This is a key difference when compared to how asynchronous calls work by default in python where the execution doesn't start unless you use await keyword (refer the highlighted section in this article to learn more about this).  However, keep in mind that you'll still need to use await to fetch results, catch & handle exceptions as necessary.

*	**Flexible Event Loop Support**
    *	By default, unblock uses the event loop provided by asyncio. But we understand that different projects might have specific requirements. That's why we've designed unblock to be compatible with other event loops as well. Whether you're using uvloop, trio, or any other, we've got you covered !

*	**ThreadPool and ProcessPool Executors**
    *	unblock supports both ThreadPool and ProcessPool executors (see examples to see ), allowing you to harness the full power of these executors and comes with default executors out of the box
    *	you can also provide your own ThreadPool and ProcessPool executors as long as they are valid (implement concurrent.futures.ThreadPoolExecutor or concurrent.futures.ProcessPoolExecutor)

*	**Build Your Own Asynchronous Context Managers and Iterators**
    *	With unblock, you can create custom asynchronous context managers and iterators tailored to your project's needs.

*	**Python 3.7 and Beyond**
    *	unblock plays nicely with Python 3.7 and all subsequent versions.

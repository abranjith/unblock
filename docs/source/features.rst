==========
Features
==========

*	**Asynchronous Conversion Made Easy**
    *	With unblock, you can effortlessly convert your synchronous functions and methods to asynchronous ones.
    *	Asynchronous tasks start running in the background without requiring the await keyword. This is a key difference when compared to how asynchronous calls work by default in python where the execution doesn't start unless you use await keyword (refer the highlighted section in this article to learn more about this).  However, keep in mind that you'll still need to use await to fetch results, catch & handle exceptions as necessary.

*	**Flexible Event Loop Support**
    *	By default, unblock uses the event loop provided by asyncio. But unblock has been designed to be compatible with any other event loops as well. So if your project is using event loops such as uvloop, trio, or any other, we've got you covered !

*	**Threads vs Processes**
    *	unblock uses either threads or processes to execute your callables asynchronously. It uses default executors from concurrent.futures module which should work for most of the cases.
    *	You can also provide your own executors as long as they are valid implementations

*	**Build Your Own Asynchronous Context Managers and Iterators**
    *	With unblock, you can create custom asynchronous context managers and iterators tailored to your project's needs.

*	**Python 3.7 and Beyond**
    *	unblock plays nicely with Python 3.7 and all subsequent versions.

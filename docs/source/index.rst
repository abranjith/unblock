.. unblock documentation master file, created by
   sphinx-quickstart on Fri Jan 15 01:01:17 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to unblock's documentation!
===================================


**About the project**
*********************
**unblock** provides small utilities that convert synchronous functions, methods,
and classes into asynchronous ones for use inside an asyncio event loop. It
offloads blocking work to a thread or process pool so it does not block the loop.
Here is a basic example,

.. code-block:: python

   import asyncio
   from unblock import asyncify

   @asyncify
   def my_sync_func():
       ...  # do something blocking

   if __name__ == "__main__":
       asyncio.run(my_sync_func())


**Get It Now**
***************
The distribution name is ``get-unblock``; the import name is ``unblock``.

.. code-block:: text

   pip install get-unblock

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   features
   basicusage
   api
   caveats
   migration
   apireference



Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

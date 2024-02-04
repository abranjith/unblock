.. unblock documentation master file, created by
   sphinx-quickstart on Fri Jan 15 01:01:17 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to unblock's documentation!
===================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

**About the project**
*********************
**unblock** comes with utilities that can be used to convert synchronous functions to asynch for use in event loop across your maps. Here is a basic example,

.. code-block:: python

   import asyncio
   from unblock.core import asyncify
    
   @asyncify
   def my_sync_func():
      #do something
   
   if __name__ == "__main__":
      asyncio.run(my_sync_func())




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

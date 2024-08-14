.. unblock documentation master file, created by
   sphinx-quickstart on Fri Jan 15 01:01:17 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to unblock's documentation!
===================================


**About the project**
*********************
**unblock** comes with utilities that can be used to convert synchronous functions to asynch for use in event loop. Here is a basic example,

.. code-block:: python

   import asyncio
   from unblock import asyncify
    
   @asyncify
   def my_sync_func():
      #do something
   
   if __name__ == "__main__":
      asyncio.run(my_sync_func())


**Get It Now**
***************
.. code-block:: python

   pip install unblockio

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   features
   basicusage
   api



Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

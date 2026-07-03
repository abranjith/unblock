=========
Migration
=========

Version 0.1.0+ is a ground-up refactor with a smaller, unified API. There is no
backward compatibility with 0.0.1. This page maps the old names to the new ones.

Functions and decorators
------------------------

.. list-table::
   :header-rows: 1

   * - Old
     - New
   * - ``asyncify_pp(func)``
     - ``asyncify(func, executor="process")`` -- and it now works as a decorator
   * - ``asyncify_func`` / ``asyncify_func_pp``
     - ``asyncify`` (with ``executor=`` as needed)
   * - ``asyncify_cls``
     - ``asyncify`` on a class
   * - ``UnblockException``
     - ``UnblockError``

Classes
-------

The eight base classes are replaced by four executor-configurable mixins, and the
string-list override method is gone.

.. list-table::
   :header-rows: 1

   * - Old
     - New
   * - ``AsyncBase`` / ``AsyncPPBase`` + ``_unblock_methods_to_asynchify``
     - ``@asyncify(include=[...] / exclude=[...])`` on the class, or
       ``class W(Base, AsyncMixin, executor=...)``
   * - ``AsyncIterBase`` / ``AsyncPPIterBase``
     - ``AsyncIterMixin`` (or protocol auto-detection via ``@asyncify``)
   * - ``AsyncCtxMgrBase`` / ``AsyncPPCtxMgrBase``
     - ``AsyncContextMixin``
   * - ``AsyncCtxMgrIterBase`` / ``AsyncPPCtxMgrIterBase``
     - ``AsyncContextIterMixin``

Before:

.. code-block:: python

   from unblock import AsyncBase

   class MyClassAsync(MyClass, AsyncBase):
       @staticmethod
       def _unblock_methods_to_asynchify():
           return ["sync_method1", "sync_method2"]

After:

.. code-block:: python

   from unblock import AsyncMixin

   class MyClassAsync(MyClass, AsyncMixin):
       pass  # all public methods; use include=/exclude= to narrow

Configuration
-------------

.. list-table::
   :header-rows: 1

   * - Old
     - New
   * - ``set_event_loop(loop)``
     - removed -- the running loop is always used
   * - ``set_threadpool_executor(executor)``
     - ``set_thread_pool(executor)``
   * - ``set_processpool_executor(executor)``
     - ``set_process_pool(executor)``
   * - ``Registry`` (public)
     - removed -- internal; use the configuration helpers and ``shutdown()``

The new ``shutdown()`` helper releases the default pools (also registered via
``atexit``).

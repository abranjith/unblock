=============
API reference
=============

Converter
---------

.. autofunction:: unblock.asyncify

Properties
----------

.. autoclass:: unblock.async_property
   :members:

.. autoclass:: unblock.async_cached_property
   :members:

Mixins
------

.. autoclass:: unblock.AsyncMixin
.. autoclass:: unblock.AsyncIterMixin
.. autoclass:: unblock.AsyncContextMixin
.. autoclass:: unblock.AsyncContextIterMixin

Configuration and lifecycle
---------------------------

.. autofunction:: unblock.set_thread_pool
.. autofunction:: unblock.set_process_pool
.. autofunction:: unblock.shutdown

Errors
------

.. autoexception:: unblock.UnblockError

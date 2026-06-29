"""unblock: turn synchronous callables into asynchronous ones.

``unblock`` offloads blocking work to a thread or process pool via
:meth:`asyncio.loop.run_in_executor`, so synchronous code can be used from an
event loop without rewriting it. When a loop is already running, an asyncified
call starts immediately in the background and returns an awaitable; you still
``await`` to collect the result.
"""

from __future__ import annotations

import logging

from .classes import (
    AsyncContextIterMixin,
    AsyncContextMixin,
    AsyncIterMixin,
    AsyncMixin,
)
from .config import set_process_pool, set_thread_pool, shutdown
from .errors import UnblockError
from .functions import asyncify
from .properties import async_cached_property, async_property

# A library should not configure logging for the application. Attach a
# NullHandler so unblock's own DEBUG diagnostics are silent unless the
# application opts in.
logging.getLogger("unblock").addHandler(logging.NullHandler())

__author__ = "ranjith"
__version__ = "0.1.0"

__all__ = [
    "asyncify",
    "async_property",
    "async_cached_property",
    "AsyncMixin",
    "AsyncIterMixin",
    "AsyncContextMixin",
    "AsyncContextIterMixin",
    "UnblockError",
    "set_thread_pool",
    "set_process_pool",
    "shutdown",
]

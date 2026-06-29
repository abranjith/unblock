"""Internal executor resolver and lifecycle management.

This module owns the process-global thread and process pools used to run
synchronous work off the event loop. It is intentionally private: the public
configuration surface is re-exported from :mod:`unblock.config`.

Design notes:

* Pools are created lazily and only once, guarded by a lock so concurrent
  first-use from multiple threads cannot create duplicates.
* Sensible bounded defaults are used (the standard-library defaults are already
  bounded; we keep them explicit and name threads for easier debugging).
* :func:`shutdown` releases the pools and is registered with :mod:`atexit` so a
  process does not hang or leak workers on exit.
"""

from __future__ import annotations

import atexit
import logging
import multiprocessing
import os
import threading
from concurrent.futures import Executor, ProcessPoolExecutor, ThreadPoolExecutor
from typing import Literal

from .errors import UnblockError

__all__ = [
    "ExecutorKind",
    "resolve_executor",
    "get_thread_pool",
    "get_process_pool",
    "set_thread_pool",
    "set_process_pool",
    "shutdown",
    "in_worker_process",
]

_logger = logging.getLogger("unblock")

ExecutorKind = Executor | Literal["thread", "process"]

_THREAD_NAME_PREFIX = "unblock.asyncio"

# Process-global state, guarded by ``_lock``.
_lock = threading.Lock()
_thread_pool: ThreadPoolExecutor | None = None
_process_pool: ProcessPoolExecutor | None = None
_is_shutdown = False


def _default_thread_workers() -> int:
    return min(32, (os.cpu_count() or 1) + 4)


def _default_process_workers() -> int:
    return os.cpu_count() or 1


def get_thread_pool() -> ThreadPoolExecutor:
    """Return the shared thread pool, creating it on first use."""
    global _thread_pool
    pool = _thread_pool
    if pool is not None:
        return pool
    with _lock:
        if _is_shutdown:
            raise UnblockError(
                "unblock has been shut down; configure a new executor with "
                "set_thread_pool() before asyncifying more work"
            )
        if _thread_pool is None:
            _thread_pool = ThreadPoolExecutor(
                max_workers=_default_thread_workers(),
                thread_name_prefix=_THREAD_NAME_PREFIX,
            )
            _logger.debug(
                "created default ThreadPoolExecutor (max_workers=%d)",
                _default_thread_workers(),
            )
        return _thread_pool


def get_process_pool() -> ProcessPoolExecutor:
    """Return the shared process pool, creating it on first use."""
    global _process_pool
    pool = _process_pool
    if pool is not None:
        return pool
    with _lock:
        if _is_shutdown:
            raise UnblockError(
                "unblock has been shut down; configure a new executor with "
                "set_process_pool() before asyncifying more work"
            )
        if _process_pool is None:
            _process_pool = ProcessPoolExecutor(max_workers=_default_process_workers())
            _logger.debug(
                "created default ProcessPoolExecutor (max_workers=%d)",
                _default_process_workers(),
            )
        return _process_pool


def resolve_executor(executor: ExecutorKind) -> Executor:
    """Map ``executor`` to a concrete :class:`concurrent.futures.Executor`.

    Accepts the literal strings ``"thread"`` or ``"process"``, or an existing
    :class:`~concurrent.futures.Executor` instance (returned unchanged). Any
    other value raises :class:`~unblock.UnblockError`.
    """
    if isinstance(executor, Executor):
        return executor
    if executor == "thread":
        return get_thread_pool()
    if executor == "process":
        return get_process_pool()
    raise UnblockError(
        f"invalid executor {executor!r}; expected 'thread', 'process', or a "
        f"concurrent.futures.Executor instance"
    )


def is_process_executor(executor: ExecutorKind) -> bool:
    """Return ``True`` if ``executor`` selects a process pool."""
    if executor == "process":
        return True
    return isinstance(executor, ProcessPoolExecutor)


def set_thread_pool(executor: ThreadPoolExecutor) -> None:
    """Replace the shared thread pool with ``executor``.

    Raises:
        UnblockError: if ``executor`` is not a
            :class:`concurrent.futures.ThreadPoolExecutor`.
    """
    if not isinstance(executor, ThreadPoolExecutor):
        raise UnblockError(
            f"set_thread_pool() requires a ThreadPoolExecutor, got "
            f"{type(executor).__name__}"
        )
    global _thread_pool, _is_shutdown
    with _lock:
        _thread_pool = executor
        _is_shutdown = False


def set_process_pool(executor: ProcessPoolExecutor) -> None:
    """Replace the shared process pool with ``executor``.

    Raises:
        UnblockError: if ``executor`` is not a
            :class:`concurrent.futures.ProcessPoolExecutor`.
    """
    if not isinstance(executor, ProcessPoolExecutor):
        raise UnblockError(
            f"set_process_pool() requires a ProcessPoolExecutor, got "
            f"{type(executor).__name__}"
        )
    global _process_pool, _is_shutdown
    with _lock:
        _process_pool = executor
        _is_shutdown = False


def shutdown(wait: bool = True) -> None:
    """Shut down any pools ``unblock`` created and mark the library shut down.

    Idempotent and safe to call when nothing was ever created. After shutdown,
    requesting a default pool raises :class:`~unblock.UnblockError` until a new
    pool is supplied via :func:`set_thread_pool` / :func:`set_process_pool`.

    This is registered with :mod:`atexit`, so default pools are cleaned up on
    interpreter exit without any action from the caller.
    """
    global _thread_pool, _process_pool, _is_shutdown
    with _lock:
        for pool in (_thread_pool, _process_pool):
            if pool is not None:
                pool.shutdown(wait=wait)
        if _thread_pool is not None or _process_pool is not None:
            _logger.debug("shut down unblock executors")
        _thread_pool = None
        _process_pool = None
        _is_shutdown = True


def in_worker_process() -> bool:
    """Return ``True`` when running inside a spawned worker process.

    Uses :func:`multiprocessing.parent_process`, which returns ``None`` only in
    the main process. This is a robust replacement for comparing the process
    name against the string ``"MainProcess"``.
    """
    return multiprocessing.parent_process() is not None


atexit.register(shutdown)

"""The single scheduling funnel used by every public construct.

All asyncification paths (functions, methods, classes, properties, mixins) route
through :func:`schedule`, so the behaviour that matters -- which loop the work
binds to, and whether a started future or a coroutine is returned -- is defined
in exactly one place.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from ._executors import ExecutorKind, resolve_executor

__all__ = ["schedule", "is_loop_running"]

_T = TypeVar("_T")


def is_loop_running() -> bool:
    """Return ``True`` if called from within a running event loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return False
    return True


def _run_now(fn: Callable[[], _T], executor: ExecutorKind) -> asyncio.Future[_T]:
    """Submit ``fn`` to ``executor`` on the *running* loop and return its future.

    Binding to ``asyncio.get_running_loop()`` (rather than a separately stored
    loop) guarantees the returned future is awaited on the same loop it is
    attached to, which is what prevents the "future attached to a different
    loop" error.
    """
    loop = asyncio.get_running_loop()
    resolved = resolve_executor(executor)
    return loop.run_in_executor(resolved, fn)


def schedule(fn: Callable[[], _T], executor: ExecutorKind) -> Awaitable[_T]:
    """Run ``fn`` off the event loop and return an awaitable for its result.

    ``fn`` must be a zero-argument callable; callers pre-bind any arguments
    (typically with :func:`functools.partial`).

    Return-type duality:

    * **A loop is already running** -- the work is submitted immediately and a
      started :class:`asyncio.Future` is returned. The work runs in the
      background; ``await`` only collects the result.
    * **No loop is running** -- a coroutine is returned that submits the work
      when it is awaited (at which point a loop exists).

    Either way the work binds to the loop that is actually running at execution
    time. Exceptions raised by ``fn`` propagate to the awaiter unchanged.

    Note:
        Cancelling the returned awaitable follows
        :meth:`asyncio.loop.run_in_executor` semantics: work that has already
        started in a thread or process cannot be forcibly stopped. Cancellation
        only prevents work that has not yet begun.
    """
    if is_loop_running():
        return _run_now(fn, executor)

    async def _deferred() -> _T:
        return await _run_now(fn, executor)

    return _deferred()

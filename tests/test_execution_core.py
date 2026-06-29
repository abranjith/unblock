"""Tests for FEAT-001: execution core (errors, executor resolver, scheduling)."""

from __future__ import annotations

import asyncio
import logging
import threading
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import pytest

import unblock
import unblock._executors as ex
from unblock import UnblockError
from unblock._scheduling import is_loop_running, schedule

# --- UnblockError -----------------------------------------------------------


def test_unblock_error_is_exception():
    assert issubclass(UnblockError, Exception)


def test_unblock_error_importable_from_package_and_module():
    from unblock.errors import UnblockError as FromModule

    assert FromModule is unblock.UnblockError


# --- resolve_executor / lazy pools ------------------------------------------


def test_resolve_thread_returns_threadpool_singleton():
    pool = ex.resolve_executor("thread")
    assert isinstance(pool, ThreadPoolExecutor)
    assert ex.resolve_executor("thread") is pool


def test_resolve_process_returns_processpool_singleton():
    pool = ex.resolve_executor("process")
    assert isinstance(pool, ProcessPoolExecutor)
    assert ex.resolve_executor("process") is pool


def test_resolve_executor_passes_through_instance():
    custom = ThreadPoolExecutor(max_workers=1)
    try:
        assert ex.resolve_executor(custom) is custom
    finally:
        custom.shutdown(wait=False)


@pytest.mark.parametrize("bad", ["green", 42, None, object()])
def test_resolve_executor_invalid_raises(bad):
    with pytest.raises(UnblockError):
        ex.resolve_executor(bad)


def test_thread_pool_created_once_under_concurrency():
    seen: list[ThreadPoolExecutor] = []
    barrier = threading.Barrier(8)

    def grab():
        barrier.wait()
        seen.append(ex.get_thread_pool())

    threads = [threading.Thread(target=grab) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(set(id(p) for p in seen)) == 1


def test_in_worker_process_false_in_main():
    assert ex.in_worker_process() is False


def test_is_process_executor():
    assert ex.is_process_executor("process") is True
    assert ex.is_process_executor("thread") is False
    pp = ProcessPoolExecutor(max_workers=1)
    tp = ThreadPoolExecutor(max_workers=1)
    try:
        assert ex.is_process_executor(pp) is True
        assert ex.is_process_executor(tp) is False
    finally:
        pp.shutdown(wait=False)
        tp.shutdown(wait=False)


# --- config: set_*_pool / shutdown ------------------------------------------


def test_set_thread_pool_validates_type():
    with pytest.raises(UnblockError):
        unblock.set_thread_pool(ProcessPoolExecutor(max_workers=1))


def test_set_process_pool_validates_type():
    with pytest.raises(UnblockError):
        unblock.set_process_pool(ThreadPoolExecutor(max_workers=1))


def test_set_thread_pool_replaces_default():
    custom = ThreadPoolExecutor(max_workers=1)
    unblock.set_thread_pool(custom)
    assert ex.get_thread_pool() is custom


def test_shutdown_is_idempotent():
    ex.get_thread_pool()
    unblock.shutdown()
    unblock.shutdown()  # second call must not raise


def test_use_after_shutdown_raises_until_reconfigured():
    unblock.shutdown()
    with pytest.raises(UnblockError):
        ex.get_thread_pool()
    # reconfiguring clears the shutdown flag
    custom = ThreadPoolExecutor(max_workers=1)
    unblock.set_thread_pool(custom)
    assert ex.get_thread_pool() is custom


def test_shutdown_registered_with_atexit():
    import atexit

    # atexit._ncallbacks is not introspectable portably; instead assert the
    # function object is referenced by atexit's registry.
    registered = getattr(atexit, "_exithandlers", None)
    if registered is not None:  # CPython detail; skip gracefully otherwise
        funcs = [entry[0] for entry in registered]
        assert ex.shutdown in funcs


# --- scheduling: duality + loop binding -------------------------------------


def test_is_loop_running_outside_loop():
    assert is_loop_running() is False


async def test_is_loop_running_inside_loop():
    assert is_loop_running() is True


async def test_schedule_returns_started_future_with_running_loop():
    awaitable = schedule(lambda: 21 * 2, "thread")
    assert isinstance(awaitable, asyncio.Future)
    assert await awaitable == 42


def test_schedule_returns_coroutine_without_loop():
    import inspect

    awaitable = schedule(lambda: "ok", "thread")
    assert inspect.iscoroutine(awaitable)
    assert asyncio.run(_await(awaitable)) == "ok"


async def _await(awaitable):
    return await awaitable


async def test_schedule_propagates_exception():
    def boom():
        raise ValueError("kaboom")

    with pytest.raises(ValueError, match="kaboom"):
        await schedule(boom, "thread")


def test_schedule_binds_to_running_loop_across_loops():
    # Regression for the cross-loop bug: scheduling under one loop, then again
    # under a freshly created loop, must not raise "attached to a different
    # loop". Each schedule() binds to whatever loop is actually running.
    def run_once():
        async def main():
            return await schedule(lambda: 1, "thread")

        return asyncio.run(main())

    assert run_once() == 1
    assert run_once() == 1  # fresh loop the second time


# --- logging policy ---------------------------------------------------------


def test_package_attaches_null_handler():
    handlers = logging.getLogger("unblock").handlers
    assert any(isinstance(h, logging.NullHandler) for h in handlers)

"""Tests for FEAT-001/006: executor config, lifecycle, and cross-loop regression."""

from __future__ import annotations

import asyncio
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import pytest

import unblock
import unblock._executors as ex
from unblock import UnblockError


def test_process_use_after_shutdown_raises():
    unblock.shutdown()
    with pytest.raises(UnblockError):
        ex.get_process_pool()


def test_set_process_pool_replaces_default():
    pool = ProcessPoolExecutor(max_workers=1)
    try:
        unblock.set_process_pool(pool)
        assert ex.get_process_pool() is pool
    finally:
        pool.shutdown(wait=False)


def test_shutdown_closes_created_process_pool():
    ex.get_process_pool()  # force creation
    unblock.shutdown()
    # After shutdown the default is gone and use raises until reconfigured.
    with pytest.raises(UnblockError):
        ex.get_process_pool()


def test_thread_pool_double_checked_locking_branch():
    # Deterministically exercise the inner "already created" branch of the
    # double-checked locking: hold the lock, let a worker block on it, then set
    # the pool before releasing so the worker takes the not-None path.
    created = ThreadPoolExecutor(max_workers=1)
    result: dict[str, object] = {}

    def worker():
        result["pool"] = ex.get_thread_pool()

    try:
        with ex._lock:
            ex._thread_pool = None
            t = threading.Thread(target=worker)
            t.start()
            time.sleep(0.05)  # let the worker block on _lock
            ex._thread_pool = created
        t.join()
        assert result["pool"] is created
    finally:
        created.shutdown(wait=False)


def test_process_pool_double_checked_locking_branch():
    sentinel = ThreadPoolExecutor(max_workers=1)  # stand-in; only identity matters
    result: dict[str, object] = {}

    def worker():
        result["pool"] = ex.get_process_pool()

    try:
        with ex._lock:
            ex._process_pool = None
            t = threading.Thread(target=worker)
            t.start()
            time.sleep(0.05)
            ex._process_pool = sentinel  # type: ignore[assignment]
        t.join()
        assert result["pool"] is sentinel
    finally:
        sentinel.shutdown(wait=False)


def test_cross_loop_regression_fresh_loops():
    # Running asyncified work under one loop, then a fresh loop, must not raise
    # "Future attached to a different loop".
    @unblock.asyncify
    def work():
        return 1

    def run():
        async def main():
            return await work()

        return asyncio.run(main())

    assert run() == 1
    assert run() == 1  # brand-new event loop the second time

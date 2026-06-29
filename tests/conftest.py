"""Shared pytest fixtures for the unblock test suite."""

from __future__ import annotations

import pytest

import unblock._executors as _executors


def _reset_executor_state() -> None:
    """Tear down any pools and clear the process-global executor state.

    Keeps tests isolated: a pool created (or a shutdown triggered) by one test
    must not bleed into the next.
    """
    with _executors._lock:
        for pool in (_executors._thread_pool, _executors._process_pool):
            if pool is not None:
                pool.shutdown(wait=False)
        _executors._thread_pool = None
        _executors._process_pool = None
        _executors._is_shutdown = False


@pytest.fixture(autouse=True)
def reset_executors():
    """Reset unblock's executor state before and after every test."""
    _reset_executor_state()
    yield
    _reset_executor_state()

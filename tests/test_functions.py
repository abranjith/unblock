"""Tests for FEAT-002: function & method asyncification."""

from __future__ import annotations

import asyncio
import inspect
import os
from concurrent.futures import ThreadPoolExecutor

import pytest

from unblock import UnblockError, asyncify

# --- dispatcher forms -------------------------------------------------------


async def test_bare_decorator_on_function():
    @asyncify
    def add(a, b):
        return a + b

    assert await add(2, 3) == 5


async def test_parameterized_decorator_thread():
    @asyncify(executor="thread")
    def greet(name):
        return f"hi {name}"

    assert await greet("sam") == "hi sam"


async def test_direct_call_form():
    def square(x):
        return x * x

    asquare = asyncify(square)
    assert await asquare(4) == 16


def test_misuse_raises_unblock_error():
    for bad in (42, "string", 3.14, [1, 2]):
        with pytest.raises(UnblockError):
            asyncify(bad)


async def test_coroutine_function_passthrough_identity():
    async def already():
        return 1

    assert asyncify(already) is already


def test_include_on_callable_raises():
    def fn():
        return 1

    with pytest.raises(UnblockError):
        asyncify(fn, include=["x"])


# --- wrapper behaviour ------------------------------------------------------


async def test_wrapper_preserves_metadata():
    @asyncify
    def documented(x):
        """A docstring."""
        return x

    assert documented.__name__ == "documented"
    assert documented.__doc__ == "A docstring."
    assert hasattr(documented, "__wrapped__")


async def test_works_on_instance_method():
    class C:
        def __init__(self, base):
            self.base = base

        @asyncify
        def add(self, x):
            return self.base + x

    c = C(10)
    assert await c.add(5) == 15


async def test_exception_propagates():
    @asyncify
    def boom():
        raise RuntimeError("nope")

    with pytest.raises(RuntimeError, match="nope"):
        await boom()


async def test_runs_off_the_event_loop_thread():
    main_thread = __import__("threading").get_ident()

    @asyncify
    def where():
        return __import__("threading").get_ident()

    assert await where() != main_thread


# --- duality ----------------------------------------------------------------


async def test_returns_started_future_under_loop():
    @asyncify
    def fn():
        return 7

    awaitable = fn()
    assert isinstance(awaitable, asyncio.Future)
    assert await awaitable == 7


def test_returns_coroutine_without_loop():
    @asyncify
    def fn():
        return 7

    awaitable = fn()
    assert inspect.iscoroutine(awaitable)
    assert asyncio.run(_collect(awaitable)) == 7


async def _collect(awaitable):
    return await awaitable


# --- custom executor instance -----------------------------------------------


async def test_custom_thread_executor_instance():
    pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="custom-pool")
    try:

        @asyncify(executor=pool)
        def name():
            return __import__("threading").current_thread().name

        assert (await name()).startswith("custom-pool")
    finally:
        pool.shutdown(wait=False)


# --- process pool: fail-fast at decoration time -----------------------------


def test_process_lambda_rejected_at_decoration():
    with pytest.raises(UnblockError, match="process pool"):
        asyncify(lambda x: x, executor="process")


def test_process_closure_rejected_at_decoration():
    def make():
        def inner(x):
            return x

        return inner

    with pytest.raises(UnblockError, match="process pool"):
        asyncify(make(), executor="process")


# --- process pool: trampoline (uses importable targets) ---------------------


async def test_process_decorator_returns_result():
    from tests import _picklable_targets as t

    assert await t.decorated_double(21) == 42


async def test_process_direct_call_returns_result():
    from tests import _picklable_targets as t

    ap = asyncify(t.plain_double, executor="process")
    assert await ap(5) == 10


async def test_process_runs_in_separate_process():
    from tests import _picklable_targets as t

    worker_pid = await t.returns_pid()
    assert worker_pid != os.getpid()


async def test_process_exception_propagates():
    from tests import _picklable_targets as t

    with pytest.raises(ValueError, match="worker boom"):
        await t.raises_in_worker()


def test_run_via_reference_unwraps_decorated():
    # The trampoline runs inside worker processes, so exercise it directly here.
    from tests import _picklable_targets as t
    from unblock.functions import _run_via_reference

    assert _run_via_reference(t.__name__, "decorated_double", (5,), {}) == 10


def test_run_via_reference_plain_function():
    from tests import _picklable_targets as t
    from unblock.functions import _run_via_reference

    # A plain (non-asyncified) function has no __wrapped__; resolve to itself.
    assert _run_via_reference(t.__name__, "plain_double", (6,), {}) == 12


# --- cancellation semantics (documented limitation) -------------------------


async def test_cancel_before_start_raises_cancelled():
    import threading

    started = threading.Event()
    release = threading.Event()

    @asyncify
    def slow():
        started.set()
        release.wait(timeout=5)
        return "done"

    fut = slow()
    fut.cancel()
    with pytest.raises(asyncio.CancelledError):
        await fut
    release.set()

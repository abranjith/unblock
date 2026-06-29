"""Tests for FEAT-003: class & protocol asyncification."""

from __future__ import annotations

import asyncio
import threading

import pytest

import unblock
from unblock import (
    AsyncContextIterMixin,
    AsyncContextMixin,
    AsyncIterMixin,
    AsyncMixin,
    UnblockError,
    asyncify,
)

# --- decorator: selection rules ---------------------------------------------


async def test_decorator_wraps_public_instance_methods_only():
    @asyncify
    class C:
        def __init__(self):
            self.calls = []

        def pub(self):
            return "pub"

        def _priv(self):
            return "priv"

        @staticmethod
        def stat():
            return "stat"

        @classmethod
        def cls_m(cls):
            return "cls"

        async def already(self):
            return "already"

    c = C()
    assert await c.pub() == "pub"
    assert c._priv() == "priv"  # untouched (private)
    assert C.stat() == "stat"  # untouched (staticmethod)
    assert C.cls_m() == "cls"  # untouched (classmethod)
    assert await c.already() == "already"  # already async, untouched
    assert C.__unblock_wrapped__ == frozenset({"pub"})


async def test_decorator_include():
    @asyncify(include=["a"])
    class C:
        def a(self):
            return "a"

        def b(self):
            return "b"

    c = C()
    assert await c.a() == "a"
    assert c.b() == "b"  # not wrapped
    assert C.__unblock_wrapped__ == frozenset({"a"})


async def test_decorator_exclude():
    @asyncify(exclude=["b"])
    class C:
        def a(self):
            return "a"

        def b(self):
            return "b"

    c = C()
    assert await c.a() == "a"
    assert c.b() == "b"
    assert C.__unblock_wrapped__ == frozenset({"a"})


def test_include_and_exclude_mutually_exclusive():
    with pytest.raises(UnblockError):

        @asyncify(include=["a"], exclude=["b"])
        class C:
            def a(self):
                return "a"

            def b(self):
                return "b"


def test_include_invalid_name_raises():
    with pytest.raises(UnblockError):

        @asyncify(include=["does_not_exist"])
        class C:
            def a(self):
                return "a"


def test_include_string_rejected():
    with pytest.raises(UnblockError):

        @asyncify(include="a")
        class C:
            def a(self):
                return "a"


def test_include_non_iterable_rejected():
    with pytest.raises(UnblockError):

        @asyncify(include=123)
        class C:
            def a(self):
                return "a"


async def test_build_once_identity():
    @asyncify
    class C:
        def m(self):
            return 1

    c = C()
    # Wrapper is created once at class-definition time, not per access.
    assert c.m.__func__ is C.__dict__["m"]


# --- mixin: wrapper pattern -------------------------------------------------


class Base:
    def __init__(self, base):
        self.base = base

    def compute(self, x):
        return self.base + x

    def _hidden(self):
        return "hidden"


async def test_mixin_wraps_without_modifying_base():
    class Wrapper(Base, AsyncMixin):
        pass

    w = Wrapper(10)
    assert await w.compute(5) == 15
    # Base is untouched
    assert Base(1).compute(2) == 3


async def test_mixin_executor_keyword_accepted():
    class Wrapper(Base, AsyncMixin, executor="thread"):
        pass

    w = Wrapper(1)
    assert await w.compute(1) == 2


# --- iterator protocol ------------------------------------------------------


class Counter:
    def __init__(self, n):
        self.n = n

    def __iter__(self):
        self.i = 0
        return self

    def __next__(self):
        self.i += 1
        if self.i > self.n:
            raise StopIteration
        return self.i


async def test_iter_via_decorator():
    @asyncify
    class C(Counter):
        pass

    out = [i async for i in C(3)]
    assert out == [1, 2, 3]


async def test_iter_via_mixin():
    class C(Counter, AsyncIterMixin):
        pass

    out = [i async for i in C(4)]
    assert out == [1, 2, 3, 4]


# --- context manager protocol ----------------------------------------------


class CtxRecorder:
    def __init__(self):
        self.entered_thread = None
        self.exited = False
        self.closed = False

    def __enter__(self):
        self.entered_thread = threading.get_ident()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.exited = True
        return False

    def close(self):
        self.closed = True


async def test_context_runs_enter_exit_off_loop_thread():
    @asyncify
    class C(CtxRecorder):
        pass

    main = threading.get_ident()
    async with C() as obj:
        pass
    assert obj.exited is True
    # __enter__ must have run on a worker thread, not the loop thread.
    assert obj.entered_thread is not None
    assert obj.entered_thread != main


async def test_context_calls_close_when_no_aclose():
    @asyncify
    class C(CtxRecorder):
        pass

    # CtxRecorder.__exit__ does not call close(); the consolidated rule should
    # not call close() either, because __exit__ handled cleanup.
    async with C() as obj:
        pass
    assert obj.closed is False


class CloseOnly:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


async def test_context_mixin_on_close_only_class():
    class C(CloseOnly, AsyncContextMixin):
        pass

    obj = C()
    async with obj:
        pass
    # No __exit__, so the consolidated rule calls close().
    assert obj.closed is True


class CtxWithAclose:
    def __init__(self):
        self.exited = False
        self.aclosed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.exited = True
        return False

    async def aclose(self):
        await asyncio.sleep(0)
        self.aclosed = True


async def test_context_awaits_aclose_when_present():
    @asyncify
    class C(CtxWithAclose):
        pass

    async with C() as obj:
        pass
    assert obj.exited is True
    assert obj.aclosed is True


async def test_call_close_on_exit_false_skips_aclose():
    @asyncify
    class C(CtxWithAclose):
        call_close_on_exit = False

    async with C() as obj:
        pass
    assert obj.exited is True  # __exit__ still runs
    assert obj.aclosed is False  # extra cleanup skipped


class CtxSyncAclose:
    def __init__(self):
        self.aclosed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def aclose(self):  # synchronous aclose
        self.aclosed = True


async def test_sync_aclose_is_offloaded():
    @asyncify
    class C(CtxSyncAclose):
        pass

    async with C() as obj:
        pass
    assert obj.aclosed is True


class HasOwnAsyncContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    async def __aenter__(self):
        return "custom-enter"

    async def __aexit__(self, exc_type, exc, tb):
        return False


async def test_existing_async_context_not_overwritten():
    @asyncify
    class C(HasOwnAsyncContext):
        pass

    async with C() as obj:
        assert obj == "custom-enter"  # user's __aenter__ preserved


async def test_context_mixin_with_no_cleanup_hooks():
    # AsyncContextMixin on a class with no __enter__/__exit__/close/aclose:
    # entering yields self and exiting is a no-op.
    class Bare(AsyncContextMixin):
        pass

    obj = Bare()
    async with obj as entered:
        assert entered is obj


# --- combined ctx + iter ----------------------------------------------------


class Source:
    def __init__(self, n):
        self.n = n
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def __iter__(self):
        self.i = 0
        return self

    def __next__(self):
        self.i += 1
        if self.i > self.n:
            raise StopIteration
        return self.i

    def close(self):
        self.closed = True


async def test_combined_context_iter_mixin():
    class C(Source, AsyncContextIterMixin):
        pass

    collected = []
    async with C(3) as obj:
        async for i in obj:
            collected.append(i)
    assert collected == [1, 2, 3]


# --- exports / removed legacy names -----------------------------------------


def test_mixins_importable():
    assert all(
        isinstance(m, type)
        for m in (
            AsyncMixin,
            AsyncIterMixin,
            AsyncContextMixin,
            AsyncContextIterMixin,
        )
    )


@pytest.mark.parametrize(
    "name",
    [
        "AsyncBase",
        "AsyncPPBase",
        "AsyncIterBase",
        "AsyncCtxMgrBase",
        "AsyncCtxMgrIterBase",
        "asyncify_pp",
        "set_event_loop",
        "Registry",
    ],
)
def test_legacy_names_removed(name):
    assert not hasattr(unblock, name)

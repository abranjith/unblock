"""Tests for FEAT-004: async properties."""

from __future__ import annotations

import asyncio

import pytest

from unblock import async_cached_property, async_property

# --- async_property ---------------------------------------------------------


async def test_async_property_returns_value():
    class C:
        def __init__(self, v):
            self._v = v

        @async_property
        def value(self):
            return self._v

    c = C(10)
    assert await c.value == 10


async def test_async_property_reflects_state_changes():
    class C:
        def __init__(self):
            self.v = 1

        @async_property
        def value(self):
            return self.v

    c = C()
    assert await c.value == 1
    c.v = 2
    assert await c.value == 2  # not cached


def test_async_property_class_access_returns_descriptor():
    class C:
        @async_property
        def value(self):
            return 1

    assert isinstance(C.value, async_property)


async def test_async_property_parameterized_executor():
    class C:
        @async_property(executor="thread")
        def value(self):
            return 42

    assert await C().value == 42


async def test_async_property_getter_exception_propagates():
    class C:
        @async_property
        def value(self):
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await C().value


# --- async_cached_property --------------------------------------------------


async def test_cached_property_caches_value():
    class C:
        def __init__(self):
            self.v = 1

        @async_cached_property
        def value(self):
            return self.v

    c = C()
    assert await c.value == 1
    c.v = 999
    assert await c.value == 1  # cached, ignores the state change


async def test_cached_property_computes_once_under_concurrency():
    calls = 0

    class C:
        @async_cached_property
        def value(self):
            nonlocal calls
            calls += 1
            return 7

    c = C()
    results = await asyncio.gather(*(_read(c) for _ in range(20)))
    assert results == [7] * 20
    assert calls == 1


async def _read(c):
    return await c.value


async def test_cached_property_per_instance_isolation():
    class C:
        def __init__(self, v):
            self.v = v

        @async_cached_property
        def value(self):
            return self.v

    a, b = C(1), C(2)
    assert await a.value == 1
    assert await b.value == 2


async def test_cached_property_delete_recomputes():
    calls = 0

    class C:
        @async_cached_property
        def value(self):
            nonlocal calls
            calls += 1
            return calls

    c = C()
    assert await c.value == 1
    assert await c.value == 1  # cached
    del c.value
    assert await c.value == 2  # recomputed


async def test_cached_property_manual_set_overrides():
    class C:
        @async_cached_property
        def value(self):
            return 1

    c = C()
    c.value = 100  # type: ignore[misc]
    assert await c.value == 100


def test_cached_property_class_access_returns_descriptor():
    class C:
        @async_cached_property
        def value(self):
            return 1

    assert isinstance(C.value, async_cached_property)


async def test_cached_property_getter_exception_propagates():
    class C:
        @async_cached_property
        def value(self):
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await C().value


async def test_cached_property_parameterized_executor():
    class C:
        def __init__(self):
            self.v = 5

        @async_cached_property(executor="thread")
        def value(self):
            return self.v

    assert await C().value == 5


# --- unbound descriptors (no getter) ----------------------------------------


def test_async_property_without_getter_raises():
    class C:
        pass

    C.p = async_property()  # type: ignore[attr-defined]
    with pytest.raises(AttributeError):
        _ = C().p


def test_async_cached_property_without_getter_raises():
    class C:
        pass

    C.p = async_cached_property()  # type: ignore[attr-defined]
    with pytest.raises(AttributeError):
        _ = C().p

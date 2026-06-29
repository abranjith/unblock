"""Asynchronous property descriptors.

``async_property`` runs its getter off the event loop and is awaited at the
access site (``await obj.prop``). ``async_cached_property`` does the same but
computes the value exactly once -- even under concurrent awaits -- and caches it
on the instance.

Both are plain descriptors; they deliberately do not subclass :class:`property`
(whose ``fget``/``fset``/``fdel`` machinery would be unused dead weight).
"""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Awaitable, Callable
from typing import Any, Generic, TypeVar, cast, overload

from ._executors import ExecutorKind
from ._scheduling import schedule

__all__ = ["async_property", "async_cached_property"]

_T = TypeVar("_T")


class async_property(Generic[_T]):
    """An asynchronous, non-cached property.

    Usage::

        class C:
            @async_property
            def value(self):
                return compute()

        await C().value

    The getter runs on the configured executor every time the property is
    awaited, so it always reflects current state.
    """

    _fget: Callable[[Any], _T] | None

    def __init__(
        self,
        fget: Callable[[Any], _T] | None = None,
        *,
        executor: ExecutorKind = "thread",
    ) -> None:
        self._executor = executor
        self._name = ""
        self._fget = None
        if fget is not None:
            self._bind(fget)

    def _bind(self, fget: Callable[[Any], _T]) -> None:
        self._fget = fget
        self._name = fget.__name__
        self.__doc__ = fget.__doc__

    def __call__(self, fget: Callable[[Any], _T]) -> async_property[_T]:
        # Supports the parameterized form: @async_property(executor="process").
        self._bind(fget)
        return self

    def __set_name__(self, owner: type, name: str) -> None:
        self._name = name

    @overload
    def __get__(self, obj: None, objtype: Any = None) -> async_property[_T]: ...
    @overload
    def __get__(self, obj: object, objtype: Any = None) -> Awaitable[_T]: ...
    def __get__(
        self, obj: Any, objtype: Any = None
    ) -> async_property[_T] | Awaitable[_T]:
        if obj is None:
            return self
        if self._fget is None:
            raise AttributeError("unreadable attribute")
        return schedule(functools.partial(self._fget, obj), self._executor)


class async_cached_property(Generic[_T]):
    """An asynchronous property whose value is computed once and cached.

    Usage::

        class C:
            @async_cached_property
            def value(self):
                return expensive()

        c = C()
        await c.value  # computes
        await c.value  # returns the cached value

    The getter runs at most once per instance, even if the property is awaited
    concurrently (a per-instance lock serializes the first computation).
    Assigning to the attribute overrides the cache; ``del`` clears it.
    """

    _fget: Callable[[Any], _T] | None

    def __init__(
        self,
        fget: Callable[[Any], _T] | None = None,
        *,
        executor: ExecutorKind = "thread",
    ) -> None:
        self._executor = executor
        self._name = ""
        self._fget = None
        if fget is not None:
            self._bind(fget)

    def _bind(self, fget: Callable[[Any], _T]) -> None:
        self._fget = fget
        self._name = fget.__name__
        self.__doc__ = fget.__doc__

    def __call__(self, fget: Callable[[Any], _T]) -> async_cached_property[_T]:
        self._bind(fget)
        return self

    def __set_name__(self, owner: type, name: str) -> None:
        self._name = name

    @property
    def _lock_key(self) -> str:
        return f"__unblock_lock_{self._name}"

    def _get_lock(self, obj: Any) -> asyncio.Lock:
        lock: asyncio.Lock | None = obj.__dict__.get(self._lock_key)
        if lock is None:
            lock = asyncio.Lock()
            obj.__dict__[self._lock_key] = lock
        return lock

    async def _get_or_compute(self, obj: Any) -> _T:
        cache = obj.__dict__
        if self._name in cache:
            return cast(_T, cache[self._name])
        async with self._get_lock(obj):
            if self._name in cache:  # double-checked after awaiting the lock
                return cast(_T, cache[self._name])
            assert self._fget is not None
            value = await schedule(functools.partial(self._fget, obj), self._executor)
            cache[self._name] = value
            return value

    @overload
    def __get__(self, obj: None, objtype: Any = None) -> async_cached_property[_T]: ...
    @overload
    def __get__(self, obj: object, objtype: Any = None) -> Awaitable[_T]: ...
    def __get__(
        self, obj: Any, objtype: Any = None
    ) -> async_cached_property[_T] | Awaitable[_T]:
        if obj is None:
            return self
        if self._fget is None:
            raise AttributeError("unreadable attribute")
        return self._get_or_compute(obj)

    def __set__(self, obj: Any, value: _T) -> None:
        obj.__dict__[self._name] = value

    def __delete__(self, obj: Any) -> None:
        obj.__dict__.pop(self._name, None)
        obj.__dict__.pop(self._lock_key, None)

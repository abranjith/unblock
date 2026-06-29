"""Class-level asyncification: the ``@asyncify`` class path and the mixins.

Two ways to asyncify a class:

* The ``@asyncify`` decorator (delegated here from :mod:`unblock.functions`)
  rewrites selected methods in place and auto-detects the iterator and
  context-manager protocols.
* The mixin family (:class:`AsyncMixin`, :class:`AsyncIterMixin`,
  :class:`AsyncContextMixin`, :class:`AsyncContextIterMixin`) wraps an existing
  class without editing it, with the executor chosen by class keyword.

Both share the same selection + build-once wrapping logic, so a method's async
wrapper is created exactly once at class-definition time (not rebuilt on every
attribute access).

Note:
    The ``executor`` choice affects regular method wrapping only. The protocol
    methods (async iteration and async context management) always run on the
    thread pool: iterating or entering a context in a separate process would
    operate on a pickled copy and lose state mutations.
"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Iterable
from typing import Any

from ._executors import ExecutorKind
from ._scheduling import schedule
from .errors import UnblockError
from .functions import _asyncify_callable

__all__ = [
    "AsyncMixin",
    "AsyncIterMixin",
    "AsyncContextMixin",
    "AsyncContextIterMixin",
]

# ``close``/``aclose`` are reserved cleanup hooks managed by __aexit__; they are
# never auto-wrapped as ordinary async methods.
_RESERVED = frozenset({"close", "aclose"})


# --- method selection & wrapping -------------------------------------------


def _is_wrappable(attr: Any) -> bool:
    return inspect.isfunction(attr) and not inspect.iscoroutinefunction(attr)


def _resolve(namespaces: list[dict[str, Any]], name: str) -> Any:
    for ns in namespaces:
        if name in ns:
            return ns[name]
    return None


def _collect_default(namespaces: list[dict[str, Any]]) -> list[str]:
    """Public, synchronous instance methods across the given namespaces."""
    seen: dict[str, None] = {}
    for ns in namespaces:
        for name, attr in ns.items():
            if name in seen or name.startswith("_") or name in _RESERVED:
                continue
            if _is_wrappable(attr):
                seen[name] = None
    return list(seen)


def _as_names(value: object) -> tuple[str, ...] | None:
    if value is None:
        return None
    if isinstance(value, str):
        raise UnblockError(
            "include/exclude must be an iterable of method names, not a string"
        )
    if not isinstance(value, Iterable):
        raise UnblockError("include/exclude must be an iterable of method names")
    return tuple(value)


def _select(
    include: object, exclude: object, namespaces: list[dict[str, Any]]
) -> list[str]:
    inc = _as_names(include)
    exc = _as_names(exclude)
    if inc is not None and exc is not None:
        raise UnblockError("pass either include or exclude to asyncify, not both")
    if inc is not None:
        for name in inc:
            func = _resolve(namespaces, name)
            if func is None or not _is_wrappable(func):
                raise UnblockError(
                    f"include: {name!r} is not a synchronous instance method "
                    f"on the class"
                )
        return list(inc)
    excluded = set(exc) if exc is not None else set()
    return [n for n in _collect_default(namespaces) if n not in excluded]


def _wrap_methods(
    cls: Any,
    executor: ExecutorKind,
    include: object,
    exclude: object,
    namespaces: list[dict[str, Any]],
) -> None:
    names = _select(include, exclude, namespaces)
    for name in names:
        func = _resolve(namespaces, name)
        setattr(cls, name, _asyncify_callable(func, executor))
    cls.__unblock_wrapped__ = frozenset(names)
    cls._unblock_executor = executor


# --- protocol implementations (always thread-based) -------------------------


def _no_params(method: Any) -> bool:
    try:
        sig = inspect.signature(method)
    except (TypeError, ValueError):
        return False
    return len(sig.parameters) == 0


def _aiter(self: Any) -> Any:
    # iter(self) calls the (untouched) synchronous __iter__.
    self._unblock_iter = iter(self)
    return self


async def _anext(self: Any) -> Any:
    def _step() -> Any:
        try:
            return next(self._unblock_iter)
        except StopIteration as ex:
            raise StopAsyncIteration from ex

    return await schedule(_step, "thread")


async def _aenter(self: Any) -> Any:
    enter = getattr(self, "__enter__", None)
    if enter is not None:
        return await schedule(enter, "thread")
    return self


async def _run_cleanup(self: Any, exit_handled: bool) -> None:
    aclose = getattr(self, "aclose", None)
    if callable(aclose) and _no_params(aclose):
        if inspect.iscoroutinefunction(aclose):
            await aclose()
        else:
            await schedule(aclose, "thread")
        return
    if not exit_handled:
        close = getattr(self, "close", None)
        if callable(close) and _no_params(close):
            await schedule(close, "thread")


async def _aexit(self: Any, exc_type: Any, exc: Any, tb: Any) -> bool:
    exit_ = getattr(self, "__exit__", None)
    suppress = False
    if exit_ is not None:
        result = await schedule(functools.partial(exit_, exc_type, exc, tb), "thread")
        suppress = bool(result)
    if getattr(self, "call_close_on_exit", True):
        await _run_cleanup(self, exit_handled=exit_ is not None)
    return suppress


def _install_async_iter(cls: Any) -> None:
    cls.__aiter__ = _aiter
    cls.__anext__ = _anext


def _install_async_context(cls: Any) -> None:
    cls.__aenter__ = _aenter
    cls.__aexit__ = _aexit
    if not hasattr(cls, "call_close_on_exit"):
        cls.call_close_on_exit = True


def _apply_protocols(cls: type) -> None:
    """Add async iterator / context-manager protocols where appropriate.

    A protocol is added when the class implements its synchronous counterpart,
    or when the class explicitly opts in via the corresponding mixin (which lets
    a class with only ``close()`` be used as an async context manager).
    """
    wants_iter = issubclass(cls, AsyncIterMixin)
    wants_ctx = issubclass(cls, AsyncContextMixin)
    has_iter = hasattr(cls, "__iter__") and hasattr(cls, "__next__")
    has_ctx = hasattr(cls, "__enter__") and hasattr(cls, "__exit__")

    if (has_iter or wants_iter) and not hasattr(cls, "__anext__"):
        _install_async_iter(cls)
    if (has_ctx or wants_ctx) and not hasattr(cls, "__aexit__"):
        _install_async_context(cls)


# --- decorator entry point (called by unblock.functions.asyncify) ----------


def _asyncify_class(
    cls: type,
    *,
    executor: ExecutorKind = "thread",
    include: object = None,
    exclude: object = None,
) -> type:
    """Asyncify ``cls`` in place: wrap selected methods and add protocols."""
    _wrap_methods(cls, executor, include, exclude, [dict(vars(cls))])
    _apply_protocols(cls)
    return cls


# --- mixins ----------------------------------------------------------------


def _mixin_namespaces(cls: type) -> list[dict[str, Any]]:
    """Namespaces to scan for a mixin subclass: the user classes in the MRO.

    Excludes this module's mixin classes and ``object`` so only the wrapped
    base class(es) and the subclass itself contribute methods.
    """
    return [
        dict(vars(c))
        for c in cls.__mro__
        if c.__module__ != __name__ and c is not object
    ]


class _AsyncMixinBase:
    """Shared ``__init_subclass__`` wrapping for the mixin family."""

    def __init_subclass__(
        cls,
        *,
        executor: ExecutorKind = "thread",
        include: object = None,
        exclude: object = None,
        **kwargs: Any,
    ) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__module__ == __name__:
            # One of our own mixin class definitions; nothing to wrap.
            return
        _wrap_methods(cls, executor, include, exclude, _mixin_namespaces(cls))
        _apply_protocols(cls)


class AsyncMixin(_AsyncMixinBase):
    """Wrap a base class's public methods; auto-detect iterator/context protocols.

    Usage::

        class Wrapper(MyClass, AsyncMixin, executor="process"):
            pass
    """


class AsyncIterMixin(AsyncMixin):
    """Like :class:`AsyncMixin`, and provide async iteration over a sync iterator."""


class AsyncContextMixin(AsyncMixin):
    """Like :class:`AsyncMixin`, and provide an async context manager.

    Works even when the wrapped class is not a real context manager but exposes
    a ``close()`` method.
    """


class AsyncContextIterMixin(AsyncIterMixin, AsyncContextMixin):
    """Combine async iteration and async context management."""

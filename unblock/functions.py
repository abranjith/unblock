"""The unified ``asyncify`` entry point for functions, methods, and classes.

``asyncify`` is the single public converter. It works as a bare decorator
(``@asyncify``), a parameterized decorator (``@asyncify(executor="process")``),
or a direct call (``asyncify(fn)``). For classes it delegates to
:mod:`unblock.classes`.
"""

from __future__ import annotations

import functools
import importlib
import inspect
from collections.abc import Awaitable, Callable
from typing import Any, ParamSpec, TypeVar, cast, overload

from . import _executors
from ._executors import ExecutorKind
from ._scheduling import schedule
from .errors import UnblockError

__all__ = ["asyncify"]

_P = ParamSpec("_P")
_T = TypeVar("_T")
_ClassT = TypeVar("_ClassT", bound=type)


def _ensure_picklable(func: Callable[..., Any]) -> None:
    """Reject callables the process pool can never pickle, at decoration time.

    Closures, lambdas, and locally defined functions are unpicklable by the
    standard library, so no trampoline can help. Failing here gives a clear
    message instead of a cryptic ``PicklingError`` from inside the pool.
    """
    qualname = getattr(func, "__qualname__", "")
    name = getattr(func, "__name__", "")
    if "<locals>" in qualname or name == "<lambda>":
        raise UnblockError(
            f"cannot use a process pool with {qualname or name!r}: closures, "
            f"lambdas, and locally-defined functions cannot be pickled. Define "
            f"it at module level, or use executor='thread'."
        )


def _run_via_reference(
    module: str,
    qualname: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    """Re-resolve an asyncified callable in a worker process and run it.

    Submitted to the process pool in place of the original function. Because it
    is a module-level function it pickles by reference; it imports ``module``,
    walks the dotted ``qualname`` to the (asyncified) attribute, unwraps it via
    ``__wrapped__``, and calls the underlying synchronous function. This is what
    lets ``@asyncify(executor="process")`` work as a decorator.
    """
    obj: Any = importlib.import_module(module)
    for part in qualname.split("."):
        obj = getattr(obj, part)
    target = getattr(obj, "__wrapped__", obj)
    return target(*args, **kwargs)


def _asyncify_callable(
    func: Callable[_P, _T], executor: ExecutorKind
) -> Callable[_P, Awaitable[_T]]:
    """Wrap a single synchronous callable so calling it returns an awaitable."""
    is_process = _executors.is_process_executor(executor)
    if is_process:
        _ensure_picklable(func)

    # Method descriptors (e.g. some C-level slots) expose the real function via
    # __func__; use it so partial() binds the right callable.
    if inspect.ismethoddescriptor(func) and hasattr(func, "__func__"):
        thread_target: Callable[..., _T] = func.__func__
    else:
        thread_target = func

    module: str = getattr(func, "__module__", "")
    qualname: str = getattr(func, "__qualname__", "")

    @functools.wraps(func)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> Awaitable[_T]:
        # Avoid spawning nested process pools from inside a worker process; run
        # on a thread there instead.
        if is_process and not _executors.in_worker_process():
            fn: Callable[[], _T] = functools.partial(
                _run_via_reference, module, qualname, args, kwargs
            )
            return schedule(fn, executor)
        fn = functools.partial(thread_target, *args, **kwargs)
        target_executor: ExecutorKind = "thread" if is_process else executor
        return schedule(fn, target_executor)

    return wrapper


@overload
def asyncify(obj: _ClassT) -> _ClassT: ...
@overload
def asyncify(
    obj: _ClassT,
    *,
    executor: ExecutorKind = ...,
    include: object = ...,
    exclude: object = ...,
) -> _ClassT: ...
@overload
def asyncify(obj: Callable[_P, _T]) -> Callable[_P, Awaitable[_T]]: ...
@overload
def asyncify(
    obj: Callable[_P, _T], *, executor: ExecutorKind = ...
) -> Callable[_P, Awaitable[_T]]: ...
@overload
def asyncify(
    obj: None = ...,
    *,
    executor: ExecutorKind = ...,
    include: object = ...,
    exclude: object = ...,
) -> Callable[[Callable[_P, _T]], Callable[_P, Awaitable[_T]]]: ...
def asyncify(
    obj: Any = None,
    *,
    executor: ExecutorKind = "thread",
    include: object = None,
    exclude: object = None,
) -> Any:
    """Convert a synchronous callable or class to its asynchronous form.

    Usage forms:

    * ``@asyncify`` on a function or method -> an async version (thread pool).
    * ``@asyncify(executor="process")`` -> runs on the process pool. Works as a
      decorator on any importable (module-level) function; closures, lambdas,
      and locally-defined functions are rejected with :class:`UnblockError`.
    * ``@asyncify`` / ``@asyncify(include=..., exclude=...)`` on a **class** ->
      asyncify selected methods in place and auto-add async iterator /
      context-manager protocol methods (see :mod:`unblock.classes`).
    * ``asyncify(fn)`` -> the direct-call form, equivalent to the decorator.

    Args:
        obj: The function, method, class, or ``None`` (parameterized form).
        executor: ``"thread"`` (default), ``"process"``, or a concrete
            :class:`concurrent.futures.Executor` instance.
        include: Class use only -- asyncify exactly these method names.
        exclude: Class use only -- asyncify all public methods except these.

    Returns:
        For a callable, a wrapper returning an awaitable; for a class, the same
        class with methods asyncified; for ``None``, a configured decorator.

    Raises:
        UnblockError: if ``obj`` is not a function, method, or class; if
            ``include``/``exclude`` are given for a non-class; or if a process
            executor is requested for an unpicklable callable.

    Note:
        Cancelling the returned awaitable cannot forcibly stop work that has
        already started in a thread or process (standard
        :meth:`asyncio.loop.run_in_executor` behaviour). Already-async functions
        are returned unchanged.
    """
    if obj is None:

        def decorator(target: Callable[_P, _T]) -> Callable[_P, Awaitable[_T]]:
            return cast(
                "Callable[_P, Awaitable[_T]]",
                _dispatch(target, executor, include, exclude),
            )

        return decorator

    return _dispatch(obj, executor, include, exclude)


def _dispatch(
    obj: Any, executor: ExecutorKind, include: object, exclude: object
) -> Any:
    """Route ``obj`` (callable or class) to the right asyncification path."""
    if inspect.isclass(obj):
        from .classes import _asyncify_class

        return _asyncify_class(obj, executor=executor, include=include, exclude=exclude)

    if include is not None or exclude is not None:
        raise UnblockError("include/exclude are only valid when asyncifying a class")

    if inspect.iscoroutinefunction(obj):
        return obj

    if inspect.isroutine(obj):
        return _asyncify_callable(obj, executor)

    raise UnblockError(
        f"asyncify cannot convert {obj!r}; expected a function, method, or class"
    )

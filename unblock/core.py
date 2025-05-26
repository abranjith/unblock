"""
unblock.core - Core Asyncification Utilities

This module provides the central building blocks for transforming synchronous Python code
into asynchronous code. It includes:

-   High-level asyncification functions (`asyncify`, `asyncify_pp`) that can adapt
    individual functions or entire classes.
-   Specialized asyncification functions for functions (`asyncify_func`, `asyncify_func_pp`)
    and classes (`asyncify_cls`).
-   Asynchronous property decorators (`async_property`, `async_cached_property`) that
    allow synchronous property getter methods to be called asynchronously.
-   A set of base classes (`AsyncBase`, `AsyncIterBase`, `AsyncCtxMgrBase`, etc., and their
    ProcessPool (`AsyncPP...`) counterparts) designed to be inherited by synchronous
    classes. These base classes, in conjunction with a metaclass (`_AsyncMetaType`),
    can automatically make specified methods of the inheriting class behave asynchronously.
-   Internal helper functions that support the asyncification process, managing execution
    in thread or process pools and handling attribute access intricacies.

The primary goal is to allow synchronous libraries or code sections to be used in an
asynchronous context with minimal explicit modifications, typically by running the
synchronous code in a separate thread or process.
"""

__all__ = [
    "asyncify",
    "asyncify_func",
    "asyncify_cls",
    "asyncify_pp",
    "asyncify_func_pp",
    "async_property",
    "async_cached_property",
    "AsyncBase",
    "AsyncIterBase",
    "AsyncCtxMgrBase",
    "AsyncCtxMgrIterBase",
    "AsyncPPBase",
    "AsyncPPIterBase",
    "AsyncPPCtxMgrBase",
    "AsyncPPCtxMgrIterBase",
]


import inspect
from functools import wraps, partial
import contextlib
import multiprocessing
from types import TracebackType
from typing import (
    Callable,
    Awaitable,
    Type,
    Union,
    Any,
    Optional,
    List,
    TypeVar,
    Iterator as TypingIterator, # Renamed to avoid conflict with _original_iterobj
)
from .common import Registry, UnblockException

# Type variables for generic self types
_R = TypeVar('_R')
_T = TypeVar('_T')
_AsyncBaseT = TypeVar('_AsyncBaseT', bound='_AsyncBase')
_AsyncIterBaseT = TypeVar('_AsyncIterBaseT', bound='AsyncIterBase')
_AsyncCtxMgrBaseT = TypeVar('_AsyncCtxMgrBaseT', bound='AsyncCtxMgrBase')
_AsyncPPIterBaseT = TypeVar('_AsyncPPIterBaseT', bound='AsyncPPIterBase')
_AsyncPPCtxMgrBaseT = TypeVar('_AsyncPPCtxMgrBaseT', bound='AsyncPPCtxMgrBase')


# More specific Callable types
CallableAny = Callable[..., Any]
CallableToAwaitableAny = Callable[..., Awaitable[Any]]
CallableToBool = Callable[[CallableAny], bool]
CallableToFuture = Callable[[Callable[[], _R]], Awaitable[_R]]


def asyncify(arg: Union[CallableAny, Awaitable[Any], Type[Any]]) -> Union[Awaitable[Any], Type[Any]]:
    """
    Universal asyncifier for functions and classes using a ThreadPoolExecutor.

    - If `arg` is a coroutine function, it's returned as is.
    - If `arg` is a regular function or method, it's wrapped by `asyncify_func`.
    - If `arg` is a class, its public methods are wrapped using `asyncify_cls`.

    Args:
        arg: The function, method, or class to asyncify.

    Returns:
        An awaitable version of the function/method, or an asyncified class.
    """
    if inspect.iscoroutinefunction(arg):
        return arg  # Already async, no action needed.
    if inspect.isroutine(arg): # Includes functions, methods, bound methods.
        return asyncify_func(arg)
    if inspect.isclass(arg):
        return asyncify_cls(arg)
    return arg # Return arg itself if not a coroutine, routine or class.


def _is_method_descriptor(func: CallableAny) -> bool:
    """
    Checks if `func` is a method descriptor that has a `__func__` attribute.

    Method descriptors (like `list.append`) need special handling as their `__func__`
    attribute provides the actual function, and `self` is passed as the first argument.

    Args:
        func: The callable to check.

    Returns:
        True if `func` is a method descriptor with `__func__`, False otherwise.
    """
    return inspect.ismethoddescriptor(func) and hasattr(func, "__func__")


def _asyncify_func_helper(
    func: CallableAny,
    get_future_func: CallableToFuture, # e.g. Callable[[Callable[[], _R]], Awaitable[_R]]
    is_method_descriptor_check_func: CallableToBool, # e.g. Callable[[CallableAny], bool]
) -> CallableToAwaitableAny: # Returns the wrapper, which itself is callable and produces an awaitable
    """
    Core helper for creating an awaitable wrapper around a synchronous function.

    This function generalizes `asyncify_func` and `asyncify_func_pp`. It takes the
    original synchronous function (`func`), a function to obtain a future
    (`get_future_func`, e.g., from a thread or process pool), and a function
    to check for method descriptors (`is_method_descriptor_check_func`).

    The wrapper it creates ensures that when the wrapped function is called:
    1.  If it's a method descriptor, `func.__func__` is used with the instance (`args[0]`)
        bound correctly.
    2.  Otherwise, `func` is used directly.
    3.  The call is then scheduled via `get_future_func`.
    4.  If an event loop is running, it returns an awaitable future; otherwise, it
        returns a coroutine that, when awaited, runs the function.

    Args:
        func: The synchronous function to wrap.
        get_future_func: A callable that takes another callable (the partially applied
                         synchronous function) and returns a future-like object
                         (e.g., `_get_future_from_threadpool`).
        is_method_descriptor_check_func: A callable that checks if `func` is a
                                         method descriptor requiring special handling.

    Returns:
        A callable wrapper that, when called, executes the original function asynchronously
        and returns an awaitable for its result.
    """

    @wraps(func)
    def _fut(fn_to_run_in_executor: Callable[[], _R]) -> Awaitable[_R]:
        """Helper to submit the function to the executor."""
        return get_future_func(fn_to_run_in_executor)

    @wraps(func)
    async def _coro(fn_to_run_in_executor: Callable[[], _R]) -> _R:
        """Coroutine wrapper that awaits the future."""
        return await _fut(fn_to_run_in_executor)

    @wraps(func)
    def _wrapper(*args: Any, **kwargs: Any) -> Union[Awaitable[Any], Any]: # Actual return of wrapper call
        """The actual wrapper that handles argument binding and execution strategy."""
        fn_with_args: Callable[[], Any]
        if is_method_descriptor_check_func(func):
            fn_with_args = partial(func.__func__, *args, **kwargs)
        else:
            fn_with_args = partial(func, *args, **kwargs)

        return _fut(fn_with_args) if Registry.is_event_loop_running() else _coro(fn_with_args)

    return _wrapper


def asyncify_func(func: CallableAny) -> CallableToAwaitableAny:
    """
    Converts a synchronous function/method to an awaitable-producing callable using a ThreadPoolExecutor.

    The returned callable, when called, executes the original synchronous function
    in a separate thread from the `Registry`'s ThreadPoolExecutor and returns an awaitable for its result.
    - If an event loop is running at call time, it returns an asyncio Future.
    - Otherwise, it returns a coroutine that, when awaited, runs the function.

    Args:
        func: The synchronous function or method to convert.

    Returns:
        An awaitable-producing version of the input function.
    """
    return _asyncify_func_helper(func, _get_future_from_threadpool, _is_method_descriptor)


def asyncify_cls(cls: Type[_T]) -> Type[_T]:
    """
    Modifies a class to make its public, synchronous methods asynchronous.

    It iterates over the class's `__dict__` and wraps all public, user-defined
    functions (excluding those starting with an underscore or non-functions)
    with `asyncify`. This uses a ThreadPoolExecutor by default.

    Note: This modifies the class in-place.

    Args:
        cls: The class to modify.

    Returns:
        The modified class with its methods asyncified.
    """
    for attr_name, attr_value in cls.__dict__.items():
        if attr_name.startswith("_") or not inspect.isfunction(attr_value):
            continue
        # Ensure mypy knows attr_value is callable here for asyncify
        if callable(attr_value):
            setattr(cls, attr_name, asyncify(attr_value))
    return cls


def asyncify_pp(arg: Union[CallableAny, Awaitable[Any], Type[Any]]) -> Union[Awaitable[Any], Type[Any]]:
    """
    Universal asyncifier for functions using a ProcessPoolExecutor.

    - If `arg` is a coroutine function, it's returned as is.
    - If `arg` is a regular function or method, it's wrapped by `asyncify_func_pp`.
    - Asyncifying classes with ProcessPool (`asyncify_cls_pp`) is generally not
      supported due to pickling complexities with class methods and processes.

    Args:
        arg: The function or method to asyncify.

    Returns:
        An awaitable version of the function/method.

    Raises:
        UnblockException: If `arg` is a class, as class asyncification via
                          ProcessPool is not supported.
    """
    if inspect.iscoroutinefunction(arg):
        return arg
    if inspect.isroutine(arg):
        return asyncify_func_pp(arg)
    if inspect.isclass(arg):
        raise UnblockException(
            f"Asyncifying class {arg.__name__} with ProcessPoolExecutor is not supported. "
            "Consider asyncifying specific methods using asyncify_func_pp or using ThreadPool-based asyncification."
        )
    return arg


def asyncify_func_pp(func: CallableAny) -> CallableToAwaitableAny:
    """
    Converts a synchronous function/method to an awaitable-producing callable using a ProcessPoolExecutor.

    Similar to `asyncify_func`, but executes the function in a separate process
    from the `Registry`'s ProcessPoolExecutor. This is suitable for CPU-bound tasks.
    Care must be taken as arguments and return values must be picklable.

    Args:
        func: The synchronous function or method to convert.

    Returns:
        An awaitable-producing version of the input function.
    """
    return _asyncify_func_helper(func, _get_future_from_processpool, _is_method_descriptor)


class async_property(property):
    _fget: Optional[Callable[[Any], Any]]

    def __init__(self, fget: Callable[[Any], Any], name: Optional[str] = None, doc: Optional[str] = None):
        self.__name__ = name or fget.__name__
        self.__module__ = fget.__module__
        self.__doc__ = doc or fget.__doc__
        self._fget = fget
        # property constructor is not called here in the stub, but it's called by Python
        # super().__init__(fget) would be typical if we were fully re-implementing

    def __set_name__(self, owner: Type[Any], name: str) -> None:
        self.__name__ = name

    def __get__(self, obj: Any, objtype: Optional[Type[Any]] = None) -> Awaitable[Any]:
        if obj is None:
            return self # type: ignore # Mypy expects property, this is fine at runtime
        if self._fget is None:
            raise AttributeError(f"Unreadable attribute {self.__name__}")
        return asyncify(self._fget)(obj)


class async_cached_property(property):
    _fget: Optional[Callable[[Any], Any]]

    def __init__(self, fget: Callable[[Any], Any], name: Optional[str] = None, doc: Optional[str] = None):
        self.__name__ = name or fget.__name__
        self.__module__ = fget.__module__
        self.__doc__ = doc or fget.__doc__
        self._fget = fget
        # property constructor is not called here in the stub

    def __set_name__(self, owner: Type[Any], name: str) -> None:
        self.__name__ = name

    def __set__(self, obj: Any, value: Any) -> None:
        obj.__dict__[self.__name__] = value

    def __get__(self, obj: Any, objtype: Optional[Type[Any]] = None) -> Awaitable[Any]: # Runtime returns awaitable
        if obj is None:
            return self # type: ignore
        if self._fget is None:
            raise AttributeError(f"Unreadable attribute {self.__name__}")
        return self._get_or_add(obj)

    async def _get_or_add(self, obj: Any) -> Any:
        _missing = object()
        value = obj.__dict__.get(self.__name__, _missing)
        if value is _missing:
            if self._fget is None: # Should not happen if __get__ checks first
                 raise AttributeError(f"Unreadable attribute {self.__name__} in _get_or_add")
            value = await asyncify(self._fget)(obj)
            obj.__dict__[self.__name__] = value
        return value


def _process_attribute_access(
    owner_obj: Any,
    attr_name: str,
    attribute_val: Any,
    methods_to_asyncify_list_func: Callable[[], List[str]],
    asyncify_call_func: Callable[[CallableAny], Awaitable[Any]],
) -> Any:
    if attr_name in ("_unblock_methods_to_asynchify", "_unblock_asyncify"):
        return attribute_val
    if attr_name in methods_to_asyncify_list_func():
        if _is_descriptor_or_nonmethod(attribute_val):
            raise UnblockException(
                f"Attribute '{attr_name}' on {owner_obj} is listed in _unblock_methods_to_asynchify "
                f"but it is a descriptor or not a callable. Only regular methods/functions "
                f"can be automatically asyncified by this mechanism. Explicitly wrap or handle "
                f"such attributes if async behavior is needed."
            )
        return asyncify_call_func(attribute_val)
    return attribute_val


class _AsyncMetaType(type):
    def __getattribute__(cls, name: str) -> Any:
        attribute_val = super().__getattribute__(name)
        # Assuming _unblock_methods_to_asynchify and _unblock_asyncify exist due to _AsyncBase
        return _process_attribute_access(
            cls, name, attribute_val,
            cls._unblock_methods_to_asynchify, # type: ignore [attr-defined]
            cls._unblock_asyncify # type: ignore [attr-defined]
        )


class _AsyncBase(metaclass=_AsyncMetaType):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def __getattribute__(self, name: str) -> Any:
        attribute_val = object.__getattribute__(self, name)
        return _process_attribute_access(
            self, name, attribute_val, self._unblock_methods_to_asynchify, self._unblock_asyncify
        )

    @staticmethod
    def _unblock_methods_to_asynchify() -> List[str]:
        return []

    @staticmethod
    def _unblock_asyncify(attr: CallableAny) -> Awaitable[Any]:
        # This should be implemented by subclasses like AsyncBase or AsyncPPBase
        raise NotImplementedError("Subclasses must implement _unblock_asyncify")


class AsyncBase(_AsyncBase):
    @staticmethod
    def _unblock_asyncify(attr: CallableAny) -> Awaitable[Any]:
        return asyncify(attr) # type: ignore # asyncify can return Type, but here attr is Callable


class AsyncPPBase(_AsyncBase):
    @staticmethod
    def _unblock_asyncify(attr: CallableAny) -> Awaitable[Any]:
        if multiprocessing.current_process().name != "MainProcess":
            # This path returns a callable, not an Awaitable.
            # However, the expectation from _process_attribute_access is an Awaitable.
            # This needs careful handling. If it's meant to be a no-op,
            # it should still be awaitable if the signature demands it.
            # For now, type ignore, but this implies a runtime type mismatch if not handled carefully.
            return attr # type: ignore
        return asyncify_pp(attr) # type: ignore # asyncify_pp can return Type


class AsyncIterBase(AsyncBase):
    _original_iterobj: TypingIterator[Any]

    def __aiter__(self: _AsyncIterBaseT) -> _AsyncIterBaseT:
        self._original_iterobj = iter(self) # type: ignore # self is iterable
        return self

    async def __anext__(self) -> Any:
        def _sync_next() -> Any:
            try:
                return next(self._original_iterobj)
            except StopIteration as e:
                raise StopAsyncIteration from e
        return await asyncify_func(_sync_next)()


class AsyncCtxMgrBase(AsyncBase):
    call_close_on_exit: bool = True
    _stack: Optional[contextlib.ExitStack] = None

    async def __aenter__(self: _AsyncCtxMgrBaseT) -> _AsyncCtxMgrBaseT:
        self._stack = None
        if hasattr(self, "__enter__"):
            with contextlib.ExitStack() as stack:
                # We need to ensure `self` is a ContextManager if __enter__ is present.
                # This is a runtime check essentially.
                stack.enter_context(self) # type: ignore [arg-type]
                self._stack = stack.pop_all()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        if self._stack is not None:
            # The __exit__ of ExitStack returns a boolean indicating if exception was handled.
            handled = self._stack.__exit__(exc_type, exc_value, traceback)
            if self.call_close_on_exit and _has_callable_aclose(self):
                await self._unblock_asyncify(self.aclose)() # type: ignore [attr-defined]
            # If the original __exit__ handled the exception, reflect that.
            return handled if handled else None # Return None if not handled, to match Optional[bool]

        if not self.call_close_on_exit:
            return None # Explicitly return None if no action is taken.

        # Ensure self has 'close' or 'aclose' if calling them
        # _unblock_asyncify is from AsyncBase (or overridden)
        if _has_callable_close(self):
            await self._unblock_asyncify(self.close)() # type: ignore [attr-defined]
        elif _has_callable_aclose(self):
            await self._unblock_asyncify(self.aclose)() # type: ignore [attr-defined]
        return None # Default to not handling the exception if only close/aclose was called.


class AsyncCtxMgrIterBase(AsyncIterBase, AsyncCtxMgrBase):
    pass


class AsyncPPIterBase(AsyncPPBase):
    _original_iterobj: TypingIterator[Any]

    def __aiter__(self: _AsyncPPIterBaseT) -> _AsyncPPIterBaseT:
        self._original_iterobj = iter(self) # type: ignore
        return self

    async def __anext__(self) -> Any:
        def _sync_next() -> Any:
            try:
                return next(self._original_iterobj)
            except StopIteration as e:
                raise StopAsyncIteration from e
        return await asyncify_func(_sync_next)()


class AsyncPPCtxMgrBase(AsyncPPBase):
    call_close_on_exit: bool = True
    _stack: Optional[contextlib.ExitStack] = None

    async def __aenter__(self: _AsyncPPCtxMgrBaseT) -> _AsyncPPCtxMgrBaseT:
        self._stack = None
        if hasattr(self, "__enter__"):
            with contextlib.ExitStack() as stack:
                stack.enter_context(self) # type: ignore [arg-type]
                self._stack = stack.pop_all()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        if self._stack is not None:
            handled = self._stack.__exit__(exc_type, exc_value, traceback)
            if self.call_close_on_exit and _has_callable_aclose(self):
                await self._unblock_asyncify(self.aclose)() # type: ignore [attr-defined]
            return handled if handled else None

        if not self.call_close_on_exit:
            return None

        if _has_callable_close(self):
            await self._unblock_asyncify(self.close)() # type: ignore [attr-defined]
        elif _has_callable_aclose(self):
            await self._unblock_asyncify(self.aclose)() # type: ignore [attr-defined]
        return None


class AsyncPPCtxMgrIterBase(AsyncPPIterBase, AsyncPPCtxMgrBase):
    pass


def _get_future_from_threadpool(fn: Callable[[], _R]) -> Awaitable[_R]:
    loop = Registry.get_event_loop()
    executor = Registry.get_threadpool_executor()
    return loop.run_in_executor(executor, fn)


def _get_future_from_processpool(fn: Callable[[], _R]) -> Awaitable[_R]:
    loop = Registry.get_event_loop()
    executor = Registry.get_processpool_executor()
    return loop.run_in_executor(executor, fn)


def _has_callable_close(obj: Any) -> bool:
    if hasattr(obj, "close"):
        close_method = getattr(obj, "close")
        return inspect.isroutine(close_method) and not any(inspect.signature(close_method).parameters)
    return False


def _has_callable_aclose(obj: Any) -> bool:
    if hasattr(obj, "aclose"):
        aclose_method = getattr(obj, "aclose")
        return inspect.isroutine(aclose_method) and not any(inspect.signature(aclose_method).parameters)
    return False


def _is_descriptor_or_nonmethod(attr: Any) -> bool:
    is_any_descriptor = (
        inspect.isdatadescriptor(attr)
        or inspect.ismethoddescriptor(attr)
        or inspect.isgetsetdescriptor(attr)
        or inspect.ismemberdescriptor(attr)
    )
    return is_any_descriptor or (not inspect.isroutine(attr))

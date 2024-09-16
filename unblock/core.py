"""
Core constucts that can be used for asyncifying functions/ methods
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
from typing import Callable, Awaitable, Type, Union, Any
from .common import Registry, UnblockException


def asyncify(arg: Union[Callable, Awaitable, Type]) -> Union[Awaitable, Type]:
    """
    Converts synchronous function to asynch.
    Converts synchronous methods of class to asynch.
    """
    if inspect.iscoroutinefunction(arg):
        return arg
    if inspect.isroutine(arg):
        return asyncify_func(arg)
    if inspect.isclass(arg):
        return asyncify_cls(arg)
    return arg


def asyncify_func(func: Callable) -> Awaitable:
    """
    Converts synchronous function to asynch.
    Returns coroutine if event loop is running, else returns Future (asyncio Future)
    """

    @wraps(func)
    def _fut(fn):
        return _get_future_from_threadpool(fn)

    @wraps(func)
    async def _coro(fn):
        return await _fut(fn)

    @wraps(func)
    def _wrapper(*args, **kwargs):
        if inspect.ismethoddescriptor(func) and hasattr(func, "__func__"):
            fn = partial(func.__func__, *args, **kwargs)
        else:
            fn = partial(func, *args, **kwargs)
        return _fut(fn) if Registry.is_event_loop_running() else _coro(fn)

    return _wrapper


def asyncify_cls(cls: Type) -> Type:
    """
    Converts synchronous methods of class to asynch.
    """
    for attr_name, attr in cls.__dict__.items():
        # this is a generic logic to skip special methods
        if attr_name.startswith("_") or (not inspect.isfunction(attr)):
            continue
        setattr(cls, attr_name, asyncify(attr))
    return cls


def asyncify_pp(arg: Union[Callable, Awaitable, Type]) -> Union[Awaitable, Type]:
    """
    Similar to asyncify function above, but uses ProcessPool executor (run as a separate process)
    """
    if inspect.iscoroutinefunction(arg):
        return arg
    if inspect.isroutine(arg):
        return asyncify_func_pp(arg)
    if inspect.isclass(arg):
        raise UnblockException(f"asyncifying class {arg} is not supported using ProcessPool")
    return arg


def asyncify_func_pp(func: Callable) -> Awaitable:
    """
    Similar to asyncify_func function above, but uses ProcessPool executor (run as a separate process)
    """

    @wraps(func)
    def _fut(fn):
        return _get_future_from_processpool(fn)

    @wraps(func)
    async def _coro(fn):
        return await _fut(fn)

    @wraps(func)
    def _wrapper(*args, **kwargs):
        if inspect.ismethoddescriptor(func) and hasattr(func, "__func__"):
            fn = partial(func.__func__, *args, **kwargs)
        else:
            fn = partial(func, *args, **kwargs)
        return _fut(fn) if Registry.is_event_loop_running() else _coro(fn)

    return _wrapper

'''
# Not supported due to constraints with how pickling works.
# More on it - https://stackoverflow.com/a/52186874
def asyncify_cls_pp(cls: Type) -> Type:
    """
    Similar to asyncify_cls function above, but uses ProcessPool executor (run as a separate process)
    """
    for attr_name, attr in cls.__dict__.items():
        # this is a generic logic to skip special methods
        if attr_name.startswith("_") or (not inspect.isfunction(attr)):
            continue
        setattr(cls, attr_name, asyncify_pp(attr))
    return cls
'''

class async_property(property):
    """
    Similar to property, but async!
    Usage,
        class C:
            @async_property
            def prop(self):
                ...
        c = C()
        await c.prop()
    """

    def __init__(self, _fget, name=None, doc=None):
        self.__name__ = name or _fget.__name__
        self.__module__ = _fget.__module__
        self.__doc__ = doc or _fget.__doc__
        self._fget = _fget

    def __set_name__(self, owner, name):
        self.__name__ = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self._fget is None:
            raise AttributeError("unreadable attribute")
        return asyncify(self._fget)(obj)


class async_cached_property(property):
    """
    Similar to property, but async. Result once set is cached
    Usage,
        class C:
            @async_cached_property
            def prop(self):
                ...
        c = C()
        await c.prop()
    """
    def __init__(self, _fget, name=None, doc=None):
        self.__name__ = name or _fget.__name__
        self.__module__ = _fget.__module__
        self.__doc__ = doc or _fget.__doc__
        self._fget = _fget

    def __set_name__(self, owner, name):
        self.__name__ = name

    def __set__(self, obj, value):
        obj.__dict__[self.__name__] = value

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self._fget is None:
            raise AttributeError("unreadable attribute")
        return self._get_or_add(obj)

    async def _get_or_add(self, obj):
        missing = "__missing__"
        value = obj.__dict__.get(self.__name__, missing)
        if value is missing:
            value = await asyncify(self._fget)(obj)
            obj.__dict__[self.__name__] = value
        return value
    
class _AsyncMetaType(type):
    """
    Metaclass that takes care of asyncifying class level attributes
    """

    def __getattribute__(cls, name):
        attr = super().__getattribute__(name)
        if name in ("_unblock_methods_to_asynchify","_unblock_asyncify"):
            return attr
        
        if (name in cls._unblock_methods_to_asynchify()) and _is_descriptor_or_nonmethod(attr):
            raise UnblockException(
                f"{name} - Cannot use descriptors or non callables in _unblock_methods_to_asynchify.Instead explicitly asynchify such attributes"
            )
        
        if name in cls._unblock_methods_to_asynchify():
            return cls._unblock_asyncify(attr)
        return attr

class _AsyncBase(metaclass=_AsyncMetaType):
    """
    Base class for all class level constructs such as AsyncBase etc
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)
        if name in ("_unblock_methods_to_asynchify","_unblock_asyncify"):
            return attr
        
        if (name in self._unblock_methods_to_asynchify()) and _is_descriptor_or_nonmethod(attr):
            raise UnblockException(
                f"{name} - Cannot use descriptors or non callables in _unblock_methods_to_asynchify.Instead explicitly asynchify such attributes"
            )
        
        if name in self._unblock_methods_to_asynchify():
            return self._unblock_asyncify(attr)
        return attr

    @staticmethod
    def _unblock_methods_to_asynchify():
        return []

class AsyncBase(_AsyncBase):

    @staticmethod
    def _unblock_asyncify(attr):
        return asyncify(attr)

class AsyncPPBase(_AsyncBase):

    @staticmethod
    def _unblock_asyncify(attr):
        #if already in a spawned process, do not spawn more processes to keep it simple
        #for such use cases better to use ThreadPool vs ProcessPool
        if (multiprocessing.current_process().name != "MainProcess"):
            return attr
        return asyncify_pp(attr)
    
class AsyncIterBase(AsyncBase):
    def __aiter__(self):
        self._original_iterobj = iter(self)
        return self

    # see more re: use of synchronous iterator as coroutine here - https://bugs.python.org/issue26221
    async def __anext__(self):
        def _next():
            try:
                return next(self._original_iterobj)
            except StopIteration as ex:
                raise StopAsyncIteration from ex

        return await asyncify_func(_next)()

class AsyncCtxMgrBase(AsyncBase):
    call_close_on_exit = True

    async def __aenter__(self):
        self._stack = None
        if hasattr(self, "__enter__"):
            with contextlib.ExitStack() as stack:
                stack.enter_context(self)
                self._stack = stack.pop_all()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._stack is not None:
            self._stack.__exit__(exc_type, exc_value, traceback)
            if self.call_close_on_exit and _has_callable_aclose(self):
                await asyncify(self.aclose)()
            return
        if not self.call_close_on_exit:
            return
        if _has_callable_close(self):
            await asyncify(self.close)()
        if _has_callable_aclose(self):
            await asyncify(self.aclose)()


class AsyncCtxMgrIterBase(AsyncIterBase, AsyncCtxMgrBase):
    """objects that support iterator protocol & context manager"""


class AsyncPPIterBase(AsyncPPBase):
    def __aiter__(self):
        self._original_iterobj = iter(self)
        return self

    # see more re: use of synchronous iterator as coroutine here - https://bugs.python.org/issue26221
    async def __anext__(self):
        def _next():
            try:
                return next(self._original_iterobj)
            except StopIteration as ex:
                raise StopAsyncIteration from ex

        # it seems strange to use process pool exector for iterator, so going with thread pool executor
        return await asyncify_func(_next)()


class AsyncPPCtxMgrBase(AsyncPPBase):
    call_close_on_exit = True

    async def __aenter__(self):
        self._stack = None
        if hasattr(self, "__enter__"):
            with contextlib.ExitStack() as stack:
                stack.enter_context(self)
                self._stack = stack.pop_all()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._stack is not None:
            self._stack.__exit__(exc_type, exc_value, traceback)
            if self.call_close_on_exit and _has_callable_aclose(self):
                await asyncify(self.aclose)()
            return
        if not self.call_close_on_exit:
            return
        if _has_callable_close(self):
            await asyncify(self.close)()
        if _has_callable_aclose(self):
            await asyncify(self.aclose)()


class AsyncPPCtxMgrIterBase(AsyncPPIterBase, AsyncPPCtxMgrBase):
    """objects that support iterator protocol & context manager"""


def _get_future_from_threadpool(fn: Callable) -> Awaitable:
    loop = Registry.get_event_loop()
    executor = Registry.get_threadpool_executor()
    return loop.run_in_executor(executor, fn)


def _get_future_from_processpool(fn: Callable) -> Awaitable:
    loop = Registry.get_event_loop()
    executor = Registry.get_processpool_executor()
    return loop.run_in_executor(executor, fn)


def _has_callable_close(obj: Any) -> bool:
    if hasattr(obj, "close"):
        return inspect.isroutine(obj.close) and (
            not any(inspect.signature(obj.close).parameters)
        )
    return False


def _has_callable_aclose(obj: Any) -> bool:
    if hasattr(obj, "aclose"):
        return inspect.isroutine(obj.aclose) and (
            not any(inspect.signature(obj.aclose).parameters)
        )
    return False

def _is_descriptor_or_nonmethod(attr) -> bool:
    ismethoddesc = inspect.isdatadescriptor(attr) or inspect.ismethoddescriptor(attr) or inspect.isgetsetdescriptor(attr) or inspect.ismemberdescriptor(attr)
    return ismethoddesc or (not inspect.isroutine(attr))

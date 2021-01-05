import asyncio
import inspect
from functools import wraps, partial
from .common import Registry

DUNDER = "__"

def asyncify(arg):
    if inspect.iscoroutinefunction(arg):
        return arg
    elif inspect.isroutine(arg):
        return asyncify_func(arg)
    elif inspect.isclass(arg):
        return asyncify_cls(arg)
    return arg

def asyncify_func(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        fn = partial(func, *args, **kwargs)
        return await _get_future_from_threadpool(fn)
    return wrapper

async def _get_future_from_threadpool(fn):
    loop = Registry.get_event_loop()
    executor = Registry.get_threadpool_executor()
    return await loop.run_in_executor(executor, fn)

def asyncify_cls(cls):
    for attr_name, attr in cls.__dict__.items():
        #this is a generic logic to skip special methods
        if (attr_name.starts_with(DUNDER) and attr_name.ends_with(DUNDER)):
            continue
        setattr(cls, attr_name, asyncify(attr))
    return cls

def asyncify_x(arg):
    if inspect.iscoroutinefunction(arg):
        return arg
    elif inspect.isroutine(arg):
        return asyncify_func_x(arg)
    elif inspect.isclass(arg):
        return asyncify_cls_x(arg)
    return arg

def asyncify_func_x(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        fn = partial(func, *args, **kwargs)
        return await _get_future_from_processpool(fn)
    return wrapper

async def _get_future_from_processpool(fn):
    loop = Registry.get_event_loop()
    executor = Registry.get_processpool_executor()
    return await loop.run_in_executor(executor, fn)

def asyncify_cls_x(cls):
    for attr_name, attr in cls.__dict__.items():
        #this is a generic logic to skip special methods
        if (attr_name.starts_with(DUNDER) and attr_name.ends_with(DUNDER)):
            continue
        setattr(cls, attr_name, asyncify_x(attr))
    return cls

def async_property(property):

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


def async_cached_property(property):

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


class _AsyncBase(object):
    def __init__(self, original_obj):
        self._original_obj = original_obj
        if(hasattr(original_obj, "__doc__")):
            self.__doc__ = original_obj.__doc__
        if(hasattr(original_obj, "__repr__")):
            self.__repr__ = original_obj.__repr__
        if(hasattr(original_obj, "__str__")):
            self.__str__ = original_obj.__str__

    @property
    def _attrs_to_asynchify(self):
        return []

class AsyncBase(_AsyncBase):

    def __getattr__(self, name):
        if not hasattr(self._original_obj, name):
            raise AttributeError(f"'{self._original_obj.__class__.__name__}' object has no attribute '{name}'")
        attr = getattr(self._original_obj, name)
        if name in self._attrs_to_asynchify:
            return asyncify(attr)
        return attr

class AsyncXBase(_AsyncBase):
    
    def __getattr__(self, name):
        if not hasattr(self._original_obj, name):
            raise AttributeError(f"'{self._original_obj.__class__.__name__}' object has no attribute '{name}'")
        attr = getattr(self._original_obj, name)
        if name in self._attrs_to_asynchify:
            return asyncify_x(attr)
        return attr

class AsyncIterBase(AsyncBase):

    def __aiter__(self):
        self._itrtr = iter(self._original_obj)
        return self
    
    #see more re: use of synchronous iterator as coroutine here - https://bugs.python.org/issue26221
    async def __anext__(self):
        def _next():
            try:
                return next(self._itrtr)
            except StopIteration:
                raise StopAsyncIteration
        return await asyncify_func(_next)()

class AsyncCtxMgrBase(AsyncBase):

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if hasattr(self, "close"):
            await self.close()

class AsyncCtxMgrIterBase(AsyncIterBase, AsyncCtxMgrBase):
    """ objects that support iterator protocol & context manager """

class AsyncXIterBase(AsyncXBase):

    def __aiter__(self):
        self._itrtr = iter(self._original_obj)
        return self
    
    #see more re: use of synchronous iterator as coroutine here - https://bugs.python.org/issue26221
    async def __anext__(self):
        def _next():
            try:
                return next(self._itrtr)
            except StopIteration:
                raise StopAsyncIteration
        return await asyncify_func_x(_next)()

class AsyncXCtxMgrBase(AsyncXBase):

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if hasattr(self, "close"):
            await self.close()

class AsyncXCtxMgrIterBase(AsyncXIterBase, AsyncXCtxMgrBase):
    """ objects that support iterator protocol & context manager """

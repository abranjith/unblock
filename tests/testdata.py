from abc import abstractmethod
import sys
import asyncio
sys.path.append("..\\unblock")
from unblock import (
    asyncify_pp,
    asyncify,
    async_cached_property,
    async_property,
    AsyncPPBase,
    AsyncBase,
    AsyncCtxMgrBase,
    AsyncIterBase,
)

def test_sync_func():
    return test_sync_func.__name__

async def test_async_func():
    await asyncio.sleep(0)
    return test_async_func.__name__

class TestClass:

    @staticmethod
    def sync_static_method():
        return TestClass.sync_static_method.__name__
    
    @classmethod
    def sync_class_method(cls):
        return  f"{cls.__name__}.{TestClass.sync_class_method.__name__}"

    def __init__(self, a) -> None:
        self.a = a
    
    def sync_method(self):
        return self.sync_method.__name__
    
    async def async_method(self):
        await asyncio.sleep(0)
        return self.async_method.__name__
    
class TestAbstractClass:

    def __init__(self, a) -> None:
        self.a = a
    
    @abstractmethod
    def sync_abstract_method(self):
        pass

class TestClassAsyncWrapper(AsyncBase):

    @staticmethod
    def _unblock_methods_to_asynchify():
        methods = [
            "sync_static_method",
            "sync_class_method",
            "sync_method"
        ]
        return methods

class TestClassAsyncPPWrapper(AsyncPPBase):

    def __init__(self, a):
        super().__init__(TestClass(a))
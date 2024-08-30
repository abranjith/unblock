# pylint: disable=E1101

import asyncio
import time
import sys
from typing import Awaitable
from abc import abstractmethod

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


@asyncify
def sync_func(delay) -> Awaitable:
    print(f"started sync_func at {time.strftime('%X')}")
    time.sleep(delay)
    print(f"finished sync_func at {time.strftime('%X')}")
    return "tadaaa!"


async def run_sync_func(delay):
    print(f"starting sync_func at {time.strftime('%X')}")
    f = sync_func(delay)
    print(f"waiting in sync_func {f}", type(f))
    await asyncio.sleep(2)
    print("waiting done in sync_func")
    f.cancel()
    try:
        r = await f
        print(r)
    except asyncio.CancelledError:
        print("sync_func is cancelled now - ", f.cancelled())
    else:
        print("cant cancel sync_func - ", f.cancelled())
    print(f"ending sync_func at {time.strftime('%X')}")


def check_sync_func(delay):
    print(f"starting sync_func at {time.strftime('%X')}")
    f = sync_func(delay)
    print(f"sync_func {f}", type(f))
    print(f"ending sync_func at {time.strftime('%X')}")


def _asyncify_test():
    time.sleep(2)
    print("This is a synch func")


# this uses process pool ..can't use as decorator due to pickling issue
asyncify_test = asyncify_pp(_asyncify_test)


@asyncify
class SampleClsAsyncify:
    @staticmethod
    def static_method():
        print("static_method done")

    @classmethod
    def cls_method(cls):
        print(f"{cls} cls_method done")

    @abstractmethod
    def abs_method(self):
        print("abs_method done")

    def __init__(self, a):
        self.a = a

    @property
    def prop(self):
        time.sleep(2)
        print("prop done")
        return self.a

    @async_property
    def aprop(self):
        time.sleep(2)
        print("aprop done")
        return self.a

    def _private(self, caller=""):
        print(f"_private done. caller - {caller}")

    async def _asleep(self):
        await asyncio.sleep(2)
        print("_asleep done")

    async def async_fun(self):
        self._private("async_fun")
        await asyncio.sleep(2)
        print("async_fun done")

    def sync_fun(self):
        self._private("sync_fun")
        time.sleep(2)
        print("sync_fun done")


class SampleAsyncProperty:
    def __init__(self, a):
        self.a = a

    @async_property
    def prop(self):
        time.sleep(2)
        print("prop done")
        return self.a

    @async_cached_property
    def cached_prop(self):
        time.sleep(2)
        print("cached prop done")
        return self.a


class MyClass:

    @staticmethod
    def static_method():
        print("static_method done")
    
    @classmethod
    def cls_method(cls):
        print(f"cls_method done for {cls}")

    def __init__(self, a):
        self.a = a

    @property
    def prop(self):
        time.sleep(2)
        print("prop done")
        return self.a

    def _private(self, caller=""):
        print(f"_private done. caller - {caller}")

    def sync_fun(self, name):
        self._private(f"sync_fun {name}")
        time.sleep(2)
        print(f"sync_fun {name} done")

    def sync_fun2(self, name):
        self._private(f"sync_fun2 {name}")
        time.sleep(1)
        print(f"sync_fun2 {name} done")


class MyClassAsync(MyClass, AsyncBase):

    @staticmethod
    def _unblock_methods_to_asynchify():
        methods = [
            "sync_fun",
            "static_method",
            "cls_method"
        ]
        return methods


class MyClassAsyncPP(MyClass, AsyncPPBase):

    @staticmethod
    def _unblock_methods_to_asynchify():
        methods = ["sync_fun", "sync_fun2"]
        return methods


class MyCtxMgr:
    def __init__(self, a):
        self.a = a

    def __enter__(self):
        print("Starting MyCtxMgr")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        print("Exiting MyCtxMgr")

    def close(self):
        print("Closing MyCtxMgr")

    def sync_fun(self, name):
        time.sleep(1)
        print(f"sync_fun {name} done")


class MyCtxMgrAsync(MyCtxMgr, AsyncCtxMgrBase):

    def aclose(self):
        print("Closing MyCtxMgrAsync")

    @staticmethod
    def _unblock_methods_to_asynchify():
        methods = ["sync_fun"]
        return methods


class MyCtxMgr2:
    def close(self):
        print("Closing MyCtxMgr2")

    def sync_fun(self, name):
        time.sleep(1)
        print(f"sync_fun {name} done")


class MyCtxMgrAsync2(MyCtxMgr2, AsyncCtxMgrBase):

    async def aclose(self):
        await asyncio.sleep(0)
        print("Closing MyCtxMgrAsync2")


class MyItr:

    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        self.n += 1
        if self.n > 10:
            raise StopIteration("Can't exceed 10!")
        return self.n


class MyItrAsync(MyItr, AsyncIterBase):
    pass

async def test_AsyncClass():
    o = MyClassAsync(100)
    t = o.sync_fun("test")
    time.sleep(3)
    print(o.prop)
    await o.static_method()
    await o.cls_method()
    await MyClassAsync.static_method()
    await MyClassAsync.cls_method()
    await t


async def test_AsyncPPClass():
    o = MyClassAsyncPP(100)
    await o.sync_fun("test")
    await o.sync_fun2("test")


async def test_AsyncCtxMgr():
    async with MyCtxMgrAsync(100) as obj:
        await obj.sync_fun("test")


async def test_AsyncCtxMgr2():
    async with MyCtxMgrAsync2() as obj:
        obj.sync_fun("test")


async def test_AsyncItr():
    async for i in MyItrAsync():
        print(i)


async def test_SampleClsAsyncify():
    await SampleClsAsyncify.static_method()
    t = SampleClsAsyncify(100)
    r = t._asleep()
    await t.async_fun()
    await t.sync_fun()
    await r
    print(t.prop)
    print(await t.aprop)
    await t.cls_method()
    await t.abs_method()


async def test_SampleAsyncProperty():
    t = SampleAsyncProperty(100)
    print(await t.prop)
    print(await t.cached_prop)
    t.a = 200
    print(await t.prop)
    print(await t.cached_prop)


if __name__ == "__main__":
    # asyncio.run(run_sync_func(1))  # not cancelled
    # asyncio.run(run_sync_func(3))   # cancelled
    # check_sync_func(1)  # creates coroutine -- not awaited!
    # asyncio.run(test_SampleAsyncProperty())    # asyncify properties
    # asyncio.run(test_SampleClsAsyncify())   # asyncify
    # asyncio.run(test_AsyncClass())   # asyncify class
    # asyncio.run(test_AsyncPPClass())   # asyncify class PP
    # asyncio.run(test_AsyncItr())   # asyncify iterator
    # asyncio.run(test_AsyncCtxMgr())  # asyncify ctx mgr
    asyncio.run(test_AsyncCtxMgr2())  # asyncify ctx mgr2

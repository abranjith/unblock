# pylint: disable=E1101

import asyncio
import time
import sys
from typing import Awaitable
sys.path.append("..\\unblock")
from unblock import (
    asyncify_pp,
    asyncify,
    async_cached_property,
    async_property,
    AsyncBase
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

#this uses process pool ..can't use as decorator due to pickling issue
asyncify_test = asyncify_pp(_asyncify_test)


@asyncify
class SampleClsAsyncify:
        
    @staticmethod
    def static_method():
        print("static_method done")

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

    def _private(self, caller = ""):
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

    def __init__(self, a):
        self.a = a

    @property
    def prop(self):
        time.sleep(2)
        print("prop done")
        return self.a
    
    def _private(self, caller = ""):
        print(f"_private done. caller - {caller}")

    def sync_fun(self, name):
        self._private(f"sync_fun {name}")
        time.sleep(2)
        print(f"sync_fun {name} done")

class SampleUnblock(AsyncBase):

    def __init__(self, a):
        super().__init__(MyClass(a))

    def _unblock_attrs_to_asynchify(self):
        methods = [
            #"prop",    
            "sync_fun"
        ]
        return methods
    
async def test_Unblock():
    o = SampleUnblock(100)
    t = o.sync_fun("test")
    time.sleep(3)
    print(o.prop)
    await t

async def test_SampleClsAsyncify():
    await SampleClsAsyncify.static_method()
    t = SampleClsAsyncify(100)
    r = t._asleep()
    await t.async_fun()
    await t.sync_fun()
    await r
    print(t.prop)
    print(await t.aprop)
    
async def test_SampleAsyncProperty():
    t = SampleAsyncProperty(100)
    print(await t.prop)
    print(await t.cached_prop)
    t.a = 200
    print(await t.prop)
    print(await t.cached_prop)


if __name__ == "__main__":
    #asyncio.run(run_sync_func(1))  # not cancelled
    #asyncio.run(run_sync_func(3))   #cancelled
    #check_sync_func(1)  #creates coroutine
    #asyncio.run(test_SampleAsyncProperty())
    #asyncio.run(test_SampleClsAsyncify())   #asyncify
    asyncio.run(test_Unblock())   #asyncify

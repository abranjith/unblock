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
    async_property
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
class SampelClsAsyncify:
    def __init__(self, a):
        self.a = a

    @async_property
    def prop(self):
        time.sleep(2)
        print("prop done")
        return self.a

    def _private(self):
        print("_private done")

    async def _asleep(self):
        await asyncio.sleep(2)
        print("_asleep done")

    async def async_fun(self):
        self._private()
        await asyncio.sleep(2)
        print("async_fun done")

    def sync_fun(self):
        self._private()
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

async def test_SampelClsAsyncify():
    t = SampelClsAsyncify(100)
    r = t._asleep()
    await t.async_fun()
    await t.sync_fun()
    await r

async def test_SampleAsyncProperty():
    t = SampleAsyncProperty(100)
    print(await t.prop)
    print(await t.cached_prop)
    t.a = 200
    print(await t.prop)
    print(await t.cached_prop)


if __name__ == "__main__":
    #asyncio.run(run_sync_func(1))  # not cancelled
    asyncio.run(run_sync_func(3))   #cancelled
    #check_sync_func(1)  #creates coroutine
    #asyncio.run(test_SampleAsyncProperty())

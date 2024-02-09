from functools import wraps
import fileinput as fileinput_sync
from .core import asyncify_func, AsyncCtxMgrIterBase


class _AsyncCtxIterBase(AsyncCtxMgrIterBase):
    async def __anext__(self):
        line = await self.readline()
        if line:
            return line
        raise StopAsyncIteration


class AsyncFileInput(_AsyncCtxIterBase):

    def _unblock_attrs_to_asynchify(self):
        methods = ["close", "__getitem__", "__del__", "nextfile", "readline"]
        return methods


@wraps(fileinput_sync.input)
async def input(*args, **kwargs):
    f = await asyncify_func(fileinput_sync.input)(*args, **kwargs)
    return AsyncFileInput(f)


hook_compressed = asyncify_func(fileinput_sync.hook_compressed)
hook_encoded = asyncify_func(fileinput_sync.hook_encoded)

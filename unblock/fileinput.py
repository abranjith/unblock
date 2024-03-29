from functools import wraps
import fileinput as fileinput_sync
from .core import asyncify_func, AsyncBase, AsyncCtxMgrIterBase


class _AsyncCtxIterBase(AsyncCtxMgrIterBase):
    async def __anext__(self):
        line = await self.readline()
        if line:
            return line
        else:
            raise StopAsyncIteration


class AsyncFileInput(_AsyncCtxIterBase):
    @property
    def _unblock_attrs_to_asynchify(self):
        methods = ["close", "__getitem__", "__del__", "nextfile", "readline", "fileno"]
        return methods


@wraps(fileinput_sync.input)
async def input(*args, **kwargs):
    f = await asyncify_func(fileinput_sync.input)(*args, **kwargs)
    file_obj = AsyncFileInput(f)
    return file_obj


hook_compressed = asyncify_func(fileinput_sync.hook_compressed)
hook_encoded = asyncify_func(fileinput_sync.hook_encoded)

from functools import wraps
import fileinput as fileinput_sync
from .core import asyncify_func, AsyncBase

class _AsyncIterMixin(object):

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    async def __aiter__(self):
        return self

    async def __anext__(self):
        line = await self.readline()
        if line:
            return line
        else:
            raise StopAsyncIteration

class _AsyncIterBase(AsyncBase, _AsyncIterMixin):
    pass

class AsyncFileInput(_AsyncIterBase):

    @property
    def _attrs_to_asynchify(self):
        methods = ["close", "__getitem__", "__del__", "nextfile", "readline", "fileno"]
        return methods

@wraps(fileinput_sync.input)
async def input(*args, **kwargs):
    f = await asyncify_func(fileinput_sync.input)(*args, **kwargs)
    file_obj = AsyncFileInput(f)
    return file_obj

hook_compressed = asyncify_func(fileinput_sync.hook_compressed)
hook_encoded = asyncify_func(fileinput_sync.hook_encoded)

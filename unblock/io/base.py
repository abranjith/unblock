from ..core import asyncify, AsyncBase

class _AsyncIterMixin(object):

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    def __aiter__(self):
        return self

    async def __anext__(self):
        line = await self.readline()
        if line:
            return line
        else:
            raise StopAsyncIteration

class _AsyncIterBase(AsyncBase, _AsyncIterMixin):
    pass

class AsyncIOBase(_AsyncIterBase):

    @property
    def __attrs_to_asynchify(self):
        methods = ["close", "fileno", "flush", "isatty", "readable", "readline", "readlines", "seek", "seekable", "tell",
                            "truncate", "writable", "writelines"]
        return methods

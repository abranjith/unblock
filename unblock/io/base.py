from ..core import asyncify, AsyncBase, AsyncCtxMgrIterBase

class _AsyncCtxIterBase(AsyncCtxMgrIterBase):

    def __aiter__(self):
        return self

    async def __anext__(self):
        line = await self.readline()
        if line:
            return line
        else:
            raise StopAsyncIteration

class AsyncIOBase(_AsyncCtxIterBase):

    @property
    def _attrs_to_asynchify(self):
        methods = ["close", "fileno", "flush", "isatty", "readable", "readline", "readlines", "seek", "seekable", "tell",
                            "truncate", "writable", "writelines"]
        return methods

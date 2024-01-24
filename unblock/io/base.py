from ..core import AsyncCtxMgrIterBase


class _AsyncCtxIterBase(AsyncCtxMgrIterBase):
    def __aiter__(self):
        return self

    async def __anext__(self):
        line = await self.readline()
        if line:
            return line
        raise StopAsyncIteration


class AsyncIOBase(_AsyncCtxIterBase):
    @property
    def _unblock_attrs_to_asynchify(self):
        methods = [
            "close",
            "fileno",
            "flush",
            "isatty",
            "readable",
            "readline",
            "readlines",
            "seek",
            "seekable",
            "tell",
            "truncate",
            "writable",
            "writelines",
        ]
        return methods

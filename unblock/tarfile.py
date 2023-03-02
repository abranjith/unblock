from functools import wraps
import tarfile as tarfile_sync
from .core import asyncify_func, AsyncBase, AsyncIterBase


class _AsyncCtxIterBase(AsyncIterBase):
    async def __aexit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            await self.close()
        else:
            # An exception occurred. We must not call close() because
            # it would try to write end-of-archive blocks and padding.
            if not self._extfileobj:
                await asyncify_func(self.fileobj.close)()
            self.closed = True

    # see more re: use of synchronous iterator as coroutine here - https://bugs.python.org/issue26221
    async def __anext__(self):
        def _next():
            try:
                return next(self._itrtr)
            except StopIteration:
                raise StopAsyncIteration

        return await asyncify_func(_next)()


class AsyncTarInfo(AsyncBase):
    def __init__(self, *args, **kwargs):
        self._original_obj = tarfile_sync.TarInfo(*args, **kwargs)

    fromtarfile = asyncify_func(tarfile_sync.TarInfo.fromtarfile)


class AsyncTarFile(_AsyncCtxIterBase):
    @classmethod
    async def create(cls, *args, **kwargs):
        return await asyncify_func(create_tar_file)(*args, **kwargs)

    @classmethod
    async def open(cls, *args, **kwargs):
        f = await asyncify_func(tarfile_sync.TarFile.open)(*args, **kwargs)
        return cls(f)

    @classmethod
    async def taropen(cls, *args, **kwargs):
        f = await asyncify_func(tarfile_sync.TarFile.taropen)(*args, **kwargs)
        return cls(f)

    @classmethod
    async def gzopen(cls, *args, **kwargs):
        f = await asyncify_func(tarfile_sync.TarFile.gzopen)(*args, **kwargs)
        return cls(f)

    @classmethod
    async def bz2open(cls, *args, **kwargs):
        f = await asyncify_func(tarfile_sync.TarFile.bz2open)(*args, **kwargs)
        return cls(f)

    @classmethod
    async def xzopen(cls, *args, **kwargs):
        f = await asyncify_func(tarfile_sync.TarFile.xzopen)(*args, **kwargs)
        return cls(f)

    @property
    def _unblock_attrs_to_asynchify(self):
        methods = [
            "close",
            "getmember",
            "getmembers",
            "getnames",
            "gettarinfo",
            "add",
            "addfile",
            "extractall",
            "extract",
            "extractfile",
            "makedir",
            "makefile",
            "makeunknown",
            "makefifo",
            "makedev",
            "makelink",
            "chown",
            "chmod",
            "utime",
            "next",
        ]
        return methods


@wraps(tarfile_sync.open)
async def aopen(*args, **kwargs):
    f = await asyncify_func(tarfile_sync.open)(*args, **kwargs)
    return AsyncTarFile(f)


def create_tar_file(*args, **kwrgs):
    return tarfile_sync.TarFile(*args, **kwrgs)


is_tarfile = asyncify_func(tarfile_sync.is_tarfile)
copyfileobj = asyncify_func(tarfile_sync.copyfileobj)

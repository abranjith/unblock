from functools import singledispatch, wraps
import zipfile as zipfile_sync
from .core import asyncify_func, AsyncBase, AsyncCtxMgrBase
from .io.binary import AsyncBufferedIOBase


class AsyncZipInfo(AsyncBase):
    def __init__(self, *args, **kwargs):
        if(args and isinstance(args[0], zipfile_sync.ZipInfo)):
            super().__init__(args[0])
        else:
            self._original_obj = zipfile_sync.ZipInfo(*args, **kwargs)

    from_file = asyncify_func(zipfile_sync.ZipInfo.from_file)


class _AsyncZipWriteFile(AsyncBufferedIOBase):
    """Implements write and close from parent class"""


class AsyncZipExtFile(AsyncBufferedIOBase):
    @property
    def _unblock_attrs_to_asynchify(self):
        methods = super()._unblock_attrs_to_asynchify + ["peek"]
        return methods


class AsyncZipFile(AsyncCtxMgrBase):
    @classmethod
    async def create(cls, *args, **kwargs):
        f = await asyncify_func(_zipfile)(*args, **kwargs)
        return AsyncZipFile(f)

    @property
    def _unblock_attrs_to_asynchify(self):
        methods = [
            "close",
            "getinfo",
            "testzip",
            "read",
            "extract",
            "extractall",
            "write",
            "writestr",
            "namelist",
        ]
        return methods

    @wraps(zipfile_sync.ZipFile.open)
    async def open(self, *args, **kwargs):
        f = await asyncify_func(self._original_obj.open)(*args, **kwargs)
        file_obj = zip_wrap(f)
        return file_obj
    
    @wraps(zipfile_sync.ZipFile.infolist)
    async def infolist(self, *args, **kwargs):
        zipinfos = await asyncify_func(self._original_obj.infolist)(*args, **kwargs)
        return [AsyncZipInfo(f) for f in zipinfos]


class AsyncPyZipFile(AsyncZipFile):
    @property
    def _unblock_attrs_to_asynchify(self):
        methods = super()._unblock_attrs_to_asynchify + ["writepy"]
        return methods


class AsyncLZMACompressor(AsyncBase):
    def __init__(self, *args, **kwargs):
        self._original_obj = zipfile_sync.LZMACompressor(*args, **kwargs)

    @property
    def _unblock_attrs_to_asynchify(self):
        methods = ["compress", "flush"]
        return methods


class AsyncLZMADecompressor(AsyncBase):
    def __init__(self, *args, **kwargs):
        self._original_obj = zipfile_sync.LZMADecompressor(*args, **kwargs)

    @property
    def _unblock_attrs_to_asynchify(self):
        methods = ["decompress"]
        return methods


@singledispatch
def zip_wrap(file_object):
    raise TypeError(f"Unsupported io type: {file_object}.")


@zip_wrap.register(zipfile_sync.ZipExtFile)
def _(file_object):
    return AsyncZipExtFile(file_object)


@zip_wrap.register(zipfile_sync._ZipWriteFile)
def _(file_object):
    return _AsyncZipWriteFile(file_object)


def _zipfile(*args, **kwargs):
    return zipfile_sync.ZipFile(*args, **kwargs)


is_zipfile = asyncify_func(zipfile_sync.is_zipfile)

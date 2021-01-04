from functools import singledispatch, wraps
import zipfile as zipfile_sync
from .core import asyncify_func, AsyncBase, AsyncCtxMgrBase
from .io.binary import AsyncBufferedIOBase

class AsyncZipInfo(AsyncBase):

    def __init__(self, *args, **kwargs):
        self._original_obj = zipfile_sync.ZipInfo(*args, **kwargs)
    
    from_file = asyncify_func(zipfile_sync.ZipInfo.from_file)

class _AsyncZipWriteFile(AsyncBufferedIOBase):
    """Implements write and close from parent class"""

class AsyncZipExtFile(AsyncBufferedIOBase):
    
    @property
    def _attrs_to_asynchify(self):
        methods = super()._attrs_to_asynchify + ["peek"]
        return methods

class AsyncZipFile(AsyncCtxMgrBase):

    @classmethod
    async def create(cls, *args, **kwargs):
        return await aopen(*args, **kwargs)
    
    @property
    def _attrs_to_asynchify(self):
        methods = ["close", "getinfo", "testzip", "read", "extract", "extractall", "write", "writestr", "infolist", "namelist" ]
        return methods

    async def open(self, *args, **kwargs):
        f = await asyncify_func(zipfile_sync.open)(*args, **kwargs)
        file_obj = zip_wrap(f)
        return file_obj

@singledispatch
def zip_wrap(file_object):
    raise TypeError(f"Unsupported io type: {file_object}.")

@zip_wrap.register(zipfile_sync.ZipExtFile)
def _(file_object):
    return AsyncZipExtFile(file_object)

@zip_wrap.register(zipfile_sync._ZipWriteFile)
def _(file_object):
    return _AsyncZipWriteFile(file_object)

def _open(*args, **kwargs):
    return zipfile_sync.ZipFile(*args, **kwargs)

async def aopen(*args, **kwargs):
    f = await asyncify_func(_open)(*args, **kwargs)
    return AsyncZipFile(f)

is_zipfile = asyncify_func(zipfile_sync.is_zipfile)

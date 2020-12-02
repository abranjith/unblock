from functools import singledispatch
import zipfile as zipfile_sync
from .core import asyncify_func_x, AsyncXBase
from .io.binary import AsyncBufferedIOBase

class _AsyncCtxBase(AsyncXBase):

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

class AsyncZipInfo(AsyncXBase):

    def __init__(self, *args, **kwargs):
        self._original_obj = zipfile_sync.ZipInfo(*args, **kwargs)
    
    from_file = asyncify_func_x(zipfile_sync.ZipInfo.from_file)

class _AsyncZipWriteFile(AsyncBufferedIOBase):
    """Implements write and close from parent class"""

class AsyncZipExtFile(AsyncBufferedIOBase):
    
    @property
    def __attrs_to_asynchify(self):
        methods = super().__attrs_to_asynchify + ["peek"]
        return methods

class AsyncZipFile(_AsyncCtxBase):

    @classmethod
    async def create(cls, *args, **kwargs):
        return await aopen(*args, **kwargs)
    
    @property
    def __attrs_to_asynchify(self):
        methods = ["close", "getinfo", "testzip", "read", "extract", "extractall", "write", "writestr" ]
        return methods

    async def open(self, *args, **kwargs):
        f = await asyncify_func_x(zipfile_sync.open)(*args, **kwargs)
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

#recomended to use this instead of _AsyncZipFile
async def aopen(*args, **kwargs):
    f = await asyncify_func_x(_open)(*args, **kwargs)
    return AsyncZipFile(f)

is_zipfile = asyncify_func_x(zipfile_sync.is_zipfile)
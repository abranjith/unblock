from functools import singledispatch, wraps
from io import TextIOWrapper
import lzma as lzma_sync
from .core import asyncify_func, asyncify_func_x, AsyncXBase
from .io.text import AsyncTextIOWrapper
from .io.binary import AsyncBufferedIOBase

class AsyncLZMACompressor(AsyncXBase):

    def __init__(self, *args, **kwargs):
        self._original_obj = lzma_sync.LZMACompressor(*args, **kwargs)

    @property
    def __attrs_to_asynchify(self):
        methods = ["compress", "flush"]
        return methods

class AsyncLZMADecompressor(AsyncXBase):

    def __init__(self, *args, **kwargs):
        self._original_obj = lzma_sync.LZMADecompressor(*args, **kwargs)

    @property
    def __attrs_to_asynchify(self):
        methods = ["decompress"]
        return methods

class AsyncLZMAFile(AsyncBufferedIOBase):

    @property
    def __attrs_to_asynchify(self):
        methods = super().__attrs_to_asynchify + ["peek"]
        return methods

@wraps(lzma_sync.open)
async def aopen(*args, **kwargs):
    f = await asyncify_func(lzma_sync.open)(*args, **kwargs)
    file_obj = wrap(f)
    return file_obj

@singledispatch
def wrap(file_object):
    raise TypeError(f"Unsupported io type: {file_object}.")

@wrap.register(TextIOWrapper)
def _(file_object):
    return AsyncTextIOWrapper(file_object)

@wrap.register(lzma_sync.LZMAFile)
def _(file_object):
    return AsyncLZMAFile(file_object)

compress = asyncify_func_x(lzma_sync.compress)
decompress = asyncify_func_x(lzma_sync.decompress)
is_check_supported = lzma_sync.is_check_supported
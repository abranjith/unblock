from functools import wraps, singledispatch
from io import TextIOWrapper
import bz2 as bz2_sync
from .core import asyncify_func, AsyncBase
from .io.text import AsyncTextIOWrapper
from .io.binary import AsyncBufferedIOBase


class AsyncBZ2Compressor(AsyncBase):
    def __init__(self, *args, **kwargs):
        self._original_obj = bz2_sync.BZ2Compressor(*args, **kwargs)

    @property
    def _attrs_to_asynchify(self):
        methods = ["compress", "flush"]
        return methods


class AsyncBZ2Decompressor(AsyncBase):
    def __init__(self, *args, **kwargs):
        self._original_obj = bz2_sync.BZ2Decompressor(*args, **kwargs)

    @property
    def _attrs_to_asynchify(self):
        methods = ["decompress"]
        return methods


class AsyncBZ2File(AsyncBufferedIOBase):
    @property
    def _attrs_to_asynchify(self):
        methods = super()._attrs_to_asynchify + ["peek"]
        return methods


@wraps(bz2_sync.open)
async def aopen(*args, **kwargs):
    f = await asyncify_func(bz2_sync.open)(*args, **kwargs)
    file_obj = wrap(f)
    return file_obj


@singledispatch
def wrap(file_object):
    raise TypeError(f"Unsupported io type: {file_object}.")


@wrap.register(TextIOWrapper)
def _(file_object):
    return AsyncTextIOWrapper(file_object)


@wrap.register(bz2_sync.BZ2File)
def _(file_object):
    return AsyncBZ2File(file_object)


compress = asyncify_func(bz2_sync.compress)
decompress = asyncify_func(bz2_sync.decompress)

from functools import singledispatch, wraps
from io import TextIOWrapper
import gzip as gzip_sync
from .core import asyncify_func
from .io.text import AsyncTextIOWrapper
from .io.binary import AsyncBufferedIOBase


class AsyncGzipFile(AsyncBufferedIOBase):
    
    def _unblock_attrs_to_asynchify(self):
        methods = super()._unblock_attrs_to_asynchify() + ["peek"]
        return methods


@wraps(gzip_sync.open)
async def aopen(*args, **kwargs):
    f = await asyncify_func(gzip_sync.open)(*args, **kwargs)
    file_obj = wrap(f)
    return file_obj


@singledispatch
def wrap(file_object):
    raise TypeError(f"Unsupported io type: {file_object}.")


@wrap.register(TextIOWrapper)
def _(file_object):
    return AsyncTextIOWrapper(file_object)


@wrap.register(gzip_sync.GzipFile)
def _(file_object):
    return AsyncGzipFile(file_object)


compress = asyncify_func(gzip_sync.compress)
decompress = asyncify_func(gzip_sync.decompress)

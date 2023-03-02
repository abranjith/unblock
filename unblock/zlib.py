from functools import wraps
import zlib as zlib_sync
from .core import asyncify_func, AsyncBase


class AsyncCompress(AsyncBase):
    @property
    def _unblock_attrs_to_asynchify(self):
        methods = ["compress", "flush", "copy"]
        return methods


class AsyncDecompress(AsyncBase):
    @property
    def _unblock_attrs_to_asynchify(self):
        methods = ["decompress", "flush", "copy"]
        return methods


adler32 = asyncify_func(zlib_sync.adler32)
crc32 = asyncify_func(zlib_sync.crc32)
compress = asyncify_func(zlib_sync.compress)
decompress = asyncify_func(zlib_sync.decompress)


@wraps(zlib_sync.compressobj)
def compressobj(*args, **kwargs):
    rv = zlib_sync.compressobj(*args, **kwargs)
    return AsyncCompress(rv)


@wraps(zlib_sync.decompressobj)
def decompressobj(*args, **kwargs):
    rv = zlib_sync.decompressobj(*args, **kwargs)
    return AsyncDecompress(rv)

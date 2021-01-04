from functools import wraps, singledispatch
from io import (FileIO, TextIOWrapper, BufferedReader, BufferedWriter, BufferedRandom)
from .raw import AsyncFileIO
from .binary import AsyncBufferedReader, AsyncBufferedWriter, AsyncBufferedRandom
from .text import AsyncTextIOWrapper
from ..core import asyncify_func

@wraps(open)
async def aopen(*args, **kwargs):
    f = await asyncify_func(open)(*args, **kwargs)
    file_obj = wrap(f)
    return file_obj

@singledispatch
def wrap(file_object):
    raise TypeError(f"Unsupported io type: {file_object}.")

@wrap.register(TextIOWrapper)
def _(file_object):
    return AsyncTextIOWrapper(file_object)

@wrap.register(BufferedReader)
def _(file_object):
    return AsyncBufferedReader(file_object)

@wrap.register(BufferedWriter)
def _(file_object):
    return AsyncBufferedWriter(file_object)

@wrap.register(BufferedRandom)
def _(file_object):
    return AsyncBufferedRandom(file_object)

@wrap.register(FileIO)
def _(file_object):
    return AsyncFileIO(file_object)

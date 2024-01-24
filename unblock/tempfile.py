from functools import singledispatch
from io import FileIO, TextIOWrapper, BufferedReader, BufferedWriter, BufferedRandom
import tempfile as tempfile_sync
from unblock.io.raw import AsyncFileIO
from unblock.io.binary import AsyncBufferedReader, AsyncBufferedWriter, AsyncBufferedRandom
from unblock.io.text import AsyncTextIOWrapper


def AsyncTemporaryFile(*args, **kwargs):
    tf = tempfile_sync.TemporaryFile(*args, **kwargs)
    return wrap(tf.file)

def AsyncNamedTemporaryFile(*args, **kwargs):
    tf = tempfile_sync.NamedTemporaryFile(*args, **kwargs)
    return wrap(tf.file)

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

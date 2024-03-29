from .base import AsyncIOBase


class AsyncBufferedIOBase(AsyncIOBase):
    @property
    def _unblock_attrs_to_asynchify(self):
        methods = super()._unblock_attrs_to_asynchify + [
            "detach",
            "read",
            "read1",
            "readinto",
            "readinto1",
            "write",
        ]
        return methods


class AsyncBytesIO(AsyncBufferedIOBase):
    pass


class AsyncBufferedReader(AsyncBufferedIOBase):
    @property
    def _unblock_attrs_to_asynchify(self):
        methods = super()._unblock_attrs_to_asynchify + ["peek"]
        return methods


class AsyncBufferedWriter(AsyncBufferedIOBase):
    @property
    def _unblock_attrs_to_asynchify(self):
        methods = super()._unblock_attrs_to_asynchify + ["flush"]
        return methods


class AsyncBufferedRandom(AsyncBufferedIOBase):
    @property
    def _unblock_attrs_to_asynchify(self):
        methods = super()._unblock_attrs_to_asynchify + ["peek", "flush"]
        return methods


class AsyncBufferedRWPair(AsyncBufferedIOBase):
    pass

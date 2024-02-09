from .base import AsyncIOBase


class AsyncRawIOBase(AsyncIOBase):

    def _unblock_attrs_to_asynchify(self):
        methods = super()._unblock_attrs_to_asynchify() + [
            "read",
            "readall",
            "readinto",
            "write",
        ]
        return methods


class AsyncFileIO(AsyncRawIOBase):
    pass

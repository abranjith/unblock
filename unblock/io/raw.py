from .base import AsyncIOBase

class AsyncRawIOBase(AsyncIOBase):

    @property
    def __attrs_to_asynchify(self):
        methods = super().__attrs_to_asynchify + ["read", "readall", "readinto", "write"]
        return methods


class AsyncFileIO(AsyncRawIOBase):
    pass
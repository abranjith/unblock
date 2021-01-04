from .base import AsyncIOBase

class AsyncRawIOBase(AsyncIOBase):

    @property
    def _attrs_to_asynchify(self):
        methods = super()._attrs_to_asynchify + ["read", "readall", "readinto", "write"]
        return methods


class AsyncFileIO(AsyncRawIOBase):
    pass

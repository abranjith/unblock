from .base import AsyncIOBase

class AsyncTextIOBase(AsyncIOBase):

    @property
    def __attrs_to_asynchify(self):
        methods = super().__attrs_to_asynchify + ["detach","read", "readline", "write"]
        return methods

class AsyncTextIOWrapper(AsyncTextIOBase):

    @property
    def __attrs_to_asynchify(self):
        methods = super().__attrs_to_asynchify + ["reconfigure"]
        return methods

class AsyncStringIO(AsyncTextIOBase):
    pass
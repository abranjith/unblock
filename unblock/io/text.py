from .base import AsyncIOBase


class AsyncTextIOBase(AsyncIOBase):

    def _unblock_attrs_to_asynchify(self):
        methods = super()._unblock_attrs_to_asynchify() + [
            "detach",
            "read",
            "readline",
            "write",
        ]
        return methods


class AsyncTextIOWrapper(AsyncTextIOBase):

    def _unblock_attrs_to_asynchify(self):
        methods = super()._unblock_attrs_to_asynchify() + ["reconfigure"]
        return methods


class AsyncStringIO(AsyncTextIOBase):
    pass

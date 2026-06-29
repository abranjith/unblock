"""Exception types raised by :mod:`unblock`."""

from __future__ import annotations

__all__ = ["UnblockError"]


class UnblockError(Exception):
    """Raised when ``unblock`` is misused or cannot honour a request.

    Common situations:

    * :func:`unblock.asyncify` is given something it cannot convert (not a
      function, method, or class).
    * An invalid executor is supplied to the configuration helpers or to the
      ``executor`` argument (anything other than ``"thread"``, ``"process"``,
      or a :class:`concurrent.futures.Executor` instance).
    * A callable that cannot be pickled (a closure, lambda, or locally defined
      function) is asyncified for the process pool.
    * An executor is requested after :func:`unblock.shutdown` has been called.
    """

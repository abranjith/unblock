"""Module-level, importable targets for process-pool tests.

Process-pool tests must reference callables that pickle by qualified name, so
these live in an importable module rather than being defined inside a test
function (which would put ``<locals>`` in their qualname and make them
unpicklable).
"""

from __future__ import annotations

import os

from unblock import asyncify


def plain_double(x: int) -> int:
    return x * 2


@asyncify(executor="process")
def decorated_double(x: int) -> int:
    return x * 2


@asyncify(executor="process")
def returns_pid() -> int:
    return os.getpid()


@asyncify(executor="process")
def raises_in_worker() -> None:
    raise ValueError("worker boom")

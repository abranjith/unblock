"""Public configuration and lifecycle helpers for :mod:`unblock`.

These let you supply your own executors and shut the library down cleanly. The
defaults are created lazily and torn down automatically at interpreter exit, so
most programs never need to call any of these.
"""

from __future__ import annotations

from ._executors import set_process_pool, set_thread_pool, shutdown

__all__ = ["set_thread_pool", "set_process_pool", "shutdown"]

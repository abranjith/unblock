# unblock

unblock provides small utilities that convert synchronous functions, methods,
and classes into asynchronous ones for use inside an asyncio event loop. It
offloads blocking work to a thread or process pool so it does not block the loop.

For full documentation, see https://unblock.readthedocs.io/en/latest/

Install (distribution name is `get-unblock`, import name is `unblock`):

```
pip install get-unblock
```

Quick example:

```python
import asyncio
from unblock import asyncify


@asyncify
def my_sync_func():
    ...  # do something blocking


if __name__ == "__main__":
    asyncio.run(my_sync_func())
```

Run on a process pool instead of threads:

```python
@asyncify(executor="process")
def cpu_bound(n):
    return sum(i * i for i in range(n))
```

## Development

Requires Python 3.10+.

```
python -m venv .venv
. .venv/Scripts/activate        # or: source .venv/bin/activate
pip install -e ".[dev]"

ruff check .
ruff format --check .
mypy
pytest --cov=unblock --cov-branch
```

## Release Notes

**0.1.0**

A ground-up refactor of the library. There is no compatibility with `0.0.1`.

* One unified `asyncify` entry point for functions, methods, and classes, with an
  `executor` parameter (`"thread"`, `"process"`, or an `Executor` instance).
  `@asyncify(executor="process")` now works as a decorator on importable
  functions.
* A single executor-configurable mixin family (`AsyncMixin`, `AsyncIterMixin`,
  `AsyncContextMixin`, `AsyncContextIterMixin`) replaces the previous eight base
  classes; method names no longer need to be listed as strings.
* `async_property` and `async_cached_property` redesigned as proper descriptors;
  the cached variant now computes exactly once even under concurrent awaits.
* Work always binds to the running event loop (fixes cross-loop errors); the
  return-type duality (started future when a loop runs, coroutine otherwise) is
  documented.
* Thread/process pools are bounded, created thread-safely, and shut down cleanly
  via `shutdown()` and an `atexit` hook.
* Asynchronous tasks still start in the background when a loop is running; you
  `await` only to collect the result.
* Works with asyncio-compatible event loops (asyncio, uvloop). It does not
  support trio/curio, which are not asyncio compatible natively.
* Ships type information (PEP 561). Supports Python 3.10 and above.
```

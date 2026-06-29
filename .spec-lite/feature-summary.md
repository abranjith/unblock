<!-- Maintained by spec-lite | updated by: implement, fix skills -->

# Feature Summary

> **Current state only.** This document reflects what each feature does *right now* — not what it used to do.
> Maintained by the Implement and Fix skills after every code change that affects feature behavior.
> For change history, use source control (e.g., git).

---

## Conversion API

**asyncify (functions and methods)** *(updated: 2026-06-28 by implement)*
Source spec: [feature_function_asyncification.md](.spec-lite/features/feature_function_asyncification.md)
`asyncify` is the single converter for callables. It works as a bare decorator (`@asyncify`), a parameterized decorator (`@asyncify(executor="process")`), or a direct call (`asyncify(fn)`). `executor` selects `"thread"` (default), `"process"`, or a supplied `concurrent.futures.Executor`. When a loop is running an asyncified call returns a started future; with no loop it returns a coroutine that starts when awaited. Already-async functions are returned unchanged; non-callable/non-class inputs raise `UnblockError`. The process-pool form works as a decorator on any importable function (via a re-resolving trampoline); closures, lambdas, and locally-defined functions are rejected at decoration time with a clear `UnblockError`. Cancelling the returned awaitable cannot force-stop work already running in a thread or process.

**asyncify (classes and protocols)** *(updated: 2026-06-28 by implement)*
Source spec: [feature_class_asyncification.md](.spec-lite/features/feature_class_asyncification.md)
Applying `@asyncify` to a class converts its public synchronous instance methods in place (skipping dunder, private, static, class, and already-async methods). `include=[...]` and `exclude=[...]` control the selection (mutually exclusive; invalid names raise `UnblockError`). Wrapping happens once at class-definition time. The decorator also auto-detects the iterator and context-manager protocols and adds async equivalents; the synchronous `__enter__`/`__exit__` run on the executor (not the event loop). For wrapping a class without editing it, the mixin family `AsyncMixin`, `AsyncIterMixin`, `AsyncContextMixin`, `AsyncContextIterMixin` provides the same behavior with the executor chosen by class keyword (`class W(Base, AsyncMixin, executor="process")`). On context exit: `__exit__` runs first; then if `call_close_on_exit` is true a zero-arg `aclose` (sync or async) is awaited, else a zero-arg `close` is offloaded when there was no `__exit__`.

**Async properties** *(updated: 2026-06-28 by implement)*
Source spec: [feature_async_properties.md](.spec-lite/features/feature_async_properties.md)
`async_property` runs a getter off the event loop and is awaited at the access site (`await obj.prop`); it reflects current state on every read. `async_cached_property` computes the value exactly once per instance — even under concurrent awaits (a per-instance lock serializes the first computation) — and caches it on the instance; assigning to the attribute overrides the cache and `del` clears it. Both accept an `executor` argument, return the descriptor on class access, and raise `AttributeError` when no getter is bound.

---

## Runtime and configuration

**Execution core and executor lifecycle** *(updated: 2026-06-28 by implement)*
Source spec: [feature_execution_core.md](.spec-lite/features/feature_execution_core.md)
All conversions funnel through one scheduler that binds work to the event loop actually running at execution time (which removes cross-loop errors) and implements the started-future-vs-coroutine return duality. Default thread and process pools are bounded, created lazily in a thread-safe way, and shut down automatically at interpreter exit. `set_thread_pool` and `set_process_pool` replace the defaults (validating the executor type), and `shutdown()` releases the pools (idempotent; after it, default pools are recreated only once a new pool is supplied). Diagnostics are emitted on the `unblock` logger (with a `NullHandler`); the library prints nothing. Misuse and invalid configuration raise `UnblockError`.

---

## Project infrastructure

**Packaging, typing, and tooling** *(updated: 2026-06-28 by implement)*
Source spec: [feature_packaging_tooling.md](.spec-lite/features/feature_packaging_tooling.md)
Single-source packaging via `pyproject.toml` (hatchling), `requires-python >= 3.10`, corrected license/classifiers, and `dev`/`test`/`docs` optional-dependency groups. Ships a `py.typed` marker (PEP 561). Ruff (lint + format) and mypy (strict) are configured and pass. A GitHub Actions workflow runs lint, type-check, and the test suite across Python 3.10-3.13 on Linux and Windows with the coverage gate. Distribution name is `get-unblock`; import name is `unblock`.

**Test suite** *(updated: 2026-06-28 by implement)*
Source spec: [feature_test_suite.md](.spec-lite/features/feature_test_suite.md)
pytest + pytest-asyncio suite discovered by default (`test_*.py`), with an autouse fixture that resets executor state between tests for isolation. Coverage is enforced at 95% (branch coverage); current coverage is ~99%. Covers the return-type duality, the cross-loop regression, exception propagation, cancellation semantics, the process-pool trampoline and fail-fast picklability checks, class include/exclude and protocol detection, non-blocking enter/exit, compute-once cached properties, and executor lifecycle.

**Documentation** *(updated: 2026-06-28 by implement)*
Source spec: [feature_documentation.md](.spec-lite/features/feature_documentation.md)
Sphinx/rst docs on Read the Docs: features, basic usage, API, caveats, and a migration guide, plus an autodoc/napoleon-generated API reference. The docs build cleanly with warnings treated as errors. The previous incorrect "works with any event loop" claim is corrected (asyncio-compatible loops only; no trio/curio).

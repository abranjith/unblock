# TODO — tracked enhancements (out of current plan scope)

## General

- [ ] First-class trio/anyio support layer — the current docs claim "compatible with any event loop" is false; `run_in_executor` requires an asyncio-compatible loop (asyncio, uvloop). True trio/curio support needs a separate adapter. (discovered during: planning)
- [ ] Publish-to-PyPI automation (release workflow, version bump, changelog). (discovered during: planning)
- [ ] Optional process-pool backend (cloudpickle/dill/loky) as an extra, to lift the stdlib-pickle limit on closures/lambdas/locally-defined functions. Stdlib `pickle` serializes by reference and cannot do this; the trampoline fix in the plan only covers importable functions. (discovered during: planning)

## Performance

- [ ] Benchmark suite comparing asyncify overhead vs raw `run_in_executor`, and per-item cost of the async iterator (one thread round-trip per element). (discovered during: planning)
- [ ] Investigate batching / chunked iteration for `AsyncIterMixin` to amortize executor dispatch on large iterables. (discovered during: planning)

## Testing

- [ ] uvloop integration test job in CI to validate the running-loop binding under a non-default asyncio loop. (discovered during: planning)

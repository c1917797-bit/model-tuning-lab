# R45 compilation observation component

Default-off diagnostic on the pinned official image, not an algorithm or speed fix.

It times source-verified Triton JIT cache misses, compiler API calls, and lazy binary loads. Exact integer clocks, nested IDs, key hashes and selected constexpr values remain in the owned worker evidence writer. It does not seed caches, add warmups, change kernel bodies, metadata, state, numerical/finite checks, completion or durability.

Healthy original arguments, results and exceptions are preserved. Observation bounds, source/ownership drift and evidence-writer failure invalidate/abort this diagnostic; they are not algorithm failures. An original upstream exception takes priority if recording its end also fails. Already-initialized binary loads pass through unobserved, and installed/captured aliases are restored on explicit uninstall.

The CPU official-image check uses an actual JIT before-hook cancellation, so it deliberately performs no backend compilation or inference. Its rank is unassigned. The package is not wired into a serving worker yet: enabled bootstrap refuses an absent source-bound worker-loader integration. Four-worker activation, bounded NPU diagnostics, actual blocking-budget audit and any speed conclusion remain pending.

A manifest will bind the frozen code checkpoint before device admission. The bootstrap and launcher follow the repository runtime-monkeypatch template, using only this thread's reviewed generic worker-loading path. No old successful HYPIC algorithm/operator/runner/scheduler is imported.

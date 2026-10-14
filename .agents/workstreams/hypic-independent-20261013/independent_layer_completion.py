"""Draft layer completion barrier; not wired into frozen HYPIC runtime."""
def complete_layer(items, *, execute, synchronize, receipt, emit):
    """Execute all ordered plans, then synchronize once before any receipt.

    Caller retains material leases through this function. This does not batch
    kernels, establish cross-stream safety, or prove device numerical equality.
    No receipt is emitted if execution or the completion barrier fails.
    """
    items=tuple(items)
    if not items:raise ValueError("nonempty layer work required")
    if not all(callable(x) for x in (execute,synchronize,receipt,emit)):
        raise ValueError("explicit execution and completion callbacks required")
    for item in items:execute(item)
    synchronize()
    events=tuple(receipt(item) for item in items)
    for event in events:emit(event)
    return len(events)


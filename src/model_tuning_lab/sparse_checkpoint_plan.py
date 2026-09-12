"""Block-aligned sparse checkpoint planning; no runtime activation implied.

Minimize weighted replay tokens subject to a checkpoint-count budget. The
histogram must contain training/warmup overlaps only, never future requests.
This independent implementation operates on native cache block boundaries;
it does not round an already optimized token-level plan after the fact.
"""
import math


def plan_checkpoints(histogram, block_size, budget):
    """Return token positions. Position zero is the implicit empty state.

    histogram[t] is the nonnegative weight of overlap length t. Every selected
    position is a positive block multiple and costs one checkpoint. KV coverage
    and actual recurrent-state retention must be enforced by the runtime adapter.
    """
    if type(block_size) is not int or block_size <= 0:
        raise ValueError("block_size must be a positive integer")
    if type(budget) is not int or budget < 0:
        raise ValueError("budget must be a nonnegative integer")
    weights = [float(w) for w in histogram]
    if any(not math.isfinite(w) or w < 0 for w in weights):
        raise ValueError("histogram weights must be finite and nonnegative")
    n = max(0, (len(weights) - 1) // block_size)
    if not n or not budget or not any(weights):
        return []
    # Remainder replay t % block_size is independent of the chosen plan.
    bins = [0.0] * (n + 1)
    for t, weight in enumerate(weights):
        bins[t // block_size] += weight
    mass, moment = [0.0], [0.0]
    for i, weight in enumerate(bins):
        mass.append(mass[-1] + weight)
        moment.append(moment[-1] + i * weight)

    def interval(left, right):
        return moment[right] - moment[left] - left * (mass[right] - mass[left])

    # A path through checkpoint boundaries partitions overlaps into intervals.
    # State: best cost up to (excluding) the final selected boundary.
    previous = {0: (0.0, ())}
    best = (interval(0, n + 1), ())
    for _ in range(min(budget, n)):
        current = {}
        for end in range(1, n + 1):
            choices = [(value + interval(start, end), path + (end,))
                       for start, (value, path) in previous.items() if start < end]
            if not choices:
                continue
            current[end] = min(choices)
            value, path = current[end]
            candidate = (value + interval(end, n + 1), path)
            if candidate[0] < best[0]:
                best = candidate
        previous = current
    return [p * block_size for p in best[1]]


def restorable_position(positions, overlap_tokens, kv_coverage_tokens):
    """Never restore a recurrent state beyond either matching or retained KV."""
    limit = min(overlap_tokens, kv_coverage_tokens)
    return max((p for p in positions if 0 < p <= limit), default=0)


def split_at_checkpoint(positions, computed_tokens, native_new_tokens, prompt_tokens):
    """Shorten an already native-approved prefill step at the next checkpoint.

    Never extend a scheduler allocation, force progress when native returns zero,
    or split decode. The runtime still owns alignment and admission checks.
    """
    if native_new_tokens < 0 or computed_tokens < 0:
        raise ValueError("negative scheduler token count")
    if computed_tokens >= prompt_tokens or not native_new_tokens:
        return native_new_tokens
    end = computed_tokens + native_new_tokens
    boundary = min((p for p in positions if computed_tokens < p < end
                    and p <= prompt_tokens), default=end)
    return boundary - computed_tokens


def publication_mask(positions, start_block, end_block, block_size):
    """Publish selected complete state blocks only, never null or partial state.

    Native cache_full_blocks additionally filters null blocks. Unselected state
    blocks remain valid running state but are not advertised as reusable cache.
    """
    if block_size <= 0 or start_block < 0 or end_block < start_block:
        raise ValueError("invalid block interval")
    chosen = frozenset(positions)
    return [(i + 1) * block_size in chosen for i in range(start_block, end_block)]

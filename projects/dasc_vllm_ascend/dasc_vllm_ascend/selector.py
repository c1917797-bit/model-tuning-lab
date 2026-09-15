"""Weight-derived DASC retained-head selection and shape audit."""

from __future__ import annotations

import math
from typing import Any


class DascSelectorError(ValueError):
    pass


def head_horizons(module: Any, config: Any) -> Any:
    """Return the paper-derived decay horizon for each local GDN head."""
    import torch
    import torch.nn.functional as functional

    a_log = module.A_log.detach().float().reshape(-1)
    dt_bias = module.dt_bias.detach().float().reshape(-1)
    if a_log.shape != dt_bias.shape:
        raise DascSelectorError(
            f"DASC decay parameter mismatch: {a_log.shape} vs {dt_bias.shape}"
        )
    decay = -torch.exp(a_log) * functional.softplus(
        dt_bias + config.representative_a
    )
    return math.log(config.epsilon) / decay


def retained_head_indices(
    module: Any, config: Any, *, target_count: int | None = None
) -> Any:
    """Select local heads, optionally padding to a TP-consistent count.

    Padding retains the longest-horizon omitted heads.  It therefore preserves
    every head admitted by the DASC threshold while making page geometry equal
    across tensor-parallel workers.
    """
    import torch

    cached = getattr(module, "_mst_dasc_retained_indices", None)
    if cached is not None:
        if target_count is not None and cached.numel() != target_count:
            raise DascSelectorError(
                "DASC retained indices were cached with a different TP geometry"
            )
        return cached
    horizon = head_horizons(module, config)
    retained = (horizon > config.w_max).nonzero(as_tuple=False).flatten()
    if retained.numel() == 0:
        raise DascSelectorError("DASC selector retained zero local heads")
    if target_count is not None:
        if not retained.numel() <= target_count <= horizon.numel():
            raise DascSelectorError(
                f"invalid TP target {target_count} for "
                f"{retained.numel()}/{horizon.numel()} local heads"
            )
        if target_count > retained.numel():
            retained = torch.topk(
                horizon, k=target_count, largest=True, sorted=False
            ).indices.sort().values
    module._mst_dasc_retained_indices = retained
    return retained


def align_retained_heads_tp(
    named_modules: list[tuple[str, Any]],
    config: Any,
    device_group: Any,
) -> dict[str, Any]:
    """Synchronize per-layer retained counts across TP ranks with MAX.

    Indices stay rank-local because the model weights are TP-sharded.  Only the
    count is collective state, which is sufficient to make vLLM MambaSpec page
    geometry identical on every worker.
    """
    import torch
    import torch.distributed as dist

    if not named_modules:
        raise DascSelectorError("DASC found no GDN modules to align")
    names = [name for name, _ in named_modules]
    if len(names) != len(set(names)):
        raise DascSelectorError("DASC GDN module names are not unique")

    local_counts = []
    for _, module in named_modules:
        horizon = head_horizons(module, config)
        count = int((horizon > config.w_max).sum().item())
        if count == 0:
            raise DascSelectorError("DASC selector retained zero local heads")
        local_counts.append(count)

    reference = named_modules[0][1].A_log
    common = torch.tensor(local_counts, dtype=torch.int32, device=reference.device)
    dist.all_reduce(common, op=dist.ReduceOp.MAX, group=device_group)
    common_counts = [int(value) for value in common.cpu().tolist()]

    for (_, module), target_count in zip(named_modules, common_counts):
        retained_head_indices(module, config, target_count=target_count)

    return {
        "layer_names": names,
        "local_counts": local_counts,
        "common_counts": common_counts,
        "extra_local_heads": sum(common_counts) - sum(local_counts),
    }


def unique_head_axis(shape: tuple[int, ...], total_heads: int) -> int:
    axes = [axis for axis, size in enumerate(shape) if size == total_heads]
    if len(axes) != 1:
        raise DascSelectorError(
            f"cannot uniquely map {total_heads} heads into state shape {shape}"
        )
    return axes[0]

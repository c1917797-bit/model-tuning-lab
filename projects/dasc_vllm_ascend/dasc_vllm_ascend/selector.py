"""Weight-derived DASC retained-head selection and shape audit."""

from __future__ import annotations

import math
from typing import Any


class DascSelectorError(ValueError):
    pass


def retained_head_indices(module: Any, config: Any) -> Any:
    """Select local heads from loaded GDN decay parameters."""
    import torch
    import torch.nn.functional as functional

    cached = getattr(module, "_mst_dasc_retained_indices", None)
    if cached is not None:
        return cached
    a_log = module.A_log.detach().float().reshape(-1)
    dt_bias = module.dt_bias.detach().float().reshape(-1)
    if a_log.shape != dt_bias.shape:
        raise DascSelectorError(
            f"DASC decay parameter mismatch: {a_log.shape} vs {dt_bias.shape}"
        )
    decay = -torch.exp(a_log) * functional.softplus(
        dt_bias + config.representative_a
    )
    horizon = math.log(config.epsilon) / decay
    retained = (horizon > config.w_max).nonzero(as_tuple=False).flatten()
    if retained.numel() == 0:
        raise DascSelectorError("DASC selector retained zero local heads")
    module._mst_dasc_retained_indices = retained
    return retained


def unique_head_axis(shape: tuple[int, ...], total_heads: int) -> int:
    axes = [axis for axis, size in enumerate(shape) if size == total_heads]
    if len(axes) != 1:
        raise DascSelectorError(
            f"cannot uniquely map {total_heads} heads into state shape {shape}"
        )
    return axes[0]

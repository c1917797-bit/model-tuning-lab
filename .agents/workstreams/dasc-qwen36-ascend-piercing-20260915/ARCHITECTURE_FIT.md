# DASC Architecture Fit

## Decision

`fits-with-implementation` for a Qwen-GDN DASC-NR canary.

The selected checkpoint has the model mechanism DASC needs: Qwen3.6 is a Qwen3.5 text-family hybrid model with 64 layers, 48 `linear_attention`/GDN layers, and per-GDN-layer `A_log` plus `dt_bias` decay parameters. The weight-derived horizon signal is non-empty and heterogeneous across heads.

This does not yet prove serving benefit. DASC's speed path requires recurrent state checkpoint store/load and cache-hit replay behavior. That runtime path still needs source mapping in vLLM-Ascend.

## Evidence

- Model path: `/cache/efim/Qwen3.6-27B`
- `config.json` text config model type: `qwen3_5_text`
- Layers: 64 total, 48 `linear_attention`, 16 `full_attention`
- GDN decay weights in safetensors index: 48 `A_log`, 48 `dt_bias`
- Per GDN layer head units: 48
- Total GDN head-state units: 2304

Weight-derived DASC head-retention counts using `epsilon=1e-3` and representative `a=-0.3`:

| `W_max` | Retained heads | Temporal head compression if only retained heads are stored |
|---:|---:|---:|
| 16 | 2093 / 2304 | 1.10x |
| 64 | 1728 / 2304 | 1.33x |
| 128 | 1487 / 2304 | 1.55x |
| 512 | 1035 / 2304 | 2.23x |
| 1024 | 883 / 2304 | 2.61x |

Full checkpoint compression will be lower than these temporal-only ratios because convolution state remains part of the checkpoint accounting.

## Implication

The first practical canary should start with DASC-NR at `W_max=64` or `W_max=128`, not with `W_max=512/1024`. The latter are useful stress points but are more likely to trade quality for capacity.

The next blocker is not the selector; it is the service integration path: finding or adding a plugin-owned recurrent state checkpoint store/load path that can be activated only on prefix-cache hits.


#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

EXPECTED_PROFILE_SHA256 = 'b3bddd3b1a8b96571f20c59d801aa21da3da673f875f86a3b04318afbdb480a8'
PAPER_LOCAL_REDUCTION = 0.4517
TARGET_SPEEDUP = 1.10

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def amdahl_speedup(fraction: float, reduction: float) -> float:
    return 1.0 / (1.0 - fraction * reduction)

def required_reduction(fraction: float, target_speedup: float) -> float:
    return (1.0 - 1.0 / target_speedup) / fraction

def matches(operator: dict, needles: tuple[str, ...]) -> bool:
    identity = f"{operator['name']} {operator['type']}".lower()
    return any(needle.lower() in identity for needle in needles)

def audit(profile_path: Path) -> dict:
    observed_hash = sha256(profile_path)
    if observed_hash != EXPECTED_PROFILE_SHA256:
        raise RuntimeError(f'profile hash mismatch: {observed_hash}')
    profile = json.loads(profile_path.read_text())
    records = [r for r in profile['records'] if r['phase'] == 'decode']
    if len(records) != 4 or sorted(r['rank'] for r in records) != [0, 1, 2, 3]:
        raise RuntimeError('expected four decode ranks')
    faithful_needles = ('RecurrentGatedDeltaRule',)
    aggressive_needles = ('RecurrentGatedDeltaRule', 'FusedGdnGating', 'l2norm', 'Slice', 'ConcatD')
    ranks = []
    for record in records:
        interval = float(record['npu_interval_union_ms'])
        faithful_ms = sum(float(op['kernel_sum_ms']) for op in record['top_operators'] if matches(op, faithful_needles))
        aggressive_ms = sum(float(op['kernel_sum_ms']) for op in record['top_operators'] if matches(op, aggressive_needles))
        if faithful_ms <= 0 or aggressive_ms < faithful_ms:
            raise RuntimeError(f"missing affected operator on rank {record['rank']}")
        faithful = faithful_ms / interval
        aggressive = aggressive_ms / interval
        ranks.append({
            'rank': record['rank'],
            'npu_interval_union_ms': interval,
            'faithful_recurrent_ms': faithful_ms,
            'faithful_fraction': faithful,
            'paper_reduction_speedup_bound': amdahl_speedup(faithful, PAPER_LOCAL_REDUCTION),
            'perfect_faithful_speedup_bound': amdahl_speedup(faithful, 1.0),
            'aggressive_derivative_ms': aggressive_ms,
            'aggressive_derivative_fraction': aggressive,
            'perfect_derivative_speedup_bound': amdahl_speedup(aggressive, 1.0),
            'derivative_reduction_required_for_target': required_reduction(aggressive, TARGET_SPEEDUP),
        })
    faithful = [r['faithful_fraction'] for r in ranks]
    aggressive = [r['aggressive_derivative_fraction'] for r in ranks]
    required = [r['derivative_reduction_required_for_target'] for r in ranks]
    summary = {
        'faithful_fraction_percent_range': [100*min(faithful), 100*max(faithful)],
        'paper_reduction_speedup_bound_range': [min(r['paper_reduction_speedup_bound'] for r in ranks), max(r['paper_reduction_speedup_bound'] for r in ranks)],
        'perfect_faithful_speedup_bound_range': [min(r['perfect_faithful_speedup_bound'] for r in ranks), max(r['perfect_faithful_speedup_bound'] for r in ranks)],
        'aggressive_derivative_fraction_percent_range': [100*min(aggressive), 100*max(aggressive)],
        'perfect_derivative_speedup_bound_range': [min(r['perfect_derivative_speedup_bound'] for r in ranks), max(r['perfect_derivative_speedup_bound'] for r in ranks)],
        'derivative_reduction_required_percent_range': [100*min(required), 100*max(required)],
    }
    return {
        'schema': 'kvbuffer-opportunity-audit/v1',
        'status': 'complete',
        'profile_path': str(profile_path),
        'profile_sha256': observed_hash,
        'paper_reported_local_latency_reduction': PAPER_LOCAL_REDUCTION,
        'target_speedup': TARGET_SPEEDUP,
        'scope': {'faithful': list(faithful_needles), 'aggressive_derivative': list(aggressive_needles)},
        'ranks': ranks,
        'summary': summary,
        'decision': 'no-go' if min(required) > PAPER_LOCAL_REDUCTION else 'needs-target-npu-canary',
        'interpretation': 'Optimistic screen over measured NPU intervals, not E2E. Aggressive scope over-attributes all Slice/ConcatD work and assumes it can be removed.',
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise RuntimeError(f'refusing to overwrite {args.output_dir}')
    result = audit(args.profile)
    args.output_dir.mkdir(parents=True)
    output = args.output_dir / 'opportunity-audit.json'
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(output)
    print(json.dumps(result['summary'], sort_keys=True))
    if result['decision'] != 'no-go':
        raise SystemExit(2)

if __name__ == '__main__':
    main()

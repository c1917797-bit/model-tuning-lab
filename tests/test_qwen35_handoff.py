#!/usr/bin/env python3
"""Synthetic contract regressions only; this file performs no model benchmark."""
from copy import deepcopy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('handoff', ROOT / 'scripts/validate_qwen35_handoff.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Unitless synthetic values at the exact acceptance boundaries, not measurements.
fixture = {
    'role': 'candidate', 'evidence_class': 'matched-treatment-ab', 'percentile': 'p95',
    'baseline_id': 'synthetic-test-only', 'runtime_only': True,
    'activation_all_ranks': True, 'paired_same_environment': True,
    'warm_state_controlled': True, 'quality_complete': True,
    'source_fingerprints_match': True, 'prefix_cache_isolated': True,
    'comparison_registered': True, 'tail_risk_reviewed': True,
    'matrix': [dict(c=c, r=r, baseline_ttft=1.0, candidate_ttft=0.60,
                    baseline_tpot=1.0, candidate_tpot=0.80)
               for c in (1, 5, 8, 16) for r in (1, 2, 3)]
}
assert not module.promotion_errors(fixture)
count = 1
for key, value in [('role', 'control'), ('evidence_class', 'cold-warm-diagnostic'),
                   ('percentile', 'p50'), ('runtime_only', False),
                   ('quality_complete', False), ('source_fingerprints_match', False),
                   ('warm_state_controlled', False), ('baseline_id', ''),
                   ('matrix', fixture['matrix'][:-1]), ('generalization_claim', True)]:
    case = deepcopy(fixture)
    case[key] = value
    assert module.promotion_errors(case), key + ' incorrectly passed'
    count += 1
case = deepcopy(fixture)
for row in case['matrix']:
    row['candidate_tpot'] = 1 / 1.208482466
assert module.promotion_errors(case), 'near miss rounded into a pass'
count += 1
case = deepcopy(fixture)
case['matrix'][0]['candidate_ttft'] = float('nan')
assert module.promotion_errors(case), 'nonfinite measurement accepted'
count += 1
case = deepcopy(fixture)
case['matrix'][-1] = deepcopy(case['matrix'][0])
assert module.promotion_errors(case), 'duplicate matrix accepted'
count += 1
assert module.validate_packet(ROOT)['performance_accepted'] is False
count += 1
print('PASS:', count, 'handoff regression checks; zero NPU work launched')

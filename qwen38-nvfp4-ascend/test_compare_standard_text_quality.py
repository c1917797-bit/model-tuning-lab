"""Dependency-free comparator regression tests; no NPU/model calls."""
import copy
from compare_standard_text_quality import validate, compare, PINNED

expected = {'mmlu_example': [{'id': 0}, {'id': 1}],
            'gsm8k': [{'id': 2}, {'id': 3}]}
base = dict(switch_run_protocol=dict(PINNED, limit=None, concurrency=8,
            tasks=list(expected), model='fixture', tokenizer='fixture'),
            lm_eval_version='0.4.13', versions={k: 1 for k in expected},
            **{'n-shot': {k: 5 for k in expected},
               'n-samples': {k: dict(original=2, effective=2) for k in expected}})
base['samples'], base['results'] = {}, {}
for name, docs in expected.items():
    metric = 'acc' if name.startswith('mmlu_') else 'exact_match'
    filters = ['none'] if metric == 'acc' else ['strict-match', 'flexible-extract']
    base['samples'][name] = [
        dict(doc_id=i, doc=d, filter=f, resps=[[1]], filtered_resps=[1],
             **{metric: float(i == 0)})
        for f in filters for i, d in enumerate(docs)]
    base['results'][name] = {metric+','+f: 0.5 for f in filters}
validate(base, expected)
result = compare(base, copy.deepcopy(base), expected)
assert result['mmlu_micro']['delta'] == 0
assert result['gsm8k_strict']['n'] == 2

def rejected(mutation, pair=False):
    broken = copy.deepcopy(base)
    mutation(broken)
    try:
        compare(base, broken, expected) if pair else validate(broken, expected)
    except ValueError:
        return
    raise AssertionError('Invalid result accepted')

rejected(lambda d: d['switch_run_protocol'].update(limit=2))
rejected(lambda d: d['n-shot'].update(mmlu_example=0))
rejected(lambda d: d['samples']['gsm8k'].pop())
rejected(lambda d: d['samples']['mmlu_example'][1].update(doc_id=0))
rejected(lambda d: d['samples']['mmlu_example'][0].update(doc={'wrong': 1}))
rejected(lambda d: d['results']['mmlu_example'].update({'acc,none': 1.0}))
rejected(lambda d: d['samples']['mmlu_example'][0].update(resps=[]))
rejected(lambda d: d['switch_run_protocol'].update(concurrency=1), pair=True)
rejected(lambda d: d['versions'].update(gsm8k=2), pair=True)
print('PASS: complete fixture, paired identity, partial/shot/count/duplicate/data/score/evidence/protocol/version rejection')

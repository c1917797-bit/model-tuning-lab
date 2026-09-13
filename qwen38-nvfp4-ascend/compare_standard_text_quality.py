"""Compare complete pinned lm-eval text results, never generation-based MMLU.

This validates scoring artifacts, not model/image provenance or migration approval.
Native tokenizer/prompt bytes may differ across models; dataset documents must not.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
from offline_standard_data import read_rows

MATCH_FIELDS = ('concurrency', 'seed', 'num_fewshot', 'enable_thinking',
                'max_length', 'max_gen_toks', 'batch_size')
PINNED = dict(seed=1024, num_fewshot=5, enable_thinking=False,
              max_length=40960, max_gen_toks=4096, batch_size=1)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def population(root):
    subjects = sorted(p.name[:-9] for p in
                      (root / 'prepared/mmlu/test').glob('*_test.csv'))
    require(len(subjects) == 57, 'Expected exactly 57 MMLU subjects')
    docs = {'mmlu_' + s: read_rows(root, 'mmlu', s)['test'] for s in subjects}
    require(sum(map(len, docs.values())) == 14042, 'Expected full MMLU 14042')
    docs['gsm8k'] = read_rows(root, 'gsm8k')['test']
    require(len(docs['gsm8k']) == 1319, 'Expected GSM8K 1319')
    return docs


def validate(doc, expected):
    protocol = doc.get('switch_run_protocol', {})
    require(protocol.get('limit', 'missing') is None, 'Partial/preflight run rejected')
    require(set(protocol.get('tasks', [])) == set(expected), 'Task population mismatch')
    require(len(protocol['tasks']) == len(expected), 'Duplicate protocol task')
    require(all(protocol.get(k) == v for k, v in PINNED.items()), 'Protocol drift')
    require(protocol.get('concurrency') in (1, 5, 8, 16), 'Invalid concurrency')
    require(doc.get('lm_eval_version') == '0.4.13', 'Unpinned harness version')
    require(set(doc.get('samples', {})) == set(expected), 'Missing/extra sample tasks')
    indexed = {}
    for name, documents in expected.items():
        require(doc.get('n-shot', {}).get(name) == 5, name + ': not five-shot')
        require(doc.get('n-samples', {}).get(name) ==
                {'original': len(documents), 'effective': len(documents)},
                name + ': incomplete count')
        metric = 'exact_match' if name == 'gsm8k' else 'acc'
        filters = ('strict-match', 'flexible-extract') if name == 'gsm8k' else ('none',)
        rows = doc['samples'][name]
        require(len(rows) == len(documents) * len(filters), name + ': row count')
        values = {}
        for sample in rows:
            i, f = sample.get('doc_id'), sample.get('filter')
            require(type(i) is int and 0 <= i < len(documents), name + ': invalid doc_id')
            require(f in filters and (i, f) not in values, name + ': duplicate/filter')
            require(sample.get('doc') == documents[i], name + ': dataset document drift')
            require(sample.get(metric) in (0, 1), name + ': non-binary/missing metric')
            require(sample.get('resps') and sample.get('filtered_resps'),
                    name + ': missing raw scoring evidence')
            values[i, f] = float(sample[metric])
        for f in filters:
            rate = sum(values[i, f] for i in range(len(documents))) / len(documents)
            recorded = doc.get('results', {}).get(name, {}).get(metric + ',' + f)
            require(isinstance(recorded, (int, float)) and
                    math.isclose(rate, recorded, abs_tol=1e-12), name + ': score mismatch')
        primary = filters[0]
        indexed[name] = [values[i, primary] for i in range(len(documents))]
    return indexed


def paired(a, b):
    require(len(a) == len(b) and len(a) > 1, 'Invalid paired population')
    n = len(a)
    differences = [y-x for x, y in zip(a, b)]
    delta = sum(differences) / n
    variance = sum((d-delta)**2 for d in differences) / (n-1)
    margin = 1.96 * math.sqrt(variance / n)
    return dict(n=n, control=sum(a)/n, candidate=sum(b)/n, delta=delta,
                candidate_only_correct=sum(x == 0 and y == 1 for x, y in zip(a, b)),
                control_only_correct=sum(x == 1 and y == 0 for x, y in zip(a, b)),
                paired_normal_approx_95ci=[max(-1, delta-margin), min(1, delta+margin)])


def compare(a, b, expected):
    left, right = validate(a, expected), validate(b, expected)
    require(all(a['switch_run_protocol'][k] == b['switch_run_protocol'][k]
                for k in MATCH_FIELDS), 'Cross-arm protocol mismatch')
    require(a.get('versions') == b.get('versions'), 'Task version mismatch')
    subjects = sorted(k for k in expected if k.startswith('mmlu_'))
    per_subject = {k: paired(left[k], right[k]) for k in subjects}
    return dict(
        mmlu_micro=paired([x for k in subjects for x in left[k]],
                          [x for k in subjects for x in right[k]]),
        mmlu_macro=dict(control=sum(x['control'] for x in per_subject.values())/len(subjects),
                        candidate=sum(x['candidate'] for x in per_subject.values())/len(subjects)),
        mmlu_subjects=per_subject, gsm8k_strict=paired(left['gsm8k'], right['gsm8k']),
        caveat='Approximate paired intervals, not an automatic lossless or migration verdict. '
               'Image/model/data provenance and performance must be audited separately.')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--control', required=True, type=Path)
    p.add_argument('--candidate', required=True, type=Path)
    p.add_argument('--data-root', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    require(not args.output.exists(), 'Refusing to overwrite a report')
    a, b = [json.loads(x.read_text()) for x in (args.control, args.candidate)]
    report = compare(a, b, population(args.data_root))
    report['sources'] = {label: dict(path=str(path.resolve()),
                         sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                         for label, path in [('control', args.control), ('candidate', args.candidate)]}
    report['models'] = [a['switch_run_protocol']['model'], b['switch_run_protocol']['model']]
    with args.output.open('x') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()

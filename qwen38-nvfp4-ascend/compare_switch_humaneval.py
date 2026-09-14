"""Cross-model HumanEval-instruct comparison; never executes generated code.

Native rendered prompts may differ. Require identical source problems/protocol,
one generation per problem, and samples bound to sandbox execution evidence.
This is a scoring audit, not proof of model/image provenance or sandbox isolation.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from offline_standard_data import read_rows
from run_switch_humaneval import PROTOCOL, document_hash, completion
from compare_standard_text_quality import paired, require


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def index(items, label):
    result = {}
    for item in items:
        key = item.get('task_id')
        require(isinstance(key, str) and key not in result, label + ': duplicate/missing task')
        result[key] = item
    return result


def validate(records, samples, results, expected):
    rr, ss, ee = [index(x, name) for x, name in
                  ((records, 'records'), (samples, 'samples'), (results, 'results'))]
    require(all(set(x) == set(expected) for x in (rr, ss, ee)), 'Incomplete/extra population')
    outcomes, hashes, models = [], [], set()
    for key in sorted(expected):
        r, s, e = rr[key], ss[key], ee[key]
        require(not r.get('error'), key + ': serving error')
        require(r.get('protocol') == PROTOCOL, key + ': generation protocol drift')
        require(r.get('source_document_sha256') == document_hash(expected[key]),
                key + ': source problem drift')
        digest = r.get('rendered_prompt_sha256')
        require(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest),
                key + ': missing rendered prompt hash')
        hashes.append(digest)
        request = r.get('request', {})
        require(all(request.get(k) == PROTOCOL[k] for k in
                    ('temperature', 'seed', 'max_tokens', 'stop')), key + ': request drift')
        require(set(request) == {'model', 'prompt', 'temperature', 'seed', 'max_tokens', 'stop'},
                key + ': unexpected request override')
        tokens = request.get('prompt')
        require(isinstance(tokens, list) and tokens and
                all(type(t) is int and t >= 0 for t in tokens), key + ': missing input tokens')
        require(isinstance(request.get('model'), str) and request['model'], key + ': missing model')
        models.add(request['model'])
        choices = r.get('response', {}).get('choices', [])
        require(len(choices) == 1 and isinstance(choices[0].get('text'), str),
                key + ': missing/surplus generation')
        require(choices[0].get('finish_reason') in ('stop', 'length'),
                key + ': invalid termination')
        require(s.get('completion') == completion(choices[0]['text']), key + ': extraction mismatch')
        require(e.get('completion') == s['completion'], key + ': executed sample mismatch')
        require(type(e.get('passed')) is bool and isinstance(e.get('result'), str),
                key + ': invalid execution outcome')
        require(e['passed'] == (e['result'] == 'passed'), key + ': inconsistent outcome')
        outcomes.append(int(e['passed']))
    require(len(models) == 1, 'Mixed model names in one arm')
    return outcomes, hashes


def load_arm(directory, result_path, problems_sha, expected):
    sample_path = directory / 'samples.jsonl'
    manifest_path = Path(str(result_path) + '.manifest.json')
    manifest = json.loads(manifest_path.read_text())
    require(manifest.get('schema') == 'switch-humaneval-execution/v1', 'Execution manifest schema')
    require(manifest.get('samples_sha256') == sha(sample_path), 'Samples checksum mismatch')
    require(manifest.get('results_sha256') == sha(result_path), 'Results checksum mismatch')
    require(manifest.get('problems_sha256') == problems_sha, 'Problems checksum mismatch')
    require(manifest.get('timeout_seconds') == 3 and manifest.get('workers') == 4,
            'Sandbox evaluator protocol drift')
    require(manifest.get('execution_guard') == 'enabled-in-disposable-copy', 'Execution guard missing')
    evaluator = manifest.get('evaluator_sha256', {})
    require(set(evaluator) == {'execution.py', 'evaluation.py', 'data.py'} and
            all(isinstance(v, str) and re.fullmatch('[0-9a-f]{64}', v) for v in evaluator.values()),
            'Evaluator identity missing')
    paths = sorted(directory.glob('HumanEval-*.json'))
    records = []
    for path in paths:
        sidecar = path.with_suffix('.sha256').read_text().split()
        require(sidecar == [sha(path), path.name], 'Generation record checksum mismatch')
        records.append(json.loads(path.read_text()))
    result = validate(records, rows(sample_path), rows(result_path), expected)
    sources = {str(p.resolve()): sha(p) for p in
               paths + [sample_path, result_path, manifest_path]}
    return result, evaluator, sources


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--control-dir', required=True, type=Path)
    p.add_argument('--candidate-dir', required=True, type=Path)
    p.add_argument('--control-results', required=True, type=Path)
    p.add_argument('--candidate-results', required=True, type=Path)
    p.add_argument('--data-root', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    require(not args.output.exists(), 'Refusing to overwrite report')
    documents = read_rows(args.data_root, 'humaneval')['test']
    expected = index(documents, 'source problems')
    require(set(expected) == {'HumanEval/' + str(i) for i in range(164)}, 'Expected full HumanEval164')
    problem_path = args.data_root / 'unpack/humaneval/data/HumanEval.jsonl.gz'
    a, av, sources_a = load_arm(args.control_dir, args.control_results, sha(problem_path), expected)
    b, bv, sources_b = load_arm(args.candidate_dir, args.candidate_results, sha(problem_path), expected)
    require(av == bv, 'Cross-arm evaluator source mismatch')
    report = dict(schema='switch-paired-humaneval/v1', pass_at_1=paired(a[0], b[0]),
        native_prompt_hash_differences=sum(x != y for x, y in zip(a[1], b[1])),
        disagreements=[dict(task_id=k, control_passed=bool(x), candidate_passed=bool(y))
                       for k, x, y in zip(sorted(expected), a[0], b[0]) if x != y],
        sources=dict(control=sources_a, candidate=sources_b),
        caveat='Native template differences are allowed. Approximate paired interval is not '
               'a lossless or migration verdict. Audit model/image and sandbox isolation separately.')
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()


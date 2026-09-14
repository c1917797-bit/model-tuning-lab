"""Dependency-free paired HumanEval scoring checks; no generated code execution."""
import copy
from compare_switch_humaneval import validate
from run_switch_humaneval import PROTOCOL, document_hash

expected = {'HumanEval/'+str(i): dict(task_id='HumanEval/'+str(i), prompt='def f():\n', test='fixture')
            for i in range(2)}
records, samples, results = [], [], []
for key, doc in expected.items():
    records.append(dict(task_id=key, protocol=copy.deepcopy(PROTOCOL),
        source_document_sha256=document_hash(doc), rendered_prompt_sha256='a'*64,
        request=dict(model='fixture', prompt=[1, 2], temperature=0, seed=1024,
                     max_tokens=1024, stop=PROTOCOL['stop']),
        response=dict(choices=[dict(text='    return 1\n```', finish_reason='stop')])))
    samples.append(dict(task_id=key, completion='    return 1\n'))
    results.append(dict(task_id=key, completion='    return 1\n', passed=True, result='passed'))
assert validate(records, samples, results, expected)[0] == [1, 1]
other = copy.deepcopy(records)
for r in other:
    r['rendered_prompt_sha256'] = 'b'*64
    r['request']['model'] = 'other'
    r['request']['prompt'] = [5, 6, 7]
assert validate(other, samples, results, expected)[0] == [1, 1]

def rejected(mutate):
    r, s, e = copy.deepcopy((records, samples, results))
    mutate(r, s, e)
    try:
        validate(r, s, e, expected)
    except ValueError:
        return
    raise AssertionError('Invalid artifact accepted')

rejected(lambda r,s,e: r.pop())
rejected(lambda r,s,e: r.append(r[0]))
rejected(lambda r,s,e: r[0].update(source_document_sha256='b'*64))
rejected(lambda r,s,e: r[0]['request'].update(seed=3))
rejected(lambda r,s,e: r[0]['request'].update(ignore_eos=True))
rejected(lambda r,s,e: r[0].update(error='timeout'))
rejected(lambda r,s,e: r[0].update(response={}))
rejected(lambda r,s,e: s[0].update(completion='different'))
rejected(lambda r,s,e: e[0].update(completion='different'))
rejected(lambda r,s,e: e[0].update(passed='false'))
rejected(lambda r,s,e: e[0].update(result='failed'))
rejected(lambda r,s,e: r[0]['request'].update(model='mixed'))
print('PASS: native-template difference accepted; partial/duplicate/source/request/error/extraction/execution/type rejection')

# Exercise the on-disk evidence chain, not only in-memory score rows.
import json
import tempfile
from pathlib import Path
from compare_switch_humaneval import load_arm, sha

with tempfile.TemporaryDirectory(prefix='he-comparator-test-') as temporary:
    root = Path(temporary)
    for record in records:
        path = root/(record['task_id'].replace('/', '-')+'.json')
        path.write_text(json.dumps(record))
        path.with_suffix('.sha256').write_text(sha(path)+'  '+path.name+'\n')
    sample_path, result_path = root/'samples.jsonl', root/'scores.jsonl'
    sample_path.write_text(''.join(json.dumps(r)+'\n' for r in samples))
    result_path.write_text(''.join(json.dumps(r)+'\n' for r in results))
    manifest_path = Path(str(result_path)+'.manifest.json')
    manifest = dict(schema='switch-humaneval-execution/v1', workers=4,
        timeout_seconds=3, samples_sha256=sha(sample_path), results_sha256=sha(result_path),
        problems_sha256='c'*64, execution_guard='enabled-in-disposable-copy',
        evaluator_sha256={n: 'd'*64 for n in ('execution.py', 'evaluation.py', 'data.py')})
    manifest_path.write_text(json.dumps(manifest))
    assert load_arm(root, result_path, 'c'*64, expected)[0][0] == [1, 1]
    for field, value in [('samples_sha256', '0'*64), ('results_sha256', '0'*64),
                         ('problems_sha256', '0'*64), ('timeout_seconds', 1),
                         ('workers', 2), ('evaluator_sha256', {})]:
        broken = dict(manifest, **{field: value})
        manifest_path.write_text(json.dumps(broken))
        try:
            load_arm(root, result_path, 'c'*64, expected)
        except ValueError:
            pass
        else:
            raise AssertionError('Bad manifest accepted: '+field)
    manifest_path.write_text(json.dumps(manifest))
    (root/'HumanEval-0.sha256').write_text('0'*64+'  HumanEval-0.json\n')
    try:
        load_arm(root, result_path, 'c'*64, expected)
    except ValueError:
        pass
    else:
        raise AssertionError('Modified generation record accepted')
print('PASS: disk evidence binding and checksum/protocol/evaluator corruption rejection')

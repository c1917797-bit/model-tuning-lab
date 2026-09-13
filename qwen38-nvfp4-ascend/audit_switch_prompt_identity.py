#!/usr/bin/env python3
"""Offline native-template versus actual API prompt-token audit, no inference."""
import argparse
from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from transformers import AutoTokenizer


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--tokenizer', required=True)
    ap.add_argument('--roots', type=Path, nargs='+', required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        ap.error('Fresh output required')
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, local_files_only=True, trust_remote_code=False)
    cases = []
    for root in args.roots:
        paths = sorted(root.glob('*-*.json'))
        if not paths:
            raise ValueError(f'No diagnostic cases in {root}')
        for path in paths:
            doc = json.loads(path.read_text())
            req, res = doc['request'], doc['response']
            native = tokenizer.apply_chat_template(req['messages'], tokenize=True,
                add_generation_prompt=True, **req.get('chat_template_kwargs', {}))
            if isinstance(native, Mapping):
                native = native['input_ids']
            if not isinstance(native, list) or not all(isinstance(x, int) for x in native):
                raise TypeError('Expected one flat native input_ids sequence')
            actual = res.get('prompt_token_ids')
            same = isinstance(actual, list) and native == actual
            cases.append({'artifact':str(path), 'artifact_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'index':doc['index'], 'variant':doc['variant'],
                'semantic_messages_sha256':digest(req['messages']),
                'native_token_count':len(native), 'actual_token_count':len(actual) if actual is not None else None,
                'native_tokens_sha256':digest(native), 'actual_tokens_sha256':digest(actual),
                'token_ids_equal':same,
                'usage_count_equal':res.get('usage', {}).get('prompt_tokens') == len(native)})
    grouped = {}
    for case in cases:
        grouped.setdefault(case['semantic_messages_sha256'], set()).add(case['actual_tokens_sha256'])
    report = {'scope':'prompt identity only; not model arithmetic or quality validation',
        'cases':cases, 'count':len(cases),
        'token_mismatches':sum(not x['token_ids_equal'] for x in cases),
        'usage_mismatches':sum(not x['usage_count_equal'] for x in cases),
        'same_messages_different_actual_token_sequences':sum(len(v)>1 for v in grouped.values())}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    args.output.with_suffix('.sha256').write_text(hashlib.sha256(args.output.read_bytes()).hexdigest()+'  '+args.output.name+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='cases'}))
    return int(bool(report['token_mismatches'] or report['usage_mismatches']))


if __name__ == '__main__':
    raise SystemExit(main())

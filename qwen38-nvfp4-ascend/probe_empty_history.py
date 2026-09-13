#!/usr/bin/env python3
"""Diagnostic only: does removing empty historical assistant turns change EOS?

Never writes the dataset or supplies accepted baseline data. This input-policy
change needs separate agreement and matched validation before deployment.
"""
import argparse
import hashlib
import json
from pathlib import Path
from chat_benchmark import post_json


def drop_empty_assistant(messages):
    return [dict(m) for m in messages
            if not (m['role'] == 'assistant' and not m['content'].strip())]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base-url', required=True)
    ap.add_argument('--source-probe', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    rows = []
    sources = sorted(args.source_probe.glob('*-greedy_repeat_a.json'))
    if len(sources) != 12:
        raise ValueError('Expected frozen twelve-case diagnostic population')
    for source in sources:
        old = json.loads(source.read_text())
        original = old['request']['messages']
        for variant, messages in [('original', original), ('drop_empty_assistant', drop_empty_assistant(original))]:
            payload = dict(model=old['request']['model'], messages=messages,
                temperature=0, seed=1024, max_tokens=64, stream=False,
                return_token_ids=True, chat_template_kwargs={'enable_thinking':False},
                cache_salt=f'{args.output.name}:{old["index"]}:{variant}')
            record = {'index':old['index'], 'variant':variant, 'request':payload,
                'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                'removed_messages':len(original)-len(messages)}
            try:
                with post_json(args.base_url.rstrip('/')+'/v1/chat/completions', payload, 300) as response:
                    record['response'] = json.load(response)
                choice = record['response']['choices'][0]
                rows.append({'index':old['index'], 'variant':variant,
                    'removed_messages':record['removed_messages'],
                    'empty':not bool(choice['message'].get('content')),
                    'finish_reason':choice.get('finish_reason'), 'token_ids':choice.get('token_ids')})
            except Exception as exc:
                record['error'] = repr(exc)
                rows.append({'index':old['index'], 'variant':variant, 'error_type':type(exc).__name__})
            path = args.output/f'{old["index"]}-{variant}.json'
            path.write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n')
            path.with_suffix('.sha256').write_text(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+path.name+'\n')
    summary = args.output/'summary.json'
    summary.write_text(json.dumps({'scope':'input-policy diagnostic, not baseline or quality acceptance', 'cases':rows}, indent=2)+'\n')
    summary.with_suffix('.sha256').write_text(hashlib.sha256(summary.read_bytes()).hexdigest()+'  summary.json\n')
    return int(any('error_type' in row for row in rows))


if __name__ == '__main__':
    raise SystemExit(main())

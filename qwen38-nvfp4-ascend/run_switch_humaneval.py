"""HumanEval-instruct generation only; generated code is NEVER executed here.

Uses pinned lm-eval v0.4.13 instruct prompt/gen_prefix and fence extraction.
The resulting samples.jsonl goes to run_humaneval_sandbox.sh separately.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
from offline_standard_data import read_rows


def messages(prompt):
    return [dict(role='user', content='Write a solution to the following problem and make sure that it passes the tests:\n```python\n'+prompt+'\n```\n'),
            dict(role='assistant', content='Here is the completed function:\n```python\n'+prompt+'\n')]


def completion(text):
    return text.split('```', 1)[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data-root', required=True)
    ap.add_argument('--tokenizer', required=True)
    ap.add_argument('--model', required=True)
    ap.add_argument('--base-url', required=True)
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--limit', type=int, default=164)
    ap.add_argument('--preflight-only', action='store_true')
    args = ap.parse_args()
    if not 1 <= args.limit <= 164:
        ap.error('limit must be 1..164')
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, local_files_only=True, trust_remote_code=False)
    rows = read_rows(args.data_root, 'humaneval')['test'][:args.limit]
    args.output.mkdir(parents=True, exist_ok=False)
    samples = []
    for row in rows:
        rendered = tokenizer.apply_chat_template(messages(row['prompt']), tokenize=False,
            add_generation_prompt=False, continue_final_message=True, enable_thinking=False)
        payload = dict(model=args.model, prompt=tokenizer.encode(rendered, add_special_tokens=False),
            temperature=0, seed=1024, max_tokens=1024,
            stop=['\nclass', '\ndef', '\n#', '\nif', '\nprint'])
        record = dict(task_id=row['task_id'], request=payload,
            rendered_prompt_sha256=hashlib.sha256(rendered.encode()).hexdigest())
        path = args.output/(row['task_id'].replace('/', '-')+'.json')
        try:
            if not args.preflight_only:
                req = urllib.request.Request(args.base_url, data=json.dumps(payload).encode(),
                    headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(req, timeout=300) as response:
                    result = json.load(response)
                record['response'] = result
                text = result['choices'][0]['text']
                if not isinstance(text, str):
                    raise ValueError('Missing text completion')
                samples.append(dict(task_id=row['task_id'], completion=completion(text)))
        except Exception as exc:
            record['error'] = repr(exc)
            raise
        finally:
            path.write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n')
            path.with_suffix('.sha256').write_text(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+path.name+'\n')
    if not args.preflight_only:
        path = args.output/'samples.jsonl'
        path.write_text(''.join(json.dumps(s, ensure_ascii=False)+'\n' for s in samples))
        path.with_suffix('.sha256').write_text(hashlib.sha256(path.read_bytes()).hexdigest()+'  samples.jsonl\n')
    print(json.dumps({'scope':'render preflight' if args.preflight_only else 'generation only; not pass@1',
                      'samples':len(rows), 'output':str(args.output)}))


if __name__ == '__main__':
    main()

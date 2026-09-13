"""Bounded diagnostic: compare standard MMLU choice rankings to next-token scores."""
import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path


def factor(pairs):
    contexts = [x[0] for x in pairs]
    if len(pairs) != 4 or any(x != contexts[0] for x in contexts):
        raise ValueError('Expected four choices with identical encoded contexts')
    tails = [x[1] for x in pairs]
    shared = []
    for tokens in zip(*tails):
        if len(set(tokens)) != 1:
            break
        shared.append(tokens[0])
    residual = [t[len(shared):] for t in tails]
    if any(len(t) != 1 for t in residual) or len({t[0] for t in residual}) != 4:
        raise ValueError('Choices do not reduce to four unique single tokens')
    return contexts[0] + shared, [t[0] for t in residual]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True, type=Path)
    p.add_argument('--tokenizer', required=True)
    p.add_argument('--model', required=True)
    p.add_argument('--base-url', required=True)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    from no_thinking_api import NoThinkingCompletions
    lm = NoThinkingCompletions(model=args.model, tokenizer=args.tokenizer,
         tokenizer_backend='huggingface', tokenized_requests=True,
         base_url=args.base_url+'/v1/completions', max_length=40960,
         max_gen_toks=4096, trust_remote_code=False, batch_size=1)
    source = json.loads(args.source.read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    records = []
    for task, samples in source['samples'].items():
        if not task.startswith('mmlu_'):
            continue
        for sample in samples:
            pairs = [lm._encode_pair(*pair) for pair in sample['arguments']]
            prompt, labels = factor(pairs)
            if len(prompt) >= 40960:
                raise ValueError('Would truncate; diagnostic rejected')
            payload = dict(model=args.model, prompt=prompt, max_tokens=1,
                temperature=0, seed=1024, logprobs=20, echo=False,
                return_tokens_as_token_ids=True)
            record = dict(task=task, doc_id=sample['doc_id'],
                prompt_tokens=len(prompt), label_token_ids=labels, request=payload,
                standard_loglikelihoods=[x[0][0] for x in sample['resps']])
            start = time.monotonic()
            req = urllib.request.Request(args.base_url+'/v1/completions',
                data=json.dumps(payload).encode(), headers={'Content-Type':'application/json'})
            try:
                with urllib.request.urlopen(req, timeout=300) as response:
                    record['response'] = json.load(response)
                tops = record['response']['choices'][0]['logprobs']['top_logprobs'][0]
                keys = ['token_id:'+str(t) for t in labels]
                record['all_labels_present'] = all(k in tops for k in keys)
                if record['all_labels_present']:
                    scores = [tops[k] for k in keys]
                    record['next_token_logprobs'] = scores
                    a = record['standard_loglikelihoods']
                    record['same_winner'] = max(range(4), key=a.__getitem__) == max(range(4), key=scores.__getitem__)
                    record['relative_logprob_max_abs_diff'] = max(abs((a[i]-a[0])-(scores[i]-scores[0])) for i in range(4))
            except Exception as exc:
                record['error'] = repr(exc)
            record['elapsed_seconds'] = time.monotonic()-start
            path = args.output/(task+'-'+str(sample['doc_id'])+'.json')
            path.write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n')
            record['artifact_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            records.append({k:v for k,v in record.items() if k not in ('request','response')})
    summary = dict(scope='diagnostic only, not accepted replacement or full quality',
                   source_sha256=hashlib.sha256(args.source.read_bytes()).hexdigest(),
                   cases=records)
    (args.output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()

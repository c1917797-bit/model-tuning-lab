"""Pinned offline-data MMLU/GSM8K scoring; model service must already be owned.

HumanEval remains a separate generation and sandbox execution stage.
Raw samples go to the caller's external artifact directory, never Git.
"""
import argparse
from functools import partial
import hashlib
import json
from pathlib import Path
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--harness', required=True, type=Path)
    ap.add_argument('--data-root', required=True)
    ap.add_argument('--tokenizer', required=True)
    ap.add_argument('--model', required=True)
    ap.add_argument('--base-url', required=True)
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--tasks', nargs='+', required=True)
    ap.add_argument('--limit', type=int)
    ap.add_argument('--concurrency', type=int, choices=(1, 5, 8, 16), default=1)
    ap.add_argument('--preflight-only', action='store_true')
    args = ap.parse_args()
    if 'mmlu' in args.tasks:
        subjects = sorted(p.stem for p in (args.harness/'lm_eval/tasks/mmlu/default').glob('mmlu_*.yaml'))
        if len(subjects) != 57:
            ap.error('Full MMLU requires exactly 57 pinned subject configurations')
        args.tasks = [task for name in args.tasks for task in (subjects if name == 'mmlu' else [name])]
    if len(set(args.tasks)) != len(args.tasks):
        ap.error('Duplicate quality tasks are not allowed')
    if args.limit is not None and args.limit < 1:
        ap.error('limit must be a positive sample count')
    if args.output.exists():
        ap.error('output must be a fresh artifact directory')
    sys.path.insert(0, str(args.harness))
    import datasets
    def no_hub(*a, **kw):
        raise RuntimeError('Unexpected Hub dataset access')
    datasets.load_dataset = no_hub
    from lm_eval.tasks._yaml_loader import load_yaml
    from lm_eval.api.task import ConfigurableTask
    import offline_standard_data as local
    tasks = []
    for name in args.tasks:
        if name == 'gsm8k':
            path = args.harness / 'lm_eval/tasks/gsm8k/gsm8k.yaml'
            provider = partial(local.gsm8k, data_root=args.data_root)
        elif name.startswith('mmlu_') and all(c.isalnum() or c == '_' for c in name):
            path = args.harness / 'lm_eval/tasks/mmlu/default' / (name+'.yaml')
            provider = partial(local.mmlu, data_root=args.data_root, subject=name[5:])
        else:
            ap.error('Only exact MMLU subject names and gsm8k are supported')
        config = load_yaml(path, resolve_func=True)
        config['custom_dataset'] = provider
        # Individual MMLU YAMLs do not set num_fewshot. Pin the promised
        # protocol explicitly instead of relying on the task default (zero).
        config['num_fewshot'] = 5
        tasks.append(ConfigurableTask(config=config))
    if any(task.get_config('num_fewshot') != 5 for task in tasks):
        raise RuntimeError('All standard text tasks must use exactly five shots')
    args.output.mkdir(parents=True)
    if args.preflight_only:
        doc = {'scope':'task construction only; no model requests',
               'tasks':args.tasks, 'test_rows':[len(t.test_docs()) for t in tasks],
               'fewshot_counts':[t.get_config('num_fewshot') for t in tasks]}
    else:
        from no_thinking_api import NoThinkingCompletions
        from lm_eval import simple_evaluate
        class SeededCompletions(NoThinkingCompletions):
            def _create_payload(self, *a, **kw):
                payload = super()._create_payload(*a, **kw)
                payload['seed'] = 1024
                return payload
        lm = SeededCompletions(model=args.model, tokenizer=args.tokenizer,
            tokenizer_backend='huggingface', tokenized_requests=True,
            base_url=args.base_url, max_length=40960, max_gen_toks=4096,
            trust_remote_code=False, batch_size=1, num_concurrent=args.concurrency)
        doc = simple_evaluate(model=lm, tasks=tasks, limit=args.limit,
            use_cache=str(args.output/'response_cache'),
            log_samples=True, apply_chat_template=True,
            random_seed=1024, numpy_random_seed=1024, torch_random_seed=1024,
            fewshot_random_seed=1024, bootstrap_iters=1000)
        if doc is None:
            raise RuntimeError('Evaluator returned no result')
        if any(doc.get('n-shot', {}).get(name) != 5 for name in args.tasks):
            raise RuntimeError('Actual evaluation shot counts violated the protocol')
    doc['switch_run_protocol'] = {'tasks':args.tasks, 'concurrency':args.concurrency,
        'limit':args.limit, 'model':args.model, 'tokenizer':args.tokenizer,
        'seed':1024, 'num_fewshot':5, 'enable_thinking':False, 'max_length':40960,
        'max_gen_toks':4096, 'batch_size':1}
    path = args.output/'results.json'
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2, default=str)+'\n')
    path.with_suffix('.sha256').write_text(hashlib.sha256(path.read_bytes()).hexdigest()+'  results.json\n')
    print(json.dumps({'artifact':str(path), 'scope':'preflight' if args.preflight_only else 'model scoring',
                      'limit':args.limit, 'tasks':args.tasks}))


if __name__ == '__main__':
    main()

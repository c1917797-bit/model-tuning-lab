#!/usr/bin/env python3
"""One full performance repetition against an already-owned, validated service.

No container operations. The lifecycle owner supplies the current service's
32-row canary, keeps its resource lease, and executes arms in AB/BA/AB order.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from chat_benchmark import report_valid

DATA_SHA = 'ec22de93e406d6c0706a8bd38a1ace12a74d04f503daf3a7f3577daf9a62b2e2'
ORDER = (1, 16, 5, 8)


def validate_report(report, model, concurrency, repeat, count):
    expected = {'schema': 'qwen-switch-chat-natural-eos/v4', 'model': model,
                'dataset_sha256': DATA_SHA, 'concurrency': concurrency,
                'repeat_index': repeat, 'requests': count, 'completed': count,
                'seed': 1024, 'max_output_tokens': 4096,
                'chat_template_kwargs': {'enable_thinking': False}}
    if any(report.get(k) != v for k, v in expected.items()) or not report_valid(report):
        raise ValueError('Performance progression gate failed; preserve this cell')


def command(args, concurrency, output):
    return [sys.executable, str(Path(__file__).with_name('chat_benchmark.py')),
            '--base-url', args.base_url, '--model', args.model,
            '--dataset', str(args.dataset), '--dataset-sha256', DATA_SHA,
            '--concurrency', str(concurrency), '--repeat-index', str(args.repeat),
            '--limit', '0', '--seed', '1024', '--max-output-tokens', '4096',
            '--timeout', '2400', '--cache-salt-prefix', args.output.name,
            '--output', str(output)]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base-url', required=True)
    ap.add_argument('--model', required=True)
    ap.add_argument('--dataset', type=Path, required=True)
    ap.add_argument('--canary', type=Path, required=True)
    ap.add_argument('--repeat', type=int, choices=(1, 2, 3), required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    validate_report(json.loads(args.canary.read_text()), args.model, 1, 1, 32)
    if hashlib.sha256(args.dataset.read_bytes()).hexdigest() != DATA_SHA:
        raise ValueError('Dataset identity changed')
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = {'scope': 'normalized supplement: one arm, one repetition; not original or complete paired matrix',
                'model': args.model, 'repeat': args.repeat, 'order': ORDER,
                'canary_sha256': hashlib.sha256(args.canary.read_bytes()).hexdigest(),
                'benchmark_sha256': hashlib.sha256(Path(__file__).with_name('chat_benchmark.py').read_bytes()).hexdigest(),
                'cells': [], 'state': 'running'}
    manifest_path = args.output / 'manifest.json'
    def save():
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    save()
    try:
        for concurrency in ORDER:
            result = args.output / f'c{concurrency}.json'
            argv = command(args, concurrency, result)
            with result.with_suffix('.log').open('w') as log:
                subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT, check=True)
            validate_report(json.loads(result.read_text()), args.model, concurrency, args.repeat, 357)
            rows = result.with_suffix('.rows.jsonl')
            manifest['cells'].append({'concurrency': concurrency, 'argv': argv,
                'summary_sha256': hashlib.sha256(result.read_bytes()).hexdigest(),
                'rows_sha256': hashlib.sha256(rows.read_bytes()).hexdigest()})
            save()
        manifest['state'] = 'passed'
    except BaseException:
        manifest['state'] = 'failed'
        raise
    finally:
        save()
        manifest_path.with_suffix('.sha256').write_text(
            hashlib.sha256(manifest_path.read_bytes()).hexdigest() + '  manifest.json\n')


if __name__ == '__main__':
    main()

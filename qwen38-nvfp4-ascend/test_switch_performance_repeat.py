#!/usr/bin/env python3
"""Dependency-free progression and fixed-protocol checks; no model requests."""
from pathlib import Path
from types import SimpleNamespace
from run_switch_performance_repeat import DATA_SHA, ORDER, command, validate_report

report = dict(schema='qwen-switch-chat-natural-eos/v4', model='fixture',
              dataset_sha256=DATA_SHA, concurrency=1, repeat_index=1,
              requests=32, completed=32, seed=1024, max_output_tokens=4096,
              chat_template_kwargs={'enable_thinking': False}, errors=0,
              prompt_token_mismatches=0, reasoning_seen_requests=0,
              finish_reasons={'stop': 32}, empty_content_responses=0,
              whitespace_only_content_responses=0)
validate_report(report, 'fixture', 1, 1, 32)
for key, bad in [('model', 'wrong'), ('dataset_sha256', 'wrong'),
                 ('requests', 31), ('completed', 31), ('seed', 0),
                 ('max_output_tokens', 64), ('concurrency', 8),
                 ('repeat_index', 2), ('schema', 'v3'), ('errors', 1),
                 ('empty_content_responses', 1), ('reasoning_seen_requests', 1),
                 ('finish_reasons', {'length': 32})]:
    try:
        validate_report(dict(report, **{key: bad}), 'fixture', 1, 1, 32)
    except ValueError:
        pass
    else:
        raise AssertionError(f'accepted bad {key}')
args = SimpleNamespace(base_url='http://127.0.0.1:10010', model='fixture',
                       dataset=Path('/private/data'), repeat=3, output=Path('/private/run'))
for c in ORDER:
    argv = command(args, c, Path('/private/result.json'))
    assert argv[argv.index('--limit')+1] == '0'
    assert argv[argv.index('--concurrency')+1] == str(c)
    assert argv[argv.index('--repeat-index')+1] == '3'
    assert argv[argv.index('--max-output-tokens')+1] == '4096'
assert set(ORDER) == {1, 5, 8, 16}
print('PASS: strict canary identity/validity, full dataset, four concurrency cells')

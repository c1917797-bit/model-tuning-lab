"""Dependency-free SSE accounting regression tests; no requests or model calls."""
import json
import chat_benchmark as bench


class Stream:
    def __init__(self, events):
        self.events = events

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def __iter__(self):
        for event in self.events:
            yield ('data: ' + json.dumps(event) + '\n').encode()
        yield b'data: [DONE]\n'


def run(events, tokens=3):
    events = list(events) + [
        {'choices': [{'delta': {}, 'finish_reason': 'stop'}]},
        {'choices': [], 'usage': {'prompt_tokens': 10, 'completion_tokens': tokens}},
    ]
    bench.post_json = lambda *args: Stream(events)
    ticks = iter([1.0, 2.0, 3.0])
    bench.time.perf_counter = lambda: next(ticks)
    return bench.request_one('http://unused', 'fixture', [], 32, 10, False, 1024, 5, 'test')


def main():
    good = run([{'choices': [{'delta': {'role': 'assistant'}}]},
                {'choices': [{'delta': {'content': 'answer'}}]}])
    assert good['ttft_ms'] == 1000 and good['tpot_ms'] == 500
    assert good['response_text'] == 'answer' and good['output_nonwhitespace']
    assert good['prompt_token_match'] and len(good['stream_events']) == 4
    empty = run([{'choices': [{'delta': {'role': 'assistant'}}]}])
    assert empty['ttft_ms'] is None and empty['tpot_ms'] is None
    assert not empty['output_nonempty'] and empty['finish_reason'] == 'stop'
    assert empty['stream_events']  # failed semantic output remains auditable
    whitespace = run([{'choices': [{'delta': {'content': '  '}}]}])
    assert whitespace['output_nonempty'] and not whitespace['output_nonwhitespace']
    one = run([{'choices': [{'delta': {'content': 'A'}}]}], tokens=1)
    assert one['tpot_ms'] is None
    for field in ['reasoning', 'reasoning_content']:
        row = run([{'choices': [{'delta': {field: 'hidden'}}]}])
        assert row['reasoning_seen'] and not row['output_nonempty']
    try:
        run([{'choices': [{'delta': {'content': 'A'}}]}], tokens=0)
    except RuntimeError:
        pass
    else:
        raise AssertionError('missing positive token usage was accepted')
    assert bench.summarize([]) is None
    report = dict(requests=357, completed=357, errors=0, prompt_token_mismatches=0,
                  reasoning_seen_requests=0, finish_reasons={'stop':357},
                  empty_content_responses=0, whitespace_only_content_responses=0)
    assert bench.report_valid(report)
    for field in ['errors', 'prompt_token_mismatches', 'reasoning_seen_requests',
                  'empty_content_responses', 'whitespace_only_content_responses']:
        assert not bench.report_valid(dict(report, **{field: 1})), field
    assert not bench.report_valid(dict(report, empty_content_responses=92))
    assert not bench.report_valid(dict(report, completed=356))
    assert not bench.report_valid(dict(report, finish_reasons={'stop':355, 'length':2}))
    print('PASS: content/role/finish/usage, empty, whitespace, one-token, reasoning aliases, invalid usage')


if __name__ == '__main__':
    main()

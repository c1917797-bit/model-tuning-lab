import unittest
from independent_stream_metrics import measure_stream

class StreamMetricsTests(unittest.TestCase):
    def lines(self):
        return [b'data: {"choices":[{"index":0,"text":"","finish_reason":null}]}',
                b'data: {"choices":[{"index":0,"text":"hello","finish_reason":null}]}',
                b'data: {"choices":[{"index":0,"text":" world","finish_reason":"length"}]}',
                b'data: {"choices":[],"usage":{"completion_tokens":1024,"prompt_tokens":32768}}',
                b'data: [DONE]']
    def test_authoritative_usage_not_sse_chunk_count(self):
        ticks=iter([2.,4.]);r=measure_stream(self.lines(),started=1.,clock=lambda:next(ticks))
        self.assertEqual(r["ttft_ms"],1000.)
        self.assertEqual(r["completion_tokens"],1024)
        self.assertEqual(r["tpot_ms"],2000/1024)
        self.assertEqual(r["text"],"hello world")
    def test_missing_terminal_or_usage_rejected(self):
        for lines in (self.lines()[:-1],self.lines()[:3]+[self.lines()[-1]]):
            with self.assertRaises(ValueError):measure_stream(lines,started=1.,clock=lambda:2.)
    def test_clock_reversal_rejected(self):
        with self.assertRaises(ValueError):measure_stream(self.lines(),started=3.,clock=lambda:2.)

if __name__=="__main__":unittest.main()

"""Actual-image eager event binding; runtime qualification remains mandatory.

No backend imports or device initialization occur merely by importing this file.
"""
import hashlib
import inspect
from pathlib import Path

STREAMS_SHA256 = '241741b356db5006797dbec119007afb33b73b0e1753bfb06ab27c989c5bfac4'


class EventBackend:
    def __init__(self, torch, torch_npu):
        streams = torch_npu.npu.streams
        path = Path(inspect.getsourcefile(streams.Event)).resolve(strict=True)
        if hashlib.sha256(path.read_bytes()).hexdigest() != STREAMS_SHA256:
            raise RuntimeError('actual image Event source changed')
        self.torch, self.streams = torch, streams
        self.identity = {'streams_source': str(path), 'sha256': STREAMS_SHA256}

    def current_key(self):
        stream = self.torch.npu.current_stream()
        if not isinstance(stream, self.streams.Stream):
            raise TypeError('actual current_stream type not qualified')
        pointer = stream._as_parameter_
        # ctypes represents the actual native zero handle as None. Preserve the
        # original ABI handle rather than fabricating a nonzero requirement.
        if int(pointer.value or 0) != int(stream.npu_stream):
            raise RuntimeError('actual raw stream handle unavailable')
        return (stream.npu_stream, str(stream.device))

    def record(self, expected_key):
        stream = self.torch.npu.current_stream()
        if self.current_key() != expected_key:
            raise RuntimeError('foreign launch stream changed; retain buffers')
        event = self.streams.Event(enable_timing=False, blocking=False,
                                   interprocess=False)
        event.record(stream)
        if self.current_key() != expected_key:
            raise RuntimeError('event stream changed; retain buffers')
        return event

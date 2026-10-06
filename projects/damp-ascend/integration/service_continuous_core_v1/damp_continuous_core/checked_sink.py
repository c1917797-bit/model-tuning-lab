"""CHECKED-only fresh status/output verification, explicitly outside formal timing."""
from .core import require

def validate_status_rows(values, prefills):
    require(type(prefills) is int and 1 <= prefills <= 16, "actual prefill P1..16")
    require(isinstance(values, list) and len(values) == prefills*96+16 and
            all(type(x) is int for x in values), "full INT32 guarded status required")
    require(values[:8] == [0x13579bdf]*8 and values[-8:] == [0x13579bdf]*8,
            "selected-pack status guards changed")
    rows = [tuple(values[i:i+8]) for i in range(8, len(values)-8, 8)]
    require(len(rows) == prefills*12, "status must retain every head")
    for row in rows:
        success, error, groups, certified, fallback, count, reserved0, reserved1 = row
        require((success, error, groups, count, reserved0, reserved1) ==
                (1, 0, 4, 16384, 0, 0) and
                certified >= 0 and fallback >= 0 and certified+fallback == 16384,
                "prefill-pack partial numerical/state failure: retire; NEVER retry")
    return tuple(rows)

class CheckedSink:
    def __init__(self, torch, save_observation, enabled=False, formal_perf=False):
        require(enabled is True and formal_perf is False,
                "checked sink is default OFF and never instrumentation-free performance")
        self.t, self.save = torch, save_observation
    def pack_status(self, status, prefix, turn):
        # A CPU checked seam on purpose: not hidden in a formal perf claim.
        # The caller owns poisoned-D2H error retention and slot/worker retirement.
        values = status.detach().cpu().tolist()
        self.save({"stage":"selected_pack_status", "prefix":prefix,
                   "prefill_slots":list(turn.prefill_slots), "raw":values})
        require(status.dtype == self.t.int32 and status.ndim == 1, "status tensor ABI")
        validate_status_rows(values, len(turn.prefill_rows))
    def output(self, output, prefix, turn):
        require(tuple(output.shape) == (1, turn.starts[-1], 12, 128) and
                output.dtype == self.t.bfloat16, "native BF16 output shape drift")
        # Explicit checked sync, not task-level accuracy or hidden benchmark cost.
        require(bool(self.t.isfinite(output).all().item()), "nonfinite core output: retire")

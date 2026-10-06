"""NEW opt-in actual GDN core orchestration; no import-time framework activity."""
from dataclasses import dataclass
from continuous_metadata_v1.contract import Turn

class Unsupported(RuntimeError):
    pass

def require(value, reason):
    if not value:
        raise Unsupported(reason)

@dataclass(frozen=True)
class Phase:
    prefix: str
    mode: str
    decode_requests: int
    prefill_requests: int
    decode_tokens: int
    total_tokens: int
    prefill_slots: tuple
    continuation_positions: tuple

def phase(prefix, turn):
    require(isinstance(turn, Turn), "frozen continuous Turn required")
    require(isinstance(prefix, str) and prefix and 1 <= len(turn.rows) <= 16,
            "real source-bound turn required")
    n = turn.num_decodes
    require(type(n) is int and 0 <= n <= len(turn.rows) and
            type(turn.decode_tokens) is int and turn.decode_tokens == n,
            "actual decode prefix T must be request count, never padded16")
    require(len(turn.starts) == len(turn.rows)+1 and turn.starts[0] == 0 and
            all(type(x) is int for x in turn.starts) and
            all(turn.starts[i+1]-turn.starts[i] == row.query_tokens and
                type(row.query_tokens) is int and row.query_tokens > 0
                for i, row in enumerate(turn.rows)), "native actual token boundaries required")
    require(tuple(turn.decode_rows) == tuple(turn.rows[:n]) and
            tuple(turn.prefill_rows) == tuple(turn.rows[n:]) and
            turn.starts[n] == n and
            all(r.query_tokens == 1 and r.computed_tokens > 0 for r in turn.decode_rows),
            "native decode row/token order must be preserved")
    require(tuple(turn.prefill_slots) == tuple(r.slot for r in turn.prefill_rows) and
            tuple(turn.prefill_starts) == tuple(x-n for x in turn.starts[n:]) and
            tuple(turn.has_initial) == tuple(r.computed_tokens > 0 for r in turn.prefill_rows) and
            all(type(x) is bool for x in turn.has_initial), "native exact prefill suffix identities")
    return Phase(prefix, turn.mode, n, len(turn.prefill_rows), n, turn.starts[-1],
                 tuple(turn.prefill_slots), tuple(i for i, b in enumerate(turn.has_initial) if b))

class ContinuousCore:
    """Caller provides FULL pre-writer actual cache and native metadata admission.
    Backend is an explicitly injected new-namespace op adapter, never torch.ops
    reassignment. No public install() bypasses pending receipts.
    """
    def __init__(self, backend, safety, enabled=False):
        require(enabled is True, "continuous core default OFF")
        self.backend, self.safety = backend, safety

    def __call__(self, layer, mixed_qkv, b, a, core_attn_out):
        md = self.backend.metadata(layer.prefix)
        if md is None:
            return  # identical native profile behavior, no persistent writer
        turn = self.safety.require_layer(layer.prefix, md)
        p = phase(layer.prefix, turn)
        # All layers' shared FA/GDN footprints and early zeroing must have been
        # admitted BEFORE any layer conv writes. No thin flag or hot D2H proof.
        self.safety.before_writer(layer.prefix, turn, md)
        self.backend.require_cold(layer, turn)
        self.safety.writer_started(layer.prefix)
        try:
            convolved = self.backend.conv(layer, md, turn, mixed_qkv)
            qkv = self.backend.project(layer, convolved)
            gating = self.backend.gating(layer, a, b, p.total_tokens)
            decode_out = (self.backend.decode(layer, md, turn, qkv, gating)
                          if p.decode_requests else None)
            prefill_out = (self.backend.prefill(layer, md, turn, qkv, gating,
                                               p.continuation_positions)
                           if p.prefill_requests else None)
            out = self.backend.merge(decode_out, prefill_out)
            self.backend.validate_output(out, layer.prefix, turn)
            self.backend.publish(core_attn_out, out, p.total_tokens)
            self.safety.layer_succeeded(layer.prefix)
        except BaseException as error:
            # No native fallback or replay of partially updated groups/layers.
            self.safety.retire(layer.prefix, repr(error), retry_allowed=False)
            raise

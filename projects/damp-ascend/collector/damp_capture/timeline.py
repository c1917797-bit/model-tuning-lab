"""Anchor-after-update followed by exactly the NEXT H log-decay inputs."""
import math
from .contract import require

class Timeline:
    def __init__(self, anchors, horizon, heads=12):
        self.anchors, self.horizon, self.heads = tuple(anchors), horizon, heads
        self.step, self.pending, self.finished = 0, {}, {}

    def advance(self, log_decay):
        require(len(log_decay) == self.heads and all(math.isfinite(g) and g <= 1e-6
                for g in log_decay), "invalid log decay")
        self.step += 1
        closed = []
        for anchor, rows in list(self.pending.items()):
            rows.append(tuple(float(g) for g in log_decay))
            if len(rows) == self.horizon:
                self.finished[anchor] = tuple(rows)
                closed.append(anchor)
                del self.pending[anchor]
        is_anchor = self.step in self.anchors
        if is_anchor:
            self.pending[self.step] = []
        return is_anchor, closed

    @property
    def complete(self):
        return len(self.finished) == len(self.anchors)

def decay_weights(rows):
    require(bool(rows), "empty future")
    heads = len(rows[0])
    logs, values = [0.0] * heads, [[1.0] for _ in range(heads)]
    for row in rows:
        require(len(row) == heads, "ragged future")
        for h, g in enumerate(row):
            require(math.isfinite(g) and g <= 1e-6, "invalid log decay")
            logs[h] += 2 * g
            values[h].append(math.exp(logs[h]))
    return [math.fsum(v) for v in values]

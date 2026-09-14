"""Append-only, process-safe JSONL evidence for Tail-Replay canaries."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
from typing import Any


def emit_event(event: str, **fields: Any) -> None:
    path = os.environ.get("MST_TAIL_REPLAY_EVIDENCE_FILE")
    if not path:
        return
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "tail-replay-ascend-runtime-event/v1",
        "event": event,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(),
        "hostname": socket.gethostname(),
        **fields,
    }
    data = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)

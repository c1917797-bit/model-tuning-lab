"""Bounded append-only worker activation evidence."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


def emit(path: Path, event: str, **payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "schema": "mst.dasc.activation/v1",
        "event": event,
        "time_ns": time.time_ns(),
        "pid": os.getpid(),
        "rank": os.getenv("RANK"),
        "local_rank": os.getenv("LOCAL_RANK"),
        **payload,
    }
    data = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)

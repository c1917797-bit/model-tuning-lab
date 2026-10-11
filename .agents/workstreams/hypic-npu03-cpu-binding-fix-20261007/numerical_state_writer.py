"""Exclusive, bounded per-worker raw snapshots; sealing is not device proof."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import threading


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def exclusive(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


class RawWriter:
    def __init__(self, parent, *, metadata, max_events=32, max_bytes=64*1024*1024):
        parent = Path(parent)
        if (not parent.is_absolute() or not parent.is_dir() or parent.is_symlink()
                or parent.resolve() != parent):
            raise ValueError("existing absolute nonsymlink raw root required")
        rank, pid = metadata["rank"], metadata["pid"]
        if (type(rank) is not int or rank not in range(4)
                or type(pid) is not int or pid <= 0
                or not metadata.get("request_id")
                or type(max_events) is not int or not 1 <= max_events <= 32
                or type(max_bytes) is not int or not 1 <= max_bytes <= 64*1024*1024):
            raise ValueError("invalid writer identity/bounds")
        self.metadata = json.loads(encode(metadata))
        self.path = parent / ("rank-%d-pid-%d" % (rank, pid))
        self.path.mkdir(mode=0o700)
        self.max_events, self.max_bytes = max_events, max_bytes
        self.files, self.bytes = [], 0
        self.closed = self.failed = False
        self.lock = threading.Lock()

    def __call__(self, event):
        with self.lock:
            if self.closed or self.failed:
                raise RuntimeError("writer is closed or failed")
            try:
                if any(event.get(key) != self.metadata[key]
                       for key in ("request_id", "rank", "pid")):
                    raise ValueError("cross-worker/request event refused")
                raw = encode(event)
                if len(self.files) >= self.max_events or self.bytes+len(raw) > self.max_bytes:
                    raise ValueError("raw writer budget exceeded")
                name = "%04d.json" % len(self.files)
                exclusive(self.path/name, raw)
                self.files.append(dict(name=name, size=len(raw),
                                       sha256=hashlib.sha256(raw).hexdigest()))
                self.bytes += len(raw)
            except Exception:
                self.failed = True
                raise

    def seal(self):
        with self.lock:
            if self.closed or self.failed or not self.files:
                raise RuntimeError("cannot seal closed/failed/empty capture")
            manifest = dict(schema="hypic-state-raw-seal/v1", metadata=self.metadata,
                            files=self.files, bytes=self.bytes,
                            completion_is_not_device_acceptance=True)
            try:
                exclusive(self.path/"SEAL.json", encode(manifest))
                fd = os.open(self.path, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
            except Exception:
                self.failed = True
                raise
            self.closed = True
            return manifest


def read_sealed(path):
    """Verify exact file inventory/digests; caller separately audits provenance."""
    path = Path(path)
    if path.is_symlink() or path.resolve() != path:
        raise ValueError("symlink capture directory refused")
    seal_path = path/"SEAL.json"
    if seal_path.is_symlink() or seal_path.stat().st_size > 1_000_000:
        raise ValueError("invalid seal file")
    manifest = json.loads(seal_path.read_bytes())
    files = manifest["files"]
    if (manifest.get("schema") != "hypic-state-raw-seal/v1"
            or not 1 <= len(files) <= 32):
        raise ValueError("invalid seal")
    if (any(type(item.get("size")) is not int or item["size"] <= 0 for item in files)
            or sum(item["size"] for item in files) > 64*1024*1024):
        raise ValueError("seal byte budget invalid")
    expected = {"SEAL.json"} | {item["name"] for item in files}
    if {p.name for p in path.iterdir()} != expected:
        raise ValueError("raw inventory mismatch")
    events, total = [], 0
    for index, item in enumerate(files):
        if item["name"] != "%04d.json" % index:
            raise ValueError("invalid sequence")
        source = path/item["name"]
        if (source.is_symlink() or item["size"] > 64*1024*1024
                or source.stat().st_size != item["size"]):
            raise ValueError("invalid raw file")
        raw = source.read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError("raw digest mismatch")
        event = json.loads(raw)
        if any(event.get(k) != manifest["metadata"][k]
               for k in ("request_id", "rank", "pid")):
            raise ValueError("raw identity mismatch")
        events.append(event)
        total += len(raw)
    if total != manifest["bytes"] or total > 64*1024*1024:
        raise ValueError("raw byte budget mismatch")
    return manifest, events

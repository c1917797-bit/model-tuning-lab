"""Fail-closed import of an owned MMLU SQLite checkpoint, never a live cache.

This only validates/copies cache evidence. It neither starts a model nor proves
that a caller's identity directory describes the currently running service.
The caller must establish that binding before using the imported cache.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

IDENTITIES = frozenset(("inputs.sha256", "evaluator.sha256",
                       "image.inspect.json", "models.json", "server-profile.json"))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def restore(checkpoint, manifest_sha, identity_dir, destination):
    checkpoint, identity_dir, destination = map(
        Path, (checkpoint, identity_dir, destination))
    manifest_path = checkpoint / "manifest.json"
    if sha(manifest_path) != manifest_sha:
        raise ValueError("Checkpoint manifest identity mismatch")
    manifest = json.loads(manifest_path.read_text())
    if set(manifest.get("identity_files", {})) != IDENTITIES:
        raise ValueError("Incomplete checkpoint identity population")
    for name, expected in manifest["identity_files"].items():
        if sha(checkpoint / name) != expected:
            raise ValueError("Checkpoint identity file corrupted: " + name)
        if sha(identity_dir / name) != expected:
            raise ValueError("Requested run identity differs: " + name)
    source = checkpoint / "response_cache_rank0.db"
    if sha(source) != manifest["cache_sha256"]:
        raise ValueError("Checkpoint cache checksum mismatch")
    # Never modify the source or replace a destination, including dangling links.
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb"):
        pass
    try:
        src = sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)
        dst = sqlite3.connect(str(destination))
        try:
            if src.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise ValueError("Checkpoint SQLite integrity failure")
            count = src.execute("SELECT count(*) FROM unnamed").fetchone()[0]
            if count != manifest["cache_entries"]:
                raise ValueError("Checkpoint cache count mismatch")
            src.backup(dst)
            if dst.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise ValueError("Restored SQLite integrity failure")
            # Compare raw blobs, without deserializing executable pickle data.
            if src.execute("SELECT key,value FROM unnamed ORDER BY key").fetchall() != dst.execute(
                    "SELECT key,value FROM unnamed ORDER BY key").fetchall():
                raise ValueError("Restored cache differs")
        finally:
            dst.close()
            src.close()
        if sha(source) != manifest["cache_sha256"]:
            raise ValueError("Checkpoint changed during restore")
    except Exception:
        # Preserve the failed output for inspection; never reuse it automatically.
        raise
    return {"scope": "cache import only; runtime identity binding still required",
            "checkpoint_manifest_sha256": manifest_sha,
            "cache_entries": count, "destination": str(destination),
            "restored_sha256": sha(destination)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--identity-dir", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(restore(args.checkpoint, args.manifest_sha256,
                             args.identity_dir, args.destination)))


if __name__ == "__main__":
    main()

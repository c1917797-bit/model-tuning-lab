"""Dependency-free positive and corruption tests; no NPU or model requests."""
import json
from pathlib import Path
import sqlite3
import tempfile
from restore_quality_cache import IDENTITIES, restore, sha


def rejected(call):
    try:
        call()
    except (ValueError, FileExistsError):
        return
    raise AssertionError("Expected fail-closed rejection")


with tempfile.TemporaryDirectory(prefix="quality-cache-test-") as temp:
    root = Path(temp)
    snap, identity = root / "snapshot", root / "identity"
    snap.mkdir()
    identity.mkdir()
    hashes = {}
    for name in IDENTITIES:
        (snap / name).write_text("fixture " + name)
        (identity / name).write_bytes((snap / name).read_bytes())
        hashes[name] = sha(snap / name)
    cache = snap / "response_cache_rank0.db"
    db = sqlite3.connect(str(cache))
    db.execute("CREATE TABLE unnamed (key TEXT PRIMARY KEY, value BLOB)")
    db.execute("INSERT INTO unnamed VALUES (?,?)", ("fixture", b"non-executable-fixture"))
    db.commit()
    db.close()
    manifest = {"identity_files": hashes, "cache_sha256": sha(cache), "cache_entries": 1}
    path = snap / "manifest.json"
    path.write_text(json.dumps(manifest))
    digest = sha(path)
    dest = root / "restored.db"
    result = restore(snap, digest, identity, dest)
    assert result["cache_entries"] == 1
    assert sha(cache) == manifest["cache_sha256"]
    rejected(lambda: restore(snap, digest, identity, dest))
    rejected(lambda: restore(snap, "0"*64, identity, root / "wrong-manifest.db"))
    (identity / "models.json").write_text("different model")
    rejected(lambda: restore(snap, digest, identity, root / "wrong-model.db"))
    (identity / "models.json").write_bytes((snap / "models.json").read_bytes())
    (snap / "server-profile.json").write_text("changed profile")
    rejected(lambda: restore(snap, digest, identity, root / "bad-profile.db"))
    (snap / "server-profile.json").write_bytes((identity / "server-profile.json").read_bytes())
    manifest["cache_entries"] = 2
    path.write_text(json.dumps(manifest))
    rejected(lambda: restore(snap, sha(path), identity, root / "wrong-count.db"))
    manifest["cache_entries"] = 1
    path.write_text(json.dumps(manifest))
    with cache.open("ab") as stream:
        stream.write(b"corruption")
    rejected(lambda: restore(snap, sha(path), identity, root / "bad-cache.db"))
print("PASS: import, source preservation, overwrite, manifest, model, profile, count, corruption")

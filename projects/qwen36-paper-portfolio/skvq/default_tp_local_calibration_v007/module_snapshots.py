"""Exact six same-image origin bytes transported to owned calibration output.
No native/library imports. Runtime origin verification stays in library_probe.
Host validation consumes immutable snapshots, not guessed host/guest aliases.
"""
import hashlib,re
from pathlib import Path,PurePosixPath
import common as C
NAMES=("torch","numpy","sklearn","actual_sklearn_KMeans","threadpoolctl","actual_threadpool_info")
MAX_FILE=2*2**20
def original_ref(ref):
    C.need(type(ref)is dict and set(ref)=={"path","bytes","sha256"}and
      type(ref["path"])is str and PurePosixPath(ref["path"]).is_absolute()and
      ".."not in PurePosixPath(ref["path"]).parts and
      type(ref["bytes"])is int and 0<ref["bytes"]<=MAX_FILE and
      type(ref["sha256"])is str and re.fullmatch("[0-9a-f]{64}",ref["sha256"]),
      "strict original guest module identity, no bool/extra/origin/alias")
    return ref
def capture(origins,library_root,packet):
    C.need(type(origins)is dict and set(origins)==set(NAMES),"complete six actual loaded origins")
    library_root=Path(library_root);root=library_root/"module-bytes"
    C.need(library_root.is_dir()and not root.exists()and not root.is_symlink(),
      "one absent module snapshot child of actual owned library output")
    root.mkdir(mode=0o700);modules={};total=0
    for name in NAMES:
        origin=original_ref(origins[name]);path=Path(origin["path"])
        C.need(C.reference(path)==origin,"actual deployed module before snapshot")
        raw=path.read_bytes()
        C.need(len(raw)==origin["bytes"]and hashlib.sha256(raw).hexdigest()==origin["sha256"]and
          C.reference(path)==origin,"immutable entire original module bytes")
        saved=C.atomic().publish_bytes(root/(name+".bin"),raw)
        C.need(saved["bytes"]==origin["bytes"]and saved["sha256"]==origin["sha256"],
          "actual origin bytes copied without source rewriting")
        modules[name]=dict(original_ref=origin,snapshot_ref=saved);total+=len(raw)
    value=dict(schema="skvq.actual-library-origin-byte-snapshots/v1",source_ref=packet,
      helper_ref=C.reference(__file__),snapshot_root=str(root),modules=modules,
      total_snapshot_bytes=total,live_original_files_rechecked=True,
      library_imported_by_transport=False,native_ready=False,model_ready=False)
    return C.publish(root/"ORIGIN_BYTE_SNAPSHOTS.json",value)
def verify(probe,probe_ref,packet):
    C.need(type(probe["actual_modules"])is dict and set(probe["actual_modules"])==set(NAMES),
      "same complete actual fitting module labels")
    root=Path(probe_ref["path"]).parent/"module-bytes"
    ref=probe["actual_module_snapshots_ref"]
    C.need(Path(ref["path"])==root/"ORIGIN_BYTE_SNAPSHOTS.json",
      "sole source-qualified snapshot descriptor under actual library probe")
    value=C.bound(ref)
    C.need(type(value)is dict and set(value)=={"schema","source_ref","helper_ref","snapshot_root","modules",
      "total_snapshot_bytes","live_original_files_rechecked","library_imported_by_transport","native_ready","model_ready"}and
      value["schema"]=="skvq.actual-library-origin-byte-snapshots/v1"and value["source_ref"]==packet and
      value["helper_ref"]==C.reference(__file__)and Path(value["snapshot_root"])==root and
      value["live_original_files_rechecked"]is True and value["library_imported_by_transport"]is False and
      value["native_ready"]is False and value["model_ready"]is False and
      type(value["modules"])is dict and set(value["modules"])==set(NAMES),
      "exact current transport source/owned root/six records, not original-path bypass")
    total=0
    for name in NAMES:
        row=value["modules"][name]
        C.need(type(row)is dict and set(row)=={"original_ref","snapshot_ref"},
          "one original plus immutable snapshot; no extra keys")
        origin=original_ref(row["original_ref"]);saved=row["snapshot_ref"]
        C.need(origin==probe["actual_modules"][name]and type(saved)is dict and
          set(saved)=={"path","bytes","sha256"}and Path(saved["path"])==root/(name+".bin")and
          type(saved["bytes"])is int and saved["bytes"]==origin["bytes"]and
          saved["sha256"]==origin["sha256"]and C.reference(saved["path"])==saved,
          "complete byte/size/SHA and exact original guest path preserved")
        total+=saved["bytes"]
    C.need(type(value["total_snapshot_bytes"])is int and value["total_snapshot_bytes"]==total and
      total<=len(NAMES)*MAX_FILE,"complete bounded snapshot accounting")
    return value

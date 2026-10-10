"""Current 72h source/clock identity; no algorithm authority."""
import hashlib,importlib.util,json,re,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-013")
CUT=1791788425
CLOCK={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/USER_72H_PROTOCOL_20261009.json","bytes":1379,"sha256":"b605d2a01118c4087e3450b3d800ef5bf40f6d0f882c1606a1e9117ed56151d1"}
GIB=2**30;HBM_RESERVE_MIB=3072;EXPECTED=None
def require(value,message):
    if not value:raise ValueError(message)
def reference(path):
    p=Path(path);require(p.is_absolute() and ".." not in p.parts,"exact absolute Ref")
    for q in (p,)+tuple(p.parents):require(not q.is_symlink(),"source symlink rejected")
    require(p.is_file(),"actual ordinary source");h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(2**20),b""):h.update(b)
    return {"path":str(p),"bytes":p.stat().st_size,"sha256":h.hexdigest()}
def checked(value):
    require(type(value)is dict and set(value)=={"path","bytes","sha256"} and type(value["bytes"])is int and
        value["bytes"]>0 and re.fullmatch("[0-9a-f]{64}",value["sha256"]),"strict source 3Ref")
    require(reference(value["path"])==value,"actual entire size/SHA identity");return value
def clock():
    checked(CLOCK)
    return {"protocol_ref":CLOCK,"portfolio_cutoff_epoch":CUT,"observed_epoch":time.time(),
        "old_scope_deadline_utc":"2026-10-09T11:17:31Z","old_scope_remains_expired":True}
def source(expected=None):
    actual=reference(HERE/"SOURCE_MANIFEST.json");expected=expected or EXPECTED
    require(re.fullmatch("[0-9a-f]{64}",expected or "") and actual["sha256"]==expected,"explicit current manifest SHA")
    m=json.loads(Path(actual["path"]).read_bytes())
    require(m["schema"]=="skvq.current72h.preprojection.sources/v1" and m["default_enabled"]is False and
        m["root"]==str(ROOT) and m["clock"]==CLOCK and m["portfolio_cutoff_epoch"]==CUT,"current scope, not old lease")
    require(HERE==ROOT,"installed declared root; local tests are not source admission")
    seen=set()
    for r in m["files"]+m["dependencies"]:
        checked(r);require(r["path"]not in seen,"unique complete source closure");seen.add(r["path"])
    require(len(seen)==m["source_count"] and len(m["files"])==m["own_file_count"],"actual source counts")
    clock();return actual
def configure(expected):
    global EXPECTED
    require(EXPECTED is None,"one current source context");EXPECTED=expected;return source()
def fit(seconds):
    require(type(seconds)is int and seconds>0 and time.time()+seconds<=CUT,"stage fits fixed cutoff")

PROTECTED_REFS=[{"path":"/cache/cch/qwen36-paper-preparation-20261007/sparse/adakv-native-serial-once-v1-016/once_contract.py","bytes":9234,"sha256":"a7e446d79c58672bb77cafaf3968ee4dbbdd70a2b86afcd350065b69338f45bb"},{"path":"/cache/cch/qwen36-paper-preparation-20261007/sparse/adakv-native-serial-once-v1-015/safety_lifecycle.py","bytes":6865,"sha256":"4bbd492809c9ba1922fd3885b101f8cc6fe187884703c21e4a2d44acd1444b75"}]
def protected_module():
    """Load two exact stdlib infrastructure sources; no donor numerical authority."""
    def load(ref,name):
        checked(ref)
        cached=sys.modules.get(name)
        if cached is not None:
            require(getattr(cached,"__file__",None) is not None and reference(cached.__file__)==ref,
                "cached protected namespace must have exact source identity")
            return cached
        spec=importlib.util.spec_from_file_location(name,ref["path"])
        require(spec is not None and spec.loader is not None,"actual explicit protected source loader")
        value=importlib.util.module_from_spec(spec);sys.modules[name]=value
        spec.loader.exec_module(value)
        require(reference(value.__file__)==ref,"loaded protected source exact bytes")
        return value
    original=list(sys.path)
    try:
        sys.path.insert(0,str(Path(PROTECTED_REFS[0]["path"]).parent))
        load(PROTECTED_REFS[0],"once_contract")
        return load(PROTECTED_REFS[1],"_skvq_current_protected_boundary")
    finally:sys.path[:]=original

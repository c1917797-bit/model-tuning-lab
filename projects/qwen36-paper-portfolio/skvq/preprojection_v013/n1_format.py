"""Actual image660 enum qualification, raw-before-gate and independent tiny replay.
No Torch import, no numeric conversion or permissive integer/enum union.
"""
import importlib.util,inspect,json,math,sys
from pathlib import Path,PurePosixPath
from types import SimpleNamespace
import current_contract as C
POLICY={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-bootstrap-off-materialize-v2-main-20261010-001/format_policy.py","bytes":4178,"sha256":"f3003c9c5eb67e7fd3cb10b9cefe0322431db21eae163ab0b2a13a02ab077b7a"}
def policy():
    C.checked(POLICY);name="_skvq_n1_actual_format_policy"
    cached=sys.modules.get(name)
    if cached is not None:
        C.require(getattr(cached,"__file__",None)and C.reference(cached.__file__)==POLICY,"cached exact original format policy")
        return cached
    spec=importlib.util.spec_from_file_location(name,POLICY["path"])
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    C.require(C.reference(module.__file__)==POLICY,"loaded original format policy unchanged")
    return module
def qualify(torch,npu,source):
    manifest=json.loads(Path(source["path"]).read_bytes())
    chain=manifest["native_format_patch_chain"]
    binding=dict(module="torch_npu",attribute="get_npu_format",runtime_path=str(Path(inspect.getfile(npu.get_npu_format)).resolve()),
      archive_ref=chain["format"],patch_chain=chain)
    adapter=SimpleNamespace(bound=C.checked,stable_origin=lambda obj:C.reference(inspect.getfile(obj)))
    getter,enum,observation=policy().bind_getter(npu,binding,adapter,torch.ops.npu.get_npu_format)
    return getter,enum,dict(binding=binding,observation=observation,policy_ref=POLICY)
def raw_format(value):
    inner=getattr(value,"value",None)
    return dict(actual_type=type(value).__module__+"."+type(value).__qualname__,repr=repr(value),
      enum_member=getattr(value,"name",None),native_value=inner if type(inner)in(int,str,bool)or inner is None else repr(inner),
      native_value_type=type(inner).__module__+"."+type(inner).__qualname__)
def observe_then_check(actual,value,enum,*,rank,source,identity,after_identity,qualification,destination,publish):
    # Preserve nonfinite arithmetic evidence as repr instead of failing JSON encoding.
    observed=[x if type(x)in(int,float)and math.isfinite(x)else repr(x)for x in actual]
    raw=dict(schema="skvq.actual-n1-tiny-raw/v1",source_ref=source,rank=rank,identity=identity,
      after_identity=after_identity,input=[1.,2.],output=observed,output_repr=repr(actual),
      output_types=[type(x).__module__+"."+type(x).__qualname__ for x in actual],
      format=raw_format(value),qualification=qualification,recorded_before_qualification_assertions=True)
    raw_ref=publish(destination,raw)
    C.require(type(actual)is list and actual==[4.,5.],"actual tiny arithmetic/synchronize output")
    serial=policy().serial(value,enum) # Exact source-qualified Format.ND only.
    C.require(identity==after_identity,"same actual tiny process before/after")
    return serial,raw_ref
def consume_raw(value,serial,*,rank,source,identity,after_identity):
    C.require(type(value)is dict and value["schema"]=="skvq.actual-n1-tiny-raw/v1"and
      value["source_ref"]==source and value["rank"]==rank and value["identity"]==identity==after_identity==value["after_identity"]and
      value["input"]==[1.,2.]and value["output"]==[4.,5.]and value["recorded_before_qualification_assertions"]is True,
      "same raw all4 arithmetic/identity before ND gate")
    p=policy();p.validate_serial(serial)
    expected=dict(actual_type=p.FORMAT_TYPE,repr=serial["repr"],enum_member="ND",native_value=2,native_value_type="builtins.int")
    C.require(value["format"]==expected,"exact original enum raw/serialized ND, no int/bool/foreign coercion")
    q=value["qualification"]
    C.require(q["policy_ref"]==POLICY,"actual reused format policy identity")
    p.validate_chain(q["binding"],C.checked)
    obs=q["observation"]
    # Runtime-library paths belong to the immutable image, not host filesystem
    # output aliases. Read the pinned archive and compare the producer's actual
    # full origin descriptors; never require a container site-package on host.
    for name in("wrapper_origin","enum_origin"):
        r=obs[name]
        C.require(type(r)is dict and set(r)=={"path","bytes","sha256"}and type(r["bytes"])is int and
          r["bytes"]>0 and type(r["path"])is str and PurePosixPath(r["path"]).is_absolute(),"strict actual runtime library origin descriptor")
    C.require(obs["wrapper_origin"]==obs["enum_origin"]and obs["wrapper_origin"]["path"]==q["binding"]["runtime_path"]and
      obs["wrapper_origin"]["sha256"]==p.FORMAT_SHA and obs["wrapper_origin"]["bytes"]==q["binding"]["archive_ref"]["bytes"]and
      obs["original_schemas"]and obs["compiled_schema_independently_consumed"]is False and obs["device_correctness_checked"]is False,
      "original source-qualified getter/enum and exported op schema")
    return value
def consume_row(value,source):
    C.require(value["status"]=="ACTUAL_TINY_CHECKED"and value["source_ref"]==source and
      value["input"]==[1.,2.]and value["output"]==[4.,5.]and type(value["format"])is int and value["format"]==2,
      "actual tiny terminal output and normalized ND field")
    raw=value["original_observation_ref"];C.checked(raw)
    consume_raw(json.loads(Path(raw["path"]).read_bytes()),value["actual_format"],rank=value["rank"],source=source,
      identity=value["identity"],after_identity=value["after_identity"])
    return value

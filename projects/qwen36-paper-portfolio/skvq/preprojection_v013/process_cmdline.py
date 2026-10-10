"""Exact source-bound host /proc cmdline bytes; no argv reserialization or padding policy.
Original gate_process and PID/start/cgroup/namespace checks remain mandatory.
"""
import hashlib,inspect,re,time
from pathlib import Path
import current_contract as C
GATE_REF={"path":"/opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/full_matrix_host_v2/host.py","bytes":33743,"sha256":"ab0296c698df00c9c3b2ce377601f6d6723adde6efb4a9e65407beca51ba5f86"}
SCHEMA="skvq.actual-proc-cmdline-raw/v1"
LIMIT=65536
IDENTITY={"pid","start_ticks","cgroup","cmdline_sha256"}
GATE=IDENTITY|{"argv","namespace_pids"}
def qualify(h):
    C.checked(GATE_REF)
    C.require(C.reference(h.__file__)==GATE_REF,"actual frozen process primitive owner")
    for f in (h.process_identity,h.gate_process):
        C.require(C.reference(inspect.getfile(f))==GATE_REF,"original source-qualified proc primitive; no foreign callable")
def consume(value,proof,source):
    C.require(type(value)is dict and set(value)=={"schema","source_ref","primitive_ref","before","original_gate","raw_hex","raw_bytes","raw_sha256","after","observed_epoch"} and
        value["schema"]==SCHEMA and value["source_ref"]==source and value["primitive_ref"]==GATE_REF,"complete current-source exact-byte observation")
    C.checked(source);C.checked(GATE_REF)
    before=value["before"];after=value["after"];gate=value["original_gate"]
    C.require(type(before)is dict and type(after)is dict and set(before)==IDENTITY and set(after)==IDENTITY and
        type(gate)is dict and set(gate)==GATE and before==after and
        {k:gate[k]for k in IDENTITY}==before,"original before/gate/after PID/start/cgroup/cmdline immutable fence")
    C.require(type(before["pid"])is int and before["pid"]>1 and type(before["start_ticks"])is int and
        before["start_ticks"]>0 and type(before["cgroup"])is str and before["cgroup"] and
        re.fullmatch("[0-9a-f]{64}",before["cmdline_sha256"]or""),"strict original live process identity")
    C.require(type(gate["argv"])is list and gate["argv"] and all(type(s)is str and s for s in gate["argv"]) and
        type(gate["namespace_pids"])is list and gate["namespace_pids"] and
        all(type(n)is int and n>0 for n in gate["namespace_pids"]) and gate["namespace_pids"][0]==before["pid"],
        "original nonempty filtered argv and actual namespace PID")
    C.require(all(k in proof and proof[k]==gate[k]for k in GATE),"proof remains exact original gate; physical/owned checks external")
    count=value["raw_bytes"];encoded=value["raw_hex"]
    C.require(type(count)is int and 0<count<=LIMIT and type(encoded)is str and len(encoded)==2*count and
        re.fullmatch("[0-9a-f]+",encoded),"bounded actual raw hex, no normalization or unknown representation")
    raw=bytes.fromhex(encoded)
    C.require(raw.endswith(bytes([0])) and [x.decode()for x in raw.split(bytes([0]))if x]==gate["argv"],
        "exact raw NUL bytes retain all empty segments and original decoded argv")
    C.require(hashlib.sha256(raw).hexdigest()==value["raw_sha256"]==before["cmdline_sha256"],
        "actual entire raw bytes match independent original digest")
    C.require(type(value["observed_epoch"])in(int,float) and value["observed_epoch"]>0,
        "actual observation timestamp")
    return gate
def capture(h,pid,source,writer,original_proof=None):
    qualify(h)
    before=h.process_identity(pid)
    proof=h.gate_process(pid)if original_proof is None else original_proof # Original caller proof, never stripped.
    with (Path("/proc")/str(pid)/"cmdline").open("rb")as f:raw=f.read(LIMIT+1)
    after=h.process_identity(pid)
    value=dict(schema=SCHEMA,source_ref=source,primitive_ref=GATE_REF,before=before,
        original_gate=proof,raw_hex=raw.hex(),raw_bytes=len(raw),raw_sha256=hashlib.sha256(raw).hexdigest(),
        after=after,observed_epoch=time.time())
    raw_ref=writer("ACTUAL_PROCESS_CMDLINE_RAW",value) # Preserve observed bytes before representation/fence refusal.
    consume(value,proof,source)
    return dict(proof,actual_cmdline_raw_ref=raw_ref)

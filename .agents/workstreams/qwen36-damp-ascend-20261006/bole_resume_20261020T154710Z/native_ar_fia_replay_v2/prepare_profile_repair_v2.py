"""DefaultOFF MAIN-only assembly of the exact namespace compilation repair v2."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

def need(v,m):
    if not v:raise ValueError(m)

def digest(path):
    p=Path(path);need(p.is_absolute()and p.is_file()and not any(v.is_symlink()for v in(p,*p.parents)),'ordinary exact source')
    h=hashlib.sha256();n=0
    with p.open('rb')as f:
        while True:
            b=f.read(2**20)
            if not b:break
            h.update(b);n+=len(b)
    return dict(path=str(p),bytes=n,sha256=h.hexdigest())

def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);p.add_argument('--prepare',action='store_true')
    for n in('v1-packet','probe-root','gate-source','v1-refs-json','probe-refs-json','new-packet-root','new-control-root','new-output-root'):
        p.add_argument('--'+n,type=Path)
    a=p.parse_args()
    if not a.prepare:print('{"enabled":false,"NPU":false,"resources_admitted":false}');return 0
    need(all(getattr(a,n)for n in('v1_packet','probe_root','gate_source','v1_refs_json','probe_refs_json','new_packet_root','new_control_root','new_output_root')),'all exact source/evidence/new-leaf arguments required')
    sys.dont_write_bytecode=True;old=a.v1_packet;probe=a.probe_root;new=a.new_packet_root;control=a.new_control_root;out=a.new_output_root
    r=digest(old/'ar_owner_common.py');need((r['bytes'],r['sha256'])==(19055,'5d0b9034706b9a942a4d7dd10870139959b22dfaab2cebbdddf25ba962e456a4'),'exact original common before import')
    s=importlib.util.spec_from_file_location('_fia_v2_assembly_common',r['path']);C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
    mr=C.ref(old/'ADVISORY_MANIFEST.json')
    C.need((mr['bytes'],mr['sha256'])==(6735,'81e634c01d84b14b8abd204ed93c0d364b0b52310f27b4a19a03a1760f253d57'),'exact frozen v1 flat manifest')
    historical=C.obj(mr)
    for name,row in historical['files'].items():
        C.need(Path(name).name==name,'flat source name')
        actual=C.ref(old/name);C.need((actual['bytes'],actual['sha256'])==(row['bytes'],row['sha256']),'whole original flat bytes '+name)
    for leaf in(new,control,out):
        C.need(leaf.is_absolute()and leaf.parent.is_dir()and not leaf.exists()and not any(v.is_symlink()for v in(leaf,*leaf.parents)),'fresh ordinary source/output leaf')
    C.need(len({str(v)for v in(new,control,out)})==3,'distinct fresh leaves')
    vr=C.obj(C.ref(a.v1_refs_json));pr=C.obj(C.ref(a.probe_refs_json))
    C.need(len(vr)==11 and set(pr)=={'NATIVE_AR_FIA_V2_NAMESPACE_PROBE.json','NATIVE_AR_FIA_V2_NAMESPACE_PROBE_EXECUTION.json'},'actual complete maps only')
    for row in(*vr.values(),*pr.values()):C.checked(row)
    proof=C.obj(pr['NATIVE_AR_FIA_V2_NAMESPACE_PROBE.json'])
    for name,expected in [('singleton_profile.py',(6682,'b4843a436f79337bd5fb55817b2445c7a15202e1fa19887683be0ee8418c3101')),
            ('namespace_compile_probe.py',(7297,'c9b54024922abe7f5e5064031b277868184938ed930fe5dada7bb9262fcf9e96'))]:
        row=C.ref(probe/name);C.need((row['bytes'],row['sha256'])==expected,'actual frozen successful probe source '+name)
    C.need(proof['new_profile']==C.ref(probe/'singleton_profile.py')and proof['probe_source']==C.ref(probe/'namespace_compile_probe.py'),
        'actual proof original full paths, no hash-only path rewrite')
    C.checked(C.ref(a.gate_source));new.mkdir(mode=0o700)
    for name in historical['files']:
        if name!='singleton_profile.py':shutil.copyfile(old/name,new/name)
    shutil.copyfile(probe/'singleton_profile.py',new/'singleton_profile.py')
    shutil.copyfile(probe/'namespace_compile_probe.py',new/'namespace_compile_probe.py')
    shutil.copyfile(a.gate_source,new/'namespace_repair_gate.py')
    shutil.copyfile(Path(__file__),new/'prepare_profile_repair_v2.py')
    C.write(new/'ACTUAL_FIA_V1_REFS.json',vr);C.write(new/'ACTUAL_NAMESPACE_PROBE_REFS.json',pr)
    common_path=new/'replay_common.py';original=common_path.read_bytes();body=original
    pairs=[
      (b"    'ACTUAL_FSUM_REFS.json','INSTALLED_PROVENANCE_REFS.json','INSTALLED_DISPATCH_REFS.json','INSTALLED_LINKED_REFS.json')",
       b"    'ACTUAL_FSUM_REFS.json','INSTALLED_PROVENANCE_REFS.json','INSTALLED_DISPATCH_REFS.json','INSTALLED_LINKED_REFS.json','namespace_repair_gate.py','ACTUAL_FIA_V1_REFS.json','ACTUAL_NAMESPACE_PROBE_REFS.json','namespace_compile_probe.py','prepare_profile_repair_v2.py')"),
      (b'    return y\n',b'    namespace_repair_values(C,y)\n    return y\n'),
      (b"[values,refs,y['files'],objects]",b"[values,refs,y['files'],objects,namespace_repair_values(C,y)['objects']]"),
      (b'    return x,m,on,list(unique.values()),dict(base=base_mapping,',
       b"    for path,sha in namespace_repair_values(C,y)['source_before'].items():\n        r=unique.get(path)\n        if r is None:r=C.ref(path);unique[path]=r\n        C.need(r['sha256']==sha,'all1010 exact immutable failed-v1 source paths reopened; no prefix exemption')\n    return x,m,on,list(unique.values()),dict(base=base_mapping,")]
    for before,after in pairs:
        C.need(body.count(before)==1,'unique metadata-only source/readset addition');body=body.replace(before,after)
    tail=b"\n\ndef namespace_repair_values(C,y):\n    gate=C.load(y['files']['namespace_repair_gate.py'],'_fia_namespace_repair_v2_gate')\n    return gate.verify(C,y)\n"
    body+=tail;inverse=body[:-len(tail)]
    for before,after in reversed(pairs):
        C.need(inverse.count(after)==1,'unique metadata-only inverse');inverse=inverse.replace(after,before)
    C.need(inverse==original,'complete original replay_common inverse; no math/owner/resource edits')
    common_path.write_bytes(body)
    runtime_unchanged=('replay_cpu_owner.py','metadata_cpu.py','replay_fia.py','consume_replay.py','arena_layout.py','library_maps.py','ar_saved_namespace.py','ar_owner_common.py')
    for name in runtime_unchanged:C.need((new/name).read_bytes()==(old/name).read_bytes(),'whole unchanged runtime/math/source '+name)
    for f in new.glob('*.py'):compile(f.read_bytes(),str(f),'exec',dont_inherit=True)
    before=C.ref(common_path)
    ledger=dict(schema='bole.native-AR-FIA-namespace-pipeline-repair-ledger/v2',actual_v1_refs=vr,actual_probe_refs=pr,
        original_flat_manifest=mr,original_common=C.ref(old/'replay_common.py'),new_common=before,
        actual_probe_profile=proof['new_profile'],new_profile=C.ref(new/'singleton_profile.py'),
        only_computational_change='faithful whole original-module and joint two-function readonly compilation pipeline',
        metadata_only_source_readset_gate_added=True,whole_common_inverse=True,
        metadata_pairs=[dict(before=x.decode(),after=z.decode())for x,z in pairs],metadata_append=tail.decode(),
        unchanged={name:C.ref(new/name)for name in runtime_unchanged},
        actual_namespace_probe_pass=True,actual_v2_CPU_tensor_run=False,actual_v2_NPU_run=False,
        original16frame32coordinate_failure_preserved=True,formal_success=False)
    C.write(new/'REPAIR_LEDGER.json',ledger)
    readme='Namespace repair v2. Use prepare_profile_repair_v2.py, not archived v1 prepare_replay_owner.py. Original LOCAL_CHECKS/test are archived V1 evidence, not V2 pass. Runtime math/owner/clock/resources are whole-byte unchanged; only profile compile pipeline changes. Metadata source/readset guard binds actual failed V1 and real successful namespace proof. All1010 exact previous sources are retained. Actual V2 CPU/NPU/256 calls/independent consume pending. No fsum/G1 math replay. New owner source-audit and actual finite MAIN execution remain mandatory.\n'
    (new/'REPAIR_README.txt').write_text(readme)
    files={f.name:C.ref(f)for f in sorted(new.iterdir())if f.is_file()and f.name!='ADVISORY_MANIFEST.json'}
    manifest=C.write(new/'ADVISORY_MANIFEST.json',dict(schema='bole.native-AR-FIA-namespace-repair-packet/v2',files=files,
        status='prepared_actual_namespace_probe_pass_replay_unexecuted',actual_namespace_probe=pr['NATIVE_AR_FIA_V2_NAMESPACE_PROBE.json'],
        actual_source_only_probe_pass=True,actual_new_software_controls_pending=True,
        historical_LOCAL_CHECKS_is_not_v2_pass=True,actual_CPU_Tensor_execution=False,actual_NPU_execution=False,
        actual_replay_completed=False,native_FA_math_qualified=False,formal_success=False))
    E=C.load(C.ref(new/'replay_common.py'),'_fia_v2_packet_common')
    control.mkdir(mode=0o700)
    for name in E.FILES:shutil.copyfile(new/name,control/name)
    oldy=C.obj(vr['INPUTS.json']);y=dict(oldy,output_root=str(out),files={name:C.ref(control/name)for name in E.FILES},namespace_profile_repair_v2=True)
    y['files'].update({'evidence/v1/'+name:row for name,row in vr.items()})
    y['files'].update({'evidence/probe/'+name:row for name,row in pr.items()})
    y['files'].update({'evidence/probe/original_profile.py':proof['new_profile'],
        'evidence/probe/original_probe.py':proof['probe_source'],'evidence/original_v1_flat_manifest.json':mr,
        'evidence/new_packet_manifest.json':manifest,'evidence/repair_ledger.json':C.ref(new/'REPAIR_LEDGER.json')})
    prepared=C.load(C.ref(control/'replay_common.py'),'_fia_v2_prepared_common')
    C.need(C.ref(E.__file__)['sha256']==C.ref(prepared.__file__)['sha256']and E.__file__!=prepared.__file__,
        'whole copied helper loaded at actual new control full path')
    ir=C.write(control/'INPUTS.json',y);prepared.source(C,ir);_,_,_,readset,_=prepared.readset(C,y)
    print(json.dumps(dict(inputs=ir,packet_manifest=manifest,readset_count=len(readset),
        actual_namespace_probe_pass=True,resources_admitted=False,NPU=False,actual_v2_operator_run=False)),flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())

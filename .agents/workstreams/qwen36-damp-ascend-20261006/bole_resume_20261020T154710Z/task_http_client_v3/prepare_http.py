"""Prepare fresh smoke source/authority bindings only. No HTTP/container/model."""
import argparse
import json
from pathlib import Path
import shutil
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import http_common as C


def prepare(plan_ref,CPU_ref,authority_ref,native_ref,generation_ref,new_root):
    C.authority(authority_ref,1800);plan,rows=C.plan(plan_ref);C.CPU_proof(CPU_ref,plan['source_ref'])
    # These expected runtime Refs came from actual G1 and stopped-image copies.
    C.need(C.ref(P/'NATIVE_SOURCE_EXPECTED.json')['sha256']==C.NATIVE_EXPECTED_SHA,'unchanged actual native expected source inventory')
    expected=C.parse((P/'NATIVE_SOURCE_EXPECTED.json').read_bytes());native=C.obj(native_ref)
    C.need(set(native)==set(expected),'complete exact native source closure')
    runtime={}
    for k,e in expected.items():
        actual=native[k];C.need(set(actual)=={'runtime_ref','snapshot_ref'}and actual['runtime_ref']==e,'same frozen installed native source '+k)
        snap=C.ref(C.checked(actual['snapshot_ref']));C.need((snap['bytes'],snap['sha256'])==(e['bytes'],e['sha256']),'exact actual stopped-image snapshot '+k)
        runtime[k]=e
    gen=C.ref(C.checked(generation_ref));C.need((gen['bytes'],gen['sha256'])==(202,'e70c136c1b78ddc1fb0905bac8e733a4dc448d4f852a5dd75143fffc70be550e'),'same actual original model generation config')
    root=new_root;C.need(root.is_absolute()and root.parent.is_dir()and not root.exists()and not any(p.is_symlink()for p in root.parents),'new ordinary source leaf')
    root.mkdir(mode=0o700)
    for n in(*C.FILES,'NATIVE_SOURCE_EXPECTED.json','CPU_OWNER_EXPECTED.json'):shutil.copyfile(P/n,root/n)
    shutil.copyfile(C.checked(generation_ref),root/'GENERATION_CONFIG.json')
    return C.write(root/'HTTP_SOURCE.json',dict(schema='bole.three-task-normalEOS-smoke/source/v3',default_enabled=False,prepared_only=True,
        files={n:C.ref(root/n)for n in C.FILES},native_expected_ref=C.ref(root/'NATIVE_SOURCE_EXPECTED.json'),
        client_entry_ref=C.ref(root/'client_entry.py'),client_process_optin_protocol=C.CLIENT_OPTIN_PROTOCOL,
        generation_config_ref=C.ref(root/'GENERATION_CONFIG.json'),original_generation_config_ref=generation_ref,native_source_snapshot_manifest_ref=native_ref,native_sources=runtime,plan_ref=plan_ref,
        CPU_owner_ref=CPU_ref,CPU_owner_profile=C.CPU_PROFILE,task_decoder_packet_manifest_sha256=C.TASK_PACKET_MANIFEST_SHA,authority_ref=authority_ref,image_id=C.IMAGE,phase='smoke',request_count=6,
        max_tokens=2048,minimum_context_tokens=5199,concurrency=1,phase_seconds=1800,request_seconds=300,
        raw_limit_bytes=64*2**20,barrier=dict(first_frozen_prompt_reused=True,max_tokens=1,ignore_eos=True,excluded_from_tasks=True),
        model_ready=False,formal_task_accuracy_accepted=False,performance_ready=False))


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--prepare',action='store_true')
    for n in('plan-ref','CPU-owner-ref','authority-ref','native-source-snapshot-manifest-ref','generation-config-ref'):p.add_argument('--'+n)
    p.add_argument('--new-root',type=Path);a=p.parse_args()
    if not a.prepare:print('{"enabled":false,"HTTP_executed":false}');return 0
    C.need(all(v is not None for v in vars(a).values()),'all actual prepared input/CPU/source refs and new root')
    refs=[C.parse(v)for v in(a.plan_ref,a.CPU_owner_ref,a.authority_ref,a.native_source_snapshot_manifest_ref,a.generation_config_ref)]
    print(json.dumps(dict(source_ref=prepare(*refs,a.new_root),model_ready=False,HTTP_executed=False)));return 0


if __name__=='__main__':raise SystemExit(main())

"""Read-only CPU proof joining; exact image-internal refs are not host mounts."""
import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common116 as C
from probe115 import REQUIRED


def from_cpu(sr,cpu_owner_ref):
    m=C.source(sr);cv=C.obj(cpu_owner_ref)
    C.need(cv['schema']=='bole.tree-owned-CPU/v118t'and cv['source']==sr and cv['primary']is None and cv['secondary']==[]and cv['resource_release_verified']is True and cv['stage_ref']is None and cv['Devices']==[]and cv['NPU']is False,'actual released same116 Devices[] CPU owner')
    stage=C.obj(cv['stage_result']);abi_ref=stage['actual_abi_ref'];final_inspect_ref=None
    if abi_ref['path']=='/adakv-results/preflight/ACTUAL_FIA_ABI.json':
        from ticket_alias116r5 import resolve
        abi_ref,final_inspect_ref=resolve(C,sr,m,cpu_owner_ref,cv,stage)
    abi=C.obj(abi_ref)
    C.need(stage['schema']=='bole.tree-CPU-stage/v118t'and stage['source']==sr and stage['NPU']is False and stage['primary']is None and stage['actual_meta']['pass_gate']is True,'actual CPU stage')
    C.need(abi['schema']=='bole.actual-FIA-installed-ABI/v115'and abi['source']==sr and abi['NPU']is False and abi['Devices']==[]and abi['no_device_fds']is True and abi['operator_executed']is False,'actual ABI no-operator receipt')
    C.need(abi['operator']=='npu::npu_fused_infer_attention_score'and set(REQUIRED)<=set(abi['argument_names'])and abi['header_ref']==m['header_ref']and isinstance(abi['overload'],str)and abi['schema_family'][abi['overload']]==abi['actual_schema'],'exact actual installed ABI/header')
    return dict(schema='bole.FIA-NPU-ticket/v118t',source=sr,cpu_owner=cpu_owner_ref,cpu_stage=cv['stage_result'],actual_abi_ref=abi_ref,cpu_final_inspect_ref=final_inspect_ref,image=m['image'],NPU=False,admitted_for_microprobe_only=True,model_ready=False,performance_ready=False)


def consume(ticket_ref,sr,cpu_owner_ref):
    value=C.obj(ticket_ref);C.need(value==from_cpu(sr,cpu_owner_ref),'ticket exact releasedCPU proof, not futureboolean');return value


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--cpu-owner-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    sr=json.loads(a.source_ref);C.window(C.source(sr));value=from_cpu(sr,json.loads(a.cpu_owner_ref));C.write(a.output,value);print(json.dumps(C.ref(a.output)));return 0

if __name__=='__main__':raise SystemExit(main())

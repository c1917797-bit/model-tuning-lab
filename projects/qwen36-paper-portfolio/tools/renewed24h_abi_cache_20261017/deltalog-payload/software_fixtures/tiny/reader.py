"""Independent exact tiny ABI receipt join. No model/layout/installer permission."""
import argparse
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import io_api as I

def result(v,m,base):
    I.need(v['NPU'] is True and v['actual_ND_byte_alias'] is True and v['source_storage_offset']==3 and v['alias_offset']==0 and v['complete_storage_bytes']==280,'actual offset/full-storage ABI')
    I.need(v['outside_write_negative_detected'] is True and v['tail_write_negative_detected'] is True and v['NaN_signed_zero_payload_byteexact'] is True and v['shared_BF16_offset_alias_byteexact'] is True,'actual negative/payload/shared typed controls')
    I.need(v['noncontinuous_typed_view'] is True and v['bidirectional_write_byteexact'] is True and v['source_alias_geometry_format_unchanged'] is True,'actual noncontinuous source/alias bidirectional byte writes and unchanged geometry/ND2')
    I.need(all(v[n] is False for n in('whole_native_pool_verified','model_qualified','performance_qualified','task_qualified')),'tiny evidence scope only')
    I.need(v['torch_npu_source']['bytes']==m['installed_torch_npu_init']['bytes'] and v['torch_npu_source']['sha256']==m['installed_torch_npu_init']['sha256'],'actual source-pinned torch_npu init')
    evidence=v['evidence'];I.need(evidence and len({r['path'] for r in evidence})==len(evidence),'unique complete evidence files')
    for r in evidence:I.need(Path(r['path']).parent==base/'byte-baselines','exact RW same-path evidence');I.checked(r)
    comparisons={Path(r['path']).name:I.obj(r) for r in evidence if r['path'].endswith('.comparison.json')}
    expected={'tiny-typed-offset':True,'tiny-outside-negative':False,'tiny-tail-negative':False,'tiny-nan-signedzero':True}
    I.need(set(comparisons)=={n+'.comparison.json' for n in expected},'complete actual positive/negative comparisons')
    for name,passed in expected.items():
        c=comparisons[name+'.comparison.json'];I.need(c['name']==name and c['bytewise_inactive_equal'] is passed and c['qualified'] is False and (c['first_difference'] is None)==passed,'actual bytewise verdict, not hash equality')
        baseline=I.checked(c['baseline']);I.need(baseline.parent==base/'byte-baselines','baseline exact RW path')
        if not passed:
            diff=c['first_difference'];bp=Path(diff['before_chunk']);ap=Path(diff['after_chunk'])
            I.need(bp.parent==ap.parent==base/'byte-baselines','negative exact chunk paths')
            bypath={r['path']:r for r in evidence};before=I.checked(bypath[str(bp)]).read_bytes();after=I.checked(bypath[str(ap)]).read_bytes();idx=diff['offset']-diff['chunk_begin']
            I.need(len(before)==len(after)==diff['chunk_end']-diff['chunk_begin'] and before[idx]!=after[idx] and before[idx]==diff['old_byte'] and after[idx]==diff['new_byte'],'preserved true inactive mismatch bytes')
    return v

def consume(sr,owner_ref,inspect_ref):
    m=I.verify_source(sr,HERE);o=I.obj(owner_ref);om=I.obj(o['source'])
    I.need(om['schema']=='deltalog.byteabi-owned-source/v1' and om['guest_source']==sr,'actual typed owner/guest join')
    for r in om['files'].values():I.checked(r)
    I.need(o['schema']=='deltalog.byteabi-owned/v1' and o['guest_source']==sr and o['primary'] is None and o['secondary']==[] and o['stopped_retained'] is True and o['qualified'] is False and o['physical']==[5] and o['logical']==0 and o['NPU'] is True,'actual successful original owner/scope, not old failed parent')
    root=Path(owner_ref['path']).parent;I.need(root.parent==Path('/opt/host/vnf/austinov') and root.name.startswith('run-dl-byteabi-'),'exact new authorized leaf')
    x=I.obj(inspect_ref)
    if type(x) is list:I.need(len(x)==1,'one final inspect');x=x[0]
    receipt=I.obj(I.ref(root/'numeric/create-receipt.json'));I.need(x['Id']==receipt['stdout'].strip(),'fresh exact created CID join')
    I.need(x['Image']=='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1' and x['State']['Running'] is False and x['State']['Pid']==0 and x['State']['ExitCode']==0 and not x['State']['OOMKilled'] and not x.get('ExecIDs'),'independent actual exit0/noExec/noOOM release')
    I.need(x['Config']['Labels'].get('deltalog-fresh-bridge.owner-source-sha256')==o['source']['sha256'],'owner label actual source')
    mounts=[(q['Source'],q['Destination']) for q in x['Mounts'] if q['RW']];I.need(mounts==[(str(root/'numeric'),str(root/'numeric'))],'exact sole same-path RW mount, no guest/host alias guessing')
    I.need(Path(o['result']['path'])==root/'numeric/result/STAGE_RESULT.json','actual staged result path')
    stage=I.obj(o['result']);I.need(stage['schema']=='deltalog.byteabi-stage/v1' and stage['source']==sr and stage['authority']==m['authority_ref'] and stage['primary'] is None and stage['NPU'] is True and stage['qualified'] is False and stage['old_failures_unchanged'] is True,'actual complete tiny stage')
    software=I.obj(I.ref(root/'numeric/result/SOFTWARE.json'))
    I.need(software==dict(schema='deltalog.byteabi-software/v1',source=sr,count=11,run=11,skips=0,errors=0,failures=0,passed=True),'actual sameimage complete mandatory controls')
    plan=I.obj(stage['plan']);G=I.load(m['files']['guest.py'],'_byteabi_reader_plan');G.verify_plan(plan,sr)
    r=I.obj(stage['result']);I.need(r['schema']=='deltalog.actual-tiny-byteabi/v1' and r['source']==sr and r['plan']==stage['plan'] and r['authority']==m['authority_ref'],'actual separate result joins')
    result(r['result'],m,root/'numeric/result')
    return dict(schema='deltalog.independent-tiny-byteabi/v1',source=sr,owner=owner_ref,final_inspect=inspect_ref,stage=o['result'],tiny_result=stage['result'],actual_NPU_byte_ABI=True,actual_native_pool_geometry=False,diagnostic_installer_admitted=False,model_qualified=False,performance_qualified=False,task_qualified=False)

def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--owner-ref');p.add_argument('--inspect-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    v=consume(*[json.loads(s) for s in(a.source_ref,a.owner_ref,a.inspect_ref)]);I.write(a.output,v);print(json.dumps(I.ref(a.output)));return 0

if __name__=='__main__':raise SystemExit(main())

"""Devices[] independent all256 output/original-oracle consumer; no native pass."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys


def run(t,C,R,y,ir,hr,rr,context,root):
    h,report=R.replay_gate(C,y,ir,hr,rr);x,m,_,_,_=context;original,num=R.math_sources(C,y)
    sys.path.insert(0,m['root'])
    F=C.load(original['files']['derived_math_consumer.py'],'_fia_independent_original_math')
    N=C.load(num['files']['numeric_diagnostic.py'],'_fia_independent_original_oracles')
    D=C.load(y['files']['replay_fia.py'],'_fia_raw_reader_only')
    A=C.load(y['files']['arena_layout.py'],'_fia_consumer_layout');L=C.load(y['files']['library_maps.py'],'_fia_consumer_maps_parser')
    _,metadata=R.metadata_gate(C,y,ir,hr);allowed=metadata['allowed_executable_libraries']
    independent_installed=L.bind(allowed)  # Fresh independent same-image whole SHA/ELF; never a loaded-NPU claim.
    C.need(set(independent_installed)==set(allowed),'independent complete installed catalog reopen')
    # Reopen actual whole map receipts; parse every executable path independently.
    # This CPU process cannot reopen a dead NPU process's inode. It checks that
    # its recorded exact backing identity joins the source-bound CPU catalog.
    map_count=0
    def check_map(row):
        nonlocal map_count
        C.need(row['whole_SHA_rechecked']is True,'actual complete SHA/buildIDs rechecked before/after every target call')
        value=C.obj(row['raw']);text=value['maps'];paths={}
        for line in text.splitlines():
            cols=line.split(maxsplit=5)
            C.need(len(cols)>=5,'complete retained map row')
            if 'x'not in cols[1]:continue
            C.need(len(cols)==6,'no anonymous executable mapping was accepted')
            path=cols[5]
            if path in('[vdso]','[vsyscall]'):continue
            C.need(path.startswith('/')and not path.endswith(' (deleted)')and '\\'not in path,'ordinary retained executable path')
            # Source actual CPU canonical catalog is exact: a symlink spelling
            # absent from that catalog cannot be silently canonicalized offline.
            paths.setdefault(path,[]).append(line)
        recorded=[]
        for path,v in row['observed'].items():
            C.need(path in allowed and v['ref']==allowed[path]['ref']and v['ELF']==allowed[path]['ELF'],
                'exact full canonical mapped Ref3/buildIDs join actual predeclared catalog')
            for line in v['map_rows']:
                cols=line.split(maxsplit=5);major,minor=cols[3].split(':');st=v['stat']
                C.need(line in text.splitlines()and int(cols[4])==st['inode']and
                    (int(major,16),int(minor,16))==(os.major(st['device']),os.minor(st['device'])),
                    'runtime-canonicalized exact backing inode/device retained independently per executable row')
                recorded.append(line)
        C.need(sorted(recorded)==sorted(line for lines in paths.values()for line in lines),
            'complete executable-row partition; no unknown/duplicate row, no offline symlink guessing')
        map_count+=1
    check_map(report['start_maps']);check_map(report['initialized_maps']);check_map(report['end_maps'])
    ar=C.obj(original['actual_saved_refs']['NATIVE-AR-BUNDLE.json']);rows=[];rank_refs=[];old_failed=0;old_violations=0;captured_equal=True;fillers_equal=True
    replay_failure={f:0 for f in A.FILLERS};replay_violations={f:0 for f in A.FILLERS};original_bad_all=[]
    for rank,capture in enumerate(ar['ranks']):
        export,raw=D.raw_rank(t,C,R,y,context,rank,capture);r=report['ranks'][rank];j=C.obj(r['report'])
        b=t.load(C.checked(r['tensors']),map_location='cpu',weights_only=True)
        C.need(r['rank']==j['rank']==b['rank']==rank and r['raw']==j['original_raw']==b['original_raw']==capture['raw']and
            j['inputs']==b['inputs']==ir and j['tensors']==r['tensors']and
            b['schema']=='bole.native-AR-FIA-replay-tensors/v1'and len(j['rows'])==len(b['rows'])==64,'all actual rank metadata/tensors joined')
        jm={(a['generation'],a['layer'],a['filler']):a for a in j['rows']};bm={(a['generation'],a['layer'],a['filler']):a for a in b['rows']}
        C.need(len(jm)==len(bm)==64,'every frame×both fillers, no duplicate/winner filtering')
        rank_rows=[]
        for generation,request,frame in D.frames(C,raw):
            frozen=F.actual_native_fa(t,frame);A.check_identity(frame);truths={};original_details={};original_bad={}
            for label,dtype in(('FP32',t.float32),('FP64',t.float64)):
                truth,_,_=N.reference(t,frame['query'],frame['key'],frame['value'],dtype)
                detail,bad=N.error_details(t,frame['output'],truth);truths[label]=truth;original_details[label]=detail;original_bad[label]=bad
                C.need(frozen['checks'][label]['peak_abs']==detail['peak_abs']and frozen['checks'][label]['pointwise_pass']==(detail['violation_count']==0),
                    'literal full original FP32/FP64 metrics independently recomputed, unchanged bound')
            old_failed+=original_details['FP64']['violation_count']>0;old_violations+=original_details['FP64']['violation_count']
            for v in original_details['FP64']['violations']:original_bad_all.append(dict(rank=rank,generation=generation,layer=frame['layer'],**v))
            controls={};current={}
            for filler in A.FILLERS:
                key=(generation,frame['layer'],filler);meta=jm[key];out=bm[key]['output'];aux=bm[key]['auxiliary']
                C.need(meta['rank']==rank and meta['request']==request['request']and meta['all13_original_kwargs']is True and
                    meta['storage_elements']==A.STORAGE_ELEMENTS and meta['shared_storage']is True and
                    all(meta['all_input_bits_unchanged'].values())and set(meta['all_input_bits_unchanged'])=={'arena','query','mask','table'}and
                    meta['native_output_shape']==list(frame['kernel'][0]['output'].shape)and
                    meta['original_checks']==frozen['checks']and out.dtype==t.bfloat16 and tuple(out.shape)==(1,6,256)and
                    bool(t.isfinite(out).all())and list(aux.shape)==meta['auxiliary_shape']and str(aux.dtype)==meta['auxiliary_dtype'],
                    'actual output ABI/private whole input-copy controls and original checks retained')
                expected_ordinal=rank*64+len(rank_rows)*2+list(A.FILLERS).index(filler)+1
                C.need(meta['call_ordinal']==expected_ordinal,'all256 real call order exactly preregistered')
                check_map(meta['maps_before']);check_map(meta['maps_after'])
                equal=bool(t.equal(out.view(t.int16),frame['output'].view(t.int16)));captured_equal&=equal
                C.need(meta['captured_output_bitwise_equal']==equal,'independent actual output bitwise comparison')
                metrics={}
                for label,truth in truths.items():
                    detail,bad=N.error_details(t,out,truth)
                    metrics[label]=dict(**detail,original_violating_coordinates_equal=bool(t.equal(bad,original_bad[label])))
                replay_failure[filler]+=metrics['FP64']['violation_count']>0;replay_violations[filler]+=metrics['FP64']['violation_count']
                current[filler]=out;controls[filler]=dict(captured_output_bitwise_equal=equal,checks=metrics)
            equal=bool(t.equal(current[A.FILLERS[0]].view(t.int16),current[A.FILLERS[1]].view(t.int16)));fillers_equal&=equal
            row=dict(rank=rank,generation=generation,request=request['request'],layer=frame['layer'],original_checks=original_details,
                fillers=controls,both_fillers_bitwise_equal=equal,original_native_numerical_pass=False)
            rows.append(row);rank_rows.append(row)
        jr=C.write(root/('INDEPENDENT-RANK-%d.json'%rank),dict(inputs=ir,rank=rank,original_raw=capture['raw'],actual_replay=r,rows=rank_rows))
        rank_refs.append(dict(rank=rank,report=jr));C.checked(capture['raw']);C.checked(r['tensors']);del export,raw,b,j,jm,bm,rank_rows
    C.need(len(rows)==128 and old_failed==16 and old_violations==32 and map_count==515,'all128 originals/32 coordinates and every before/after256 map pair')
    return dict(schema='bole.native-AR-FIA-independent-replay-diagnostic/v1',inputs=ir,source=x['AR_source'],replay_handoff=rr,
        metadata_handoff=hr,rank_count=4,frame_count=128,actual_operator_outputs_consumed=256,all_maps_consumed=map_count,
        original_failure_frame_count=old_failed,original_violation_count=old_violations,all_original_violating_coordinates=original_bad_all,
        filler_failure_frame_counts=replay_failure,filler_violation_counts=replay_violations,ranks=rank_refs,
        captured_output_bitwise_equal=captured_equal,both_fillers_bitwise_equal=fillers_equal,
        independent_diagnostic_completed=True,independent_installed_fullSHA_buildID_join=True,original_pointwise_bound_preserved=True,mathematics_recomputed=True,
        same_operator_replay_is_native_numerical_pass=False,weights_only_load=True,Devices=[],NPU=False,
        unused_arena_reconstruction=True,original_native_numerical_pass=False,native_FA_math_qualified=False,
        common_effects_pass=False,internal_precision_proven=False,formal_success=False)


def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--inputs-ref');p.add_argument('--metadata-handoff-ref');p.add_argument('--replay-handoff-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false,"formal_success":false}');return 0
    if not all((a.inputs_ref,a.metadata_handoff_ref,a.replay_handoff_ref,a.output)):p.error('exact source/real metadata/replay/release and fresh output required')
    if os.environ.get('ASCEND_RT_VISIBLE_DEVICES')!=''or os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')!='0'or list(Path('/dev').glob('davinci[0-9]*')):
        raise ValueError('actual Devices[] before tensor import')
    sys.dont_write_bytecode=True;s=importlib.util.spec_from_file_location('_fia_independent_common',Path(__file__).parent/'replay_common.py')
    R=importlib.util.module_from_spec(s);s.loader.exec_module(R);C=R.common();ir=json.loads(a.inputs_ref);y=R.source(C,ir);hr=json.loads(a.metadata_handoff_ref);rr=json.loads(a.replay_handoff_ref)
    C.need(C.ref(__file__)==y['files']['consume_replay.py']and a.output.parent==Path(y['output_root'])/'cpu-consumer'and
        a.output.parent.samefile('/adakv-results'),'sole independent CPU RW leaf')
    context=R.readset(C,y,installed=True);R.metadata_readset(C,y,ir,hr);R.replay_readset(C,y,ir,hr,rr)
    import torch
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    result=run(torch,C,R,y,ir,hr,rr,context,a.output.parent);C.write(a.output,result);return 0

if __name__=='__main__':raise SystemExit(main())

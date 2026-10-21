"""Strict completed128-frame metadata/source prerequisite; no tensor imports."""
import ast
import hashlib
import json
from pathlib import Path

MASK_SHA='d016ca7be6be829fd102f03317c3eed915d3df3d3fd54279a8858caea2dd57de'
PARAMETERS=dict(actual_seq_lengths=[1],actual_seq_lengths_kv=[132],block_size=128,
    input_layout='TND',num_heads=6,num_key_value_heads=1,scale=.0625,sparse_mode=3)
KEYS=sorted((*PARAMETERS,'atten_mask','block_table','query','key','value'))


def same(a,b):
    return a['path']==b['path']and a['sha256']==b['sha256']and('bytes'not in a or a['bytes']==b['bytes'])


def metadata(C,values,refs,ar):
    """Complete actual records, not a positive mathematical qualification."""
    owner=values['RESULT.json'];ticket=values['INPUTS.json'];data=values['cpu-consumer/MASKS.json']
    release=values['cpu-consumer/cleanup.json'];owned=values['cpu-consumer/OWNED.json']
    guest=values['cpu-consumer/GUEST_CPU.json'];child=values['cpu-consumer/MASK-METADATA-CHILD.json']
    pre=values['cpu-consumer/SAVED-SOURCE-PREFLIGHT.json'];prechild=values['cpu-consumer/SAVED-SOURCE-PREFLIGHT-CHILD.json']
    C.need(owner['schema']=='bole.native-ar-mask-metadata-finite-owner/v1'and owner['primary']is None and
        owner['secondary']==[]and owner['source_before']==owner['source_after']and len(owner['source_before'])==791 and
        owner['diagnostic_completed']is True and owner['inputs']==refs['INPUTS.json']and
        owner['source']==data['source']==ar['source']and owner['MAIN_lock']==values['MAIN-LOCK.json']and
        owner['MAIN_lock']['inherited_MAIN_lock_verified']is True,'actual completed clean metadata owner with exact791 source map')
    for key,name in [('diagnostic','cpu-consumer/MASKS.json'),('diagnostic_child','cpu-consumer/MASK-METADATA-CHILD.json'),
        ('release','cpu-consumer/cleanup.json'),('source_preflight','cpu-consumer/SAVED-SOURCE-PREFLIGHT.json'),
        ('source_preflight_child','cpu-consumer/SAVED-SOURCE-PREFLIGHT-CHILD.json')]:
        C.need(same(owner['summary'][key],refs[name]),'exact actual metadata child/release/report joins')
    C.need(release['stopped']is True and release['retained']is True and release['deleted']is False and
        release['errors']==[]and release['container']==owned['cid']and owned['source']==refs['INPUTS.json']and
        owned['image']==C.IMAGE and owned['arm']=='cpu-preflight'and owned['guest_cpus']==[0]and
        guest['affinity']==guest['effective_cpus']==guest['ancestor_cpuset']==[0]and guest['effective_capacity']==1 and
        guest['cgroup']=='/docker/'+owned['cid'],'actual same-image CPU0 stopped-retained metadata helper')
    inspect_ref=owner['summary']['actual_CPU_inspect']
    matches=[name for name,r in refs.items()if same(inspect_ref,r)]
    C.need(len(matches)==1,'one exact actual admission inspect receipt')
    inspection=values[matches[0]];rows=json.loads(inspection['stdout'])
    C.need(inspection['exit_code']==0 and len(rows)==1 and rows[0]['Id']==owned['cid']and
        rows[0]['Image']==C.IMAGE and rows[0]['State']['Running']is True and
        not(rows[0]['HostConfig'].get('Devices')or[])and rows[0]['HostConfig']['Memory']==8*2**30 and
        rows[0]['HostConfig']['CpusetCpus']=='0','actual bounded Devices[]8GiB CPU0 inspect')
    for ch in(child,prechild):
        C.need(ch['exit_code']==0 and ch['child_termination_observed']is True and
            ch['requested_argv'][:3]==['/usr/bin/docker','exec',owned['cid']],'actual same-owned zero-exit metadata/source children')
    for ch,script,ir in[(child,ticket['files']['mask_diagnostic.py'],refs['INPUTS.json']),
        (prechild,None,ticket['original_saved_inputs'])]:
        argv=ch['requested_argv'];pos=argv.index('--inputs-ref')
        C.need(json.loads(argv[pos+1])==ir,'actual exact source-bound child inputs')
        if script:C.need(argv[pos-2:pos]==[script['path'],'--execute'],'actual metadata child script')
    C.need(pre['source_preflight_pass']is True and pre['installed_sources_reopened']is True and pre['Devices']==[]and
        pre['inputs']==ticket['original_saved_inputs']and data['inputs']==refs['INPUTS.json']and
        data['schema']=='bole.actual-native-ar-mask-metadata-diagnostic/v1'and data['rank_count']==4 and
        data['frame_count']==128 and data['all_saved_inputs_preserved']is True and data['weights_only_load']is True and
        data['actual_failed_owner']==ticket['actual_v3_failure_refs']['RESULT.json']and
        data['actual_passed_original_G1_report']==ticket['actual_v3_failure_refs']['cpu-consumer/BOLE-INDEPENDENT-GATE/ATTRIBUTION.json'],
        'actual complete source preflight and primitive-mask metadata')
    for obj in(owner,data):
        C.need(all(obj[k]is False for k in('NPU','original_G1_math_rerun','mask_semantics_qualified',
            'native_FA_math_qualified','native_AR_numeric_pass','common_effects_pass','model_ready','formal_success')),
            'metadata never promoted to mathematics or common/model success')
    schemas=None;seen=set()
    for rank,(r,capture)in enumerate(zip(data['ranks'],ar['ranks'])):
        C.need(r['rank']==rank and r['frame_count']==len(r['frames'])==32 and r['raw']==capture['raw']and
            r['receipt']==capture['receipt'],'same actual four original captures as mathematical consumer')
        for row in r['frames']:
            key=(rank,row['generation'],row['layer'])
            C.need(key not in seen and row['rank']==rank and row['generation']in(1,2)and row['layer']in range(3,64,4)and
                row['route']=='npu_fused_infer_attention_score'and row['explicit_kwargs_keys']==KEYS and
                {k:row['parameters'][k]for k in PARAMETERS}==PARAMETERS,'all128 unique actual exact q1/KV132 FIA frames')
            seen.add(key);mask=row['mask']
            C.need(mask['dtype']=='torch.int8'and mask['shape']==[2048,2048]and mask['stride']==[2048,1]and
                mask['storage_offset']==0 and mask['contiguous']is True and mask['numel']==mask['contiguous_bytes']==4194304 and
                mask['element_size']==1 and mask['contiguous_byte_sha256']==MASK_SHA and mask['finite']is True and
                mask['negative_present']is False and mask['exact_zero_or_one_only']is True and
                mask['unique_values_complete']is True and mask['unique_values_counts']==[
                    dict(value=0,count=2098176),dict(value=1,count=2096128)]and
                mask['full_mask_formula_observations']['full_exact_zero_one_upper_triangle']is True and
                mask['formula_comparison_implies_operator_semantics']is False and mask['mask_semantics_qualified']is False,
                'exact whole4194304-entry observed mask ABI, not a dtype relaxation')
            if schemas is None:schemas=row['recorded_operator_schemas']
            C.need(row['recorded_operator_schemas']==schemas,'one exact recorded original dispatcher schema family')
    C.need(seen=={(rank,g,layer)for rank in range(4)for g in(1,2)for layer in range(3,64,4)},'every128 frame required')
    h=hashlib.sha256()
    for i in range(2048):h.update(bytes(i+1)+b'\1'*(2047-i))
    C.need(h.hexdigest()==MASK_SHA,'independent complete byte-formula matches actual observed mask SHA')
    # Lower-right origin: blocked iff j>i+(Lkv-Lq). q1/KV132 has no future key.
    C.need(not any(j>132-1 for j in range(132)),'exact q1 right-down geometry sees all132 valid keys')
    return dict(frame_count=128,raw_refs=[r['raw']for r in data['ranks']],mask_SHA=MASK_SHA,
        actual_prior_v3_failure=data['actual_failed_owner'],actual_prior_passed_G1_child=data['actual_passed_original_G1_report'],
        mask_shape=[2048,2048],mask_dtype='torch.int8',recorded_operator_schemas=schemas,
        q1_KV132_visible_keys=132,mathematical_qualification=False,formal_success=False)


def verify(C,y,ar,*,installed):
    refs=C.obj(C.ref(Path(__file__).parent/'ACTUAL_MASK_V4_REFS.json'))
    C.need(y['actual_mask_metadata_refs']==refs,'exact actual completed mask-v4 chain')
    values={name:C.obj(r)for name,r in refs.items()};proof=metadata(C,values,refs,ar)
    ticket=values['INPUTS.json'];r=ticket['files']['diag_common.py']
    C.need((r['bytes'],r['sha256'])==(9331,'e43fd9fb92b8b610b45dfcbaa3a228b4755ecefa2e3f961400f14f2c0414115d'),
        'exact completed mask source helper before import')
    D=C.load(r,'_saved_v4_actual_completed_mask_source');D.source(C,refs['INPUTS.json'])
    _,_,_,reopened,mapping=D.readset(C,ticket,installed=installed)
    reopened=[*reopened,refs['INPUTS.json']];observed={r['path']:r['sha256']for r in reopened}
    C.need(all(observed.get(p)==sha for p,sha in values['RESULT.json']['source_before'].items()),
        'all791 actual completed diagnostic immutable sources reopened now; no prefix exemptions')
    versions=C.obj(C.ref(Path(__file__).parent/'ACTUAL_TORCH_NPU_VERSION_REFS.json'))
    C.need(y['actual_torch_npu_version_refs']==versions,'exact stopped same-image version source copies')
    version={n.targets[0].id:ast.literal_eval(n.value)for n in ast.parse(C.checked(versions['version.py']).read_bytes()).body if isinstance(n,ast.Assign)}
    C.need(version==dict(__version__='2.10.0.post4',git_version='5dd8ef3f9b375b5ae4a83538d5785754148c3302'),
        'actual installed TorchNPU version primary; not stale METADATA rc2 compatibility table')
    metadata_text=C.checked(versions['METADATA']).read_text()
    C.need('\nVersion: 2.10.0.post4\n'in metadata_text and '\nRequires-Dist: torch ==2.10.0\n'in metadata_text,
        'actual distribution version/torch dependency headers')
    proof.update(actual_metadata_refs=refs,actual_version_refs=versions,version=version,
        original_diagnostic791_source_closure_reopened=True,source_mapping=mapping,
        original_FP32_FP64_pointwise_bound='0.001+0.01*abs(truth)',installed_sources_reopened=installed)
    extra={k:dict(installed=v['runtime_ref'],host=v['host_ref'])for k,v in mapping['mask_primary_sources'].items()}
    return proof,[*reopened,*refs.values(),*versions.values()],values,extra

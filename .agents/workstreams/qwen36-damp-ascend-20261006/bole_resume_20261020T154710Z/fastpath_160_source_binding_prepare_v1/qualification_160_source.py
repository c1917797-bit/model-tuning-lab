"""Exact160 source binding preparation and strict real-short8 predecessor bridge."""
import contextlib
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
PARENTS={
    "long_gate_primitives": {
        "bytes": 14106,
        "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_long_gate_prepare_v1/long_gate_primitives.py",
        "sha256": "6b48e5486d907e9532cc403f0d1b5f3a1d8530f79664b3cb128e3140ee56c142"
    },
    "prepare_clock": {
        "bytes": 3715,
        "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_clock_seam_prepare_v1/prepare_clock.py",
        "sha256": "3b7e9ddb7b0921a145689744c2c18da75848421a9aed0641cfcd68d3a4a80103"
    },
    "qualification_clock_delta": {
        "bytes": 3092,
        "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_clock_seam_prepare_v1/qualification_clock_delta.py",
        "sha256": "d9393f9d446b86537aa43c2bf40023b5bdf347c3c99cfce56010a1563433212a"
    },
    "qualification_parent_renderer": {
        "bytes": 2751,
        "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/qualification_parent_renderer.py",
        "sha256": "1db3e787bd7b9a3f3b6b532fb59e9410902c70c2f1f31d5216e4e9d965bdadae"
    },
    "qualification_short_prepare": {
        "bytes": 16410,
        "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/qualification_short_prepare.py",
        "sha256": "940f26bd449f6b0577b0d590303bb68aa0f99f73f8051cc165ba4e09a955db0b"
    },
    "qualification_tap_delta": {
        "bytes": 2577,
        "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/qualification_tap_delta.py",
        "sha256": "349bd1da965eca33df950f6817d88d9e9a3759771ce589f9b901c62302fe27da"
    },
    "render160": {
        "bytes": 12165,
        "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_long_gate_prepare_v1/render160.py",
        "sha256": "9cb4109334fffea996bdf4fb03b8037d06bb4984e9b5b06e893614815710013c"
    },
    "render_page_delta": {
        "bytes": 2272,
        "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_long_gate_prepare_v1/render_page_delta.py",
        "sha256": "ea0a9cb699872606daea5fc8373a6646c401971931b246346d7ae592d2bc4d3d"
    }
}

def need(v,s):
    if not v:raise ValueError(s)

def checked(r):
    p=Path(r['path']);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary immutable160 parent')
    b=p.read_bytes();need(len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'complete immutable160 parent Ref')
    return b

@contextlib.contextmanager
def modules(refs,order):
    bodies={n:checked(refs[n])for n in order}
    missing=object();old={n:sys.modules.get(n,missing)for n in order};paths=list(sys.path)
    for n in order:sys.modules.pop(n,None)
    loaded={}
    try:
        for name in order:
            r=refs[name];spec=importlib.util.spec_from_file_location(name,r['path'])
            module=importlib.util.module_from_spec(spec);sys.modules[name]=module
            exec(compile(bodies[name],r['path'],'exec'),module.__dict__);loaded[name]=module
        yield loaded
    finally:
        for name in order:
            sys.modules.pop(name,None)
            if old[name]is not missing:sys.modules[name]=old[name]
        sys.path[:]=paths

def refbytes(path,b):return dict(path=str(path),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def render(*,base_root=None,permit_materialized=False,parent_pair_preparation_root=None,
           historical_short_source_ref=None,authority_ref=None,parent_preparation_readset=None,
           short8_prerequisite=None):
    base=HERE if base_root is None else Path(base_root)
    need(type(permit_materialized)is bool,'explicit reconstruction mode')
    order=('qualification_parent_renderer','qualification_tap_delta','qualification_short_prepare',
           'qualification_clock_delta','prepare_clock','render_page_delta','render160')
    for r in PARENTS.values():checked(r)
    # The exact clock builder has a reconstruction-only HERE global. It is
    # configured in a private temporary namespace, never a worker module.
    with modules(PARENTS,order)as loaded:
        loaded['prepare_clock'].HERE=base
        parent=loaded['prepare_clock'].render(authority_ref=authority_ref)
        files=loaded['render160'].adapt(parent['files'])
    pm=parent['manifest']
    for supplied,expected in ((parent_pair_preparation_root,pm['qualification_parent_pair_preparation_root']),
                              (historical_short_source_ref,pm['qualification_historical_short_source']),
                              (parent_preparation_readset,pm['qualification_parent_preparation_readset'])):
        if supplied is not None:need(str(supplied)==expected if isinstance(supplied,Path)else supplied==expected,'exact inherited160 parent operand')
    files['qualification_short_prepare.py']=b'"""Source-owned160 renderer API; never a launcher."""\nfrom qualification_160_source import render,inverse\n'
    files['qualification_160_source.py']=(HERE/'qualification_160_source.py').read_bytes()
    files['long_gate_primitives.py']=checked(PARENTS['long_gate_primitives'])
    # Change ONLY qualification scope, not formal1024 gate or numerical bounds.
    text=files['qualification_source_validate.py'].decode().replace('short8','160')
    text=text.replace('output_tokens=8','output_tokens=160').replace("['output_tokens']==8","['output_tokens']==160")
    text=text.replace("['max_output_tokens']==8","['max_output_tokens']==160").replace("['HTTP_output_tokens']==8","['HTTP_output_tokens']==160")
    old="    read_ref(m['files']['qualification_clock_delta.py'])"
    need(text.count(old)==1,'current clock preimport closure')
    text=text.replace(old,old+"\n    read_ref(m['files']['qualification_160_source.py'])",1)
    old='    execution_window(m,clock=True,require_phase=True)\n    return dict'
    need(text.count(old)==1,'one actual runtime160 admission seam')
    text=text.replace(old,"    execution_window(m,clock=True,require_phase=True)\n    from qualification_160_source import require_short8\n    require_short8(m)\n    return dict",1)
    files['qualification_source_validate.py']=text.encode()
    for name in('qualification_source_validate.py','qualification_source_producer.py'):
        text=files[name].decode()
        old="        parent_preparation_readset=m['qualification_parent_preparation_readset'])"
        need(text.count(old)==1,'one actual160 reconstruction call '+name)
        text=text.replace(old,"        parent_preparation_readset=m['qualification_parent_preparation_readset'],\n        short8_prerequisite=m['qualification_short8_prerequisite'])",1)
        files[name]=text.encode()
    text=files['qualification_source_producer.py'].decode()
    for old,new in [
        ('def prepare_mapping(base_root,authority_ref=None):','def prepare_mapping(base_root,authority_ref=None,short8_prerequisite=None):'),
        ('Q.render(base_root=Path(base_root),authority_ref=authority_ref)','Q.render(base_root=Path(base_root),authority_ref=authority_ref,short8_prerequisite=short8_prerequisite)'),
        ('def materialize(base_root,authority_ref=None):','def materialize(base_root,authority_ref=None,short8_prerequisite=None):'),
        ('b=prepare_mapping(base,authority_ref);','b=prepare_mapping(base,authority_ref,short8_prerequisite);'),
        ("p.add_argument('--template-ref');p.add_argument('--source-ref')","p.add_argument('--template-ref');p.add_argument('--source-ref');p.add_argument('--short8-prerequisite')"),
        ('result=materialize(a.base_root,None if a.authority_ref is None else json.loads(a.authority_ref))',
         'result=materialize(a.base_root,None if a.authority_ref is None else json.loads(a.authority_ref),None if a.short8_prerequisite is None else json.loads(a.short8_prerequisite))'),
        ('(a.base_root,a.authority_ref,a.template_ref,a.source_ref)','(a.base_root,a.authority_ref,a.template_ref,a.source_ref,a.short8_prerequisite)'),
        ('(a.base_root,a.authority_ref,a.source_ref)','(a.base_root,a.authority_ref,a.source_ref,a.short8_prerequisite)'),
        ('(a.base_root,a.authority_ref,a.template_ref)','(a.base_root,a.authority_ref,a.template_ref,a.short8_prerequisite)')]:
        need(text.count(old)==1,'exact160 public producer operand '+old[:70]);text=text.replace(old,new,1)
    files['qualification_source_producer.py']=text.encode()
    # The old receipt-ABI test is updated to use the actual new transport API;
    # its synthetic data remains explicitly software-only, never NPU evidence.
    text=files['test_qualification_entry.py'].decode()
    old="            probe.capture(bridge,frame,dict(req_ids=['fixture'],sampled_token_ids=[[7]]))"
    need(text.count(old)==1,'one original state ABI call')
    new="""            envelope=dict(wire=dict(path='/synthetic/only',bytes=10,sha256='a'*64),
                codec=dict(wire_bytes=10,wire_sha256='a'*64))
            with patch.object(SP.LONG,'read_report',return_value=(report,envelope)):
                probe.capture(bridge,frame,dict(req_ids=['fixture'],sampled_token_ids=[[7]]))"""
    text=text.replace(old,new,1)
    text=text.replace("self.assertEqual(len(events[0][3]['rows']),128)","self.assertEqual(events[0][3]['rows_reference']['schema'],'bole.lossless-state-rows-reference/v1')")
    files['test_qualification_entry.py']=text.encode()
    m=copy.deepcopy(pm);root=base/'prepared-source-160';output=base/'reserved-output-160'
    need(permit_materialized or(not root.exists()and not output.exists()),'new160 source/output only')
    old_refs={r['path']:(name,r)for name,r in m['files'].items()}
    m.update(root=str(root),output_root=str(output),model_receipt_root=str(output/'dense/receipts'),
        fastpath_numeric_qualification=dict(m['fastpath_numeric_qualification'],output_tokens=160),
        short_state_digest_profile=dict(m['short_state_digest_profile'],output_tokens=160,ordinals=list(range(159))),
        qualification_source_schema='bole.fastpath-160-qualification-whole-source/v1',
        qualification_160_preparation_readset=copy.deepcopy(PARENTS),
        qualification_short8_prerequisite=copy.deepcopy(short8_prerequisite),prepared_only=True,performance_ready=False,numerical_qualified=False)
    m['performance_profile']['scope']['output_tokens']=160
    m['service_experiment'].update(profile='qualifier160',max_steps_per_request=159,max_output_tokens=160)
    m['profile']['HTTP_output_tokens']=160;m['performance_client_contract']['output_tokens']=160
    # Actual host output contract, not merely manifest path labels.
    text=files['contract090.py'].decode()
    text=text.replace(pm['output_root'],str(output))
    files['contract090.py']=text.encode()
    m['stream_channel_root']=str(output/'dense/receipts/STREAM')
    m['stream_channel_contract_path']=str(output/'dense/receipts/STREAM/CHANNEL.json')
    m['qualification_preparation_root']=str(base)
    m['files']={name:refbytes(root/name,b)for name,b in sorted(files.items())}
    def rebase(x):
        if type(x)is dict:
            if set(x)=={'path','bytes','sha256'}and x['path']in old_refs:
                name,r=old_refs[x['path']];need(x==r,'exact160 inherited Ref')
                return dict(m['files'][name])
            return {k:rebase(v)for k,v in x.items()}
        if type(x)is list:return [rebase(v)for v in x]
        return x
    for key in('dependencies','service_runtime_source_snapshots','performance_timing_donor','performance_streaming_client'):m[key]=rebase(m[key])
    delta={name:dict(before=parent['files'].get(name),after=b)for name,b in files.items()if name not in parent['files']or b!=parent['files'][name]}
    for name,b in files.items():
        if name.endswith('.py'):compile(b,name,'exec')
    return dict(manifest=m,files=files,parent_bundle=parent,inverse_delta=delta,prepared_only=True,
        execution_ready=False,actual_bound_validated=False,NPU=False)

def inverse(bundle):
    parent=bundle['parent_bundle']['files'];files=dict(bundle['files'])
    changed={n for n,b in files.items()if n not in parent or parent[n]!=b}
    need(changed==set(bundle['inverse_delta']),'complete160 inverse ledger')
    for name in changed:
        d=bundle['inverse_delta'][name];need(files[name]==d['after'],'exact160 after bytes')
        if d['before']is None:files.pop(name)
        else:files[name]=d['before']
    need(files==parent,'whole160 inverse restores all420 clock parent files')
    return files

def checked_short8_source(C,source,old):
    # No caller-selected executable is imported until the entire original
    # short8 source has been rebuilt by the already pinned clock420 renderer.
    order=('qualification_parent_renderer','qualification_tap_delta','qualification_short_prepare',
           'qualification_clock_delta','prepare_clock')
    for r in PARENTS.values():checked(r)
    with modules(PARENTS,order)as loaded:
        # The frozen clock builder is creation-oriented. For historical
        # verification only, derive the one supported read-only reconstruction
        # operand from its exact pinned bytes; no source or output is written.
        raw=checked(PARENTS['prepare_clock']).decode()
        needle='parent=Q.render(base_root=HERE,authority_ref=authority_ref)'
        need(raw.count(needle)==1,'exact frozen clock materialized reconstruction operand')
        raw=raw.replace(needle,'parent=Q.render(base_root=HERE,authority_ref=authority_ref,permit_materialized=True)',1)
        exec(compile(raw,PARENTS['prepare_clock']['path']+'[read-only-materialized]','exec'),
             loaded['prepare_clock'].__dict__)
        loaded['prepare_clock'].HERE=Path(old['qualification_preparation_root'])
        expected=loaded['prepare_clock'].render(authority_ref=old['qualification_authority_ref'])
        loaded['prepare_clock'].inverse(expected)
    template=C.obj(old['prepared_template'])
    need(template==expected['manifest'],'complete trusted clock420 short8 template reconstruction')
    root=Path(old['root'])
    need(Path(source['path'])==root/'SOURCE_BOUND.json'and
         Path(old['prepared_template']['path'])==root/'SOURCE_TEMPLATE.json',
         'actual predecessor source and immutable template exact root')
    normalized=dict(old);normalized['prepared_only']=True
    normalized['qualification_source_binding_pending']=True;normalized.pop('prepared_template')
    need(normalized==template,'only original short8 binding transition, not caller metadata')
    need(set(old['files'])==set(expected['files']),'complete original short8 executable readset')
    for name,raw in expected['files'].items():
        need(Path(old['files'][name]['path'])==root/name and
             C.checked(old['files'][name]).read_bytes()==raw,
             'trusted original short8 full-source bytes before any old helper '+name)
    # Historical completion may be expired now. Preserve its real MAIN review
    # and source binding checks without borrowing or extending that clock.
    with modules({'qualification_source_validate':old['files']['qualification_source_validate.py']},
                 ('qualification_source_validate',))as loaded:
        validator=loaded['qualification_source_validate']
        need(C.ref(validator.__file__)==old['files']['qualification_source_validate.py'],
             'trusted exact original short8 source-owned validator')
        validator.execution_window(old,clock=False,require_phase=False)
    return old


def require_short8(m):
    import sourceio as C
    need(C.ref(__file__)==m['files']['qualification_160_source.py'],'actual source-owned strict predecessor bridge')
    p=m.get('qualification_short8_prerequisite')
    need(type(p)is dict and set(p)=={'source','host_result','terminal_result'},
         'real short8 prerequisite missing: no synthetic numerical PASS may dispatch160')
    old=C.obj(p['source'])
    need(old['prepared_only']is False and old['fastpath_numeric_qualification']['output_tokens']==8 and
         old['short_state_digest_profile']['output_tokens']==8,'actual completed short8 source, not160/1024')
    checked_short8_source(C,p['source'],old)
    for key in('checkpoint_config_ref','checkpoint_index_ref','common','native_speculative_config','paired_common_environment'):
        need(old[key]==m[key],'same short8 prerequisite model/common '+key)
    for name in('core112.py','adapter.py','oracle112.py','independent_model.py','g2_numeric.py','transaction.py','tp_consensus.py','server090.py'):
        need(old['files'][name]['sha256']==m['files'][name]['sha256'],'same actual short8/160 math/transaction '+name)
    order=('bole_performance_profile','short_state_digest','compare_state_digest',
           'performance_client_consumer','fastpath_numeric_consumer','qualification_smoke_join')
    refs={n:old['files'][n+'.py']for n in order}
    with modules(refs,order)as loaded:
        result=loaded['qualification_smoke_join'].consume(C,old,p['source'],p['host_result'])
    terminal=C.obj(p['terminal_result'])
    need(result==terminal and result['source']==p['source']and result['short8_numeric_scope_passed']is True and
         result['full64_layers_and128_actual_writes']is True and result['all4_actual_HTTP_state_lifecycle_join']is True and
         result['numerical_qualified']is False and result['whole_model_pass']is False and result['formal_performance']is False,
         'real original short8 consumer reopened independent reports/STATE/HTTP result, no released-tensor replay or scope promotion')
    return p


if __name__=='__main__':
    if sys.argv[1:]!=['--check']:
        need(not sys.argv[1:],'explicit source-only --check required')
        print(json.dumps(dict(enabled=False,NPU=False,source_bound=False)))
    else:
        b=render();inverse(b)
        print(json.dumps(dict(files=len(b['files']),changed=sorted(b['inverse_delta']),
            execution_ready=False,short8_prerequisite_present=False,NPU=False),sort_keys=True))

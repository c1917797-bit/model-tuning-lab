"""Typed source-specific32k/C1 component delta, not a whole-source authority."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import runpy

HERE=Path(__file__).resolve().parent
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole2k_runtime_complete_prepare_v3/prepared-source-short8-qualifier")
BOUND=ROOT/'SOURCE_BOUND.json'
TARGETS={
 'input_identity.py':(('capture',),()),
 'fa_native_geometry.py':(('plan','bind_layer','bind_all'),()),
 'cache_registry.py':(('register',),()),
 'service_runner.py':(('after_prefill',),()),
 'g2_contract.py':(('scope','capacity'),()),
 'numeric_prefix_2k.py':(('frame_domain','prefill','require_runtime_admission'),('INPUT',)),
 'bole_performance_profile.py':(('Profile',),('EXPECTED_SCOPE','SERVICE_SCOPE')),
 'compare_state_digest.py':(('load_arm',),()),
 'performance_host.py':(('run',),()),
 'contract090.py':(('source',),()),
 'paired_receipt_consumer.py':(('candidate_record',),())}


def need(v,s):
    if not v:raise ValueError(s)


def raw_ref(p,b):return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def replace_nodes(text,scopes,assignments,old=2048,new=32768):
    tree=ast.parse(text);chosen=[]
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name in scopes:chosen.append(n)
        if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id in assignments for t in n.targets):chosen.append(n)
    positions={(n.lineno,n.col_offset,n.end_lineno,n.end_col_offset)for p in chosen for n in ast.walk(p)
               if isinstance(n,ast.Constant)and type(n.value)is int and n.value==old}
    lines=text.splitlines(keepends=True)
    for line,col,endline,endcol in sorted(positions,reverse=True):
        need(line==endline,'one exact typed literal')
        lines[line-1]=lines[line-1][:col]+str(new)+lines[line-1][endcol:]
    need(positions,'expected typed32k source seam')
    return ''.join(lines),len(positions)


def function(text,name,new_source):
    node=next(n for n in ast.walk(ast.parse(text))if isinstance(n,ast.FunctionDef)and n.name==name)
    lines=text.splitlines(keepends=True)
    return ''.join(lines[:node.lineno-1])+new_source.rstrip()+'\n'+''.join(lines[node.end_lineno:])


def render():
    m=json.loads(BOUND.read_bytes());files={}
    for name,r in m['files'].items():
        p=Path(r['path']);b=p.read_bytes()
        need(raw_ref(p,b)==r and p==ROOT/name and not any(x.is_symlink()for x in(p,*p.parents)),'exact actual V3 source '+name)
        files[name]=b
    parent=dict(files);counts={}
    for name,(scopes,assigns)in TARGETS.items():
        old=131 if name=='paired_receipt_consumer.py'else 2048
        s,count=replace_nodes(files[name].decode(),scopes,assigns,old=old)
        files[name]=s.encode();counts[name]=count
    # Exact owning native argv fields only; no global4096 replacement.
    s=files['contract090.py'].decode()
    node=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)and n.name=='server_command')
    part=ast.get_source_segment(s,node)
    need(part.count("'4096'")==2,'two actual native argv context/batch values')
    s=s[:s.index(part)]+part.replace("'4096'","'40960'")+s[s.index(part)+len(part):]
    # Source profile still must be rebound with the same explicit40960 fields.
    s,count=replace_nodes(s,('source',),(),old=4096,new=40960)
    files['contract090.py']=s.encode();counts['contract090.context']=count
    files['hypic32k_input.py']=(HERE/'hypic32k_input.py').read_bytes()
    s=files['service_client.py'].decode()
    s,_=replace_nodes(s,('run',),())
    s=function(s,'inputs',"""def inputs(tokenizer):
 import hypic32k_input as I
 return I.select(I.dataset(tokenizer),'warmup')""")
    files['service_client.py']=s.encode()
    s=files['performance_service_client.py'].decode()
    s,count=replace_nodes(s,('request','run'),())
    need(s.count("header = 'bole-perf-131-' + label")==1,'actual input request identity prefix')
    s=s.replace("header = 'bole-perf-131-' + label","header = 'bole-perf-32k-' + label",1)
    need(s.count('    ids = inputs(tokenizer)')==1,'actual input producer seam')
    s=s.replace('    ids = inputs(tokenizer)',"    import hypic32k_input as I\n    dataset = I.dataset(tokenizer)\n    ids = I.select(dataset,'warmup')",1)
    need(s.count("request(donor,args,ids,0,8,'measured'")==1 and
         s.count("request(donor,args,ids,1,1,'retirement-barrier'")==1,'two exact alternate role inputs')
    s=s.replace("request(donor,args,ids,0,8,'measured'","request(donor,args,I.select(dataset,'measured'),0,8,'measured'",1)
    s=s.replace("request(donor,args,ids,1,1,'retirement-barrier'","request(donor,args,I.select(dataset,'retirement-barrier'),1,1,'retirement-barrier'",1)
    s=s.replace("dict(source=sr, token_ids=ids, input_tokens=32768)",
                "dict(source=sr, input_tokens=32768, input_protocol=dataset, token_ids=ids)",1)
    files['performance_service_client.py']=s.encode();counts['performance_service_client.py']=count
    s=files['server090.py'].decode()
    need(s.count("('MXR_','MST_MXR_','QWEN36_DELTALOG','DLOG_')")==1 and
         s.count("'BOLE_', 'BOLE111_', 'DENSE_OPPORTUNITY090_')")==1,'two exact common environment cleanup seams')
    s=s.replace("('MXR_','MST_MXR_','QWEN36_DELTALOG','DLOG_')",
                "('MXR_','MST_MXR_','QWEN36_DELTALOG','DLOG_','HYPIC_')",1)
    s=s.replace("'BOLE_', 'BOLE111_', 'DENSE_OPPORTUNITY090_')",
                "'BOLE_', 'BOLE111_', 'DENSE_OPPORTUNITY090_', 'HYPIC_')",1)
    files['server090.py']=s.encode()
    # The original C1 strong native object and source checks remain. No guessed
    # native table: bind_all/metadata still require real post-native-prefill.
    for name,body in files.items():
        if name.endswith('.py'):compile(body,name,'exec')
    changed={n:dict(before=parent.get(n),after=b)for n,b in files.items()if parent.get(n)!=b}
    return dict(files=files,parent=parent,delta=changed,typed_literal_changes=counts,
        source_ready=False,execution_ready=False,NPU=False,
        pending=['32k source-owned validator/profile/current producer and input packet identity join',
                 'real native32k prefill physical pages/slots/RoPE/FA16+GDN48 observation',
                 '32k input identity embeddings require bounded evidence representation',
                 'layerwise/full-prefix lossless numeric capture: whole before_FA alone exceeds384MiB',
                 'actual independent32k math/STATE/HTTP; fixed1024 strict timing source adaptation'])


def inverse(b):
    out=dict(b['files'])
    need({n for n in out if b['parent'].get(n)!=out[n]}==set(b['delta']),'all-and-only32k delta')
    for n,r in b['delta'].items():
        need(out[n]==r['after'],'exact successor bytes')
        if r['before']is None:out.pop(n)
        else:out[n]=r['before']
    need(out==b['parent'],'entire actual V3 source restored')
    return out


def native_configuration(b):
    # Typed operands for the EXISTING native-only owning producer. They are
    # not a source ticket or a substitute for its complete readset/authority.
    need(b['source_ready']is False,'unbound component only')
    return dict(schema='native32k.existing-owner-configuration/v1',
        owner_prepare='native_2k_owning_source_prepare_v1/prepare_native_2k.py:render',
        owner_gate='native_2k_source.py:execution_window/readset/validate',
        readiness=dict(input_tokens=32768,output_tokens=1,request_count=1,concurrency=1),
        paired_baseline=dict(input_tokens=32768,output_tokens=1024,concurrency=1),
        native_server=dict(max_model_len=40960,max_num_batched_tokens=40960,max_num_seqs=1,
            enforce_eager=True,enable_prefix_caching=False,async_scheduling=False,
            gpu_memory_utilization=0.8,mamba_cache_mode='none',HCCL_DETERMINISTIC='true'),
        performance_arm='native_ar',effective_speculative_config=None,
        VLLM_PLUGINS='ascend,dense_opportunity090',HYPIC_enabled=False,BOLE_enabled=False,
        retain_original_image=True,retain_existing_owned_controller=True,
        physical_NPUs=[4,5,6,7],logical_NPUs=[0,1,2,3],phase_seconds=3600,cleanup_seconds=180,
        source_ready=False,authority_ref=None,
        pending=['derive native-only owning scope/review/renderer from2048 to32768',
                 'fresh source-specific MAIN authority/readset/mount/guest checks',
                 'actual native32k1 metadata/HTTP before paired baseline1024'])


if __name__=='__main__':
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--check',action='store_true');a=p.parse_args()
    if not a.check:print('{"enabled":false,"source_ready":false,"NPU":false}')
    else:
        b=render();inverse(b)
        print(json.dumps(dict(files=len(b['files']),changed=sorted(b['delta']),
            typed_literal_changes=b['typed_literal_changes'],whole_inverse=True,
            source_ready=False,NPU=False,pending=b['pending']),sort_keys=True))

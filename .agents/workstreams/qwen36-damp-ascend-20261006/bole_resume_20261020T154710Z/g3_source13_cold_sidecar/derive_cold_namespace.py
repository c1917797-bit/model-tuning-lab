
"""Default-OFF exact original13 saved-cold namespace derivation."""
import ast,hashlib,argparse,json,os,re,stat
from pathlib import Path
COLD13=(3692,'43fe83203ddbe1394fdead9af54241ed61abad08107f4034f5ee12f3d14c52fb')
def need(v,s):
    if not v:raise ValueError(s)
def derive_cold(text):
    wire=text.encode();need((len(wire),hashlib.sha256(wire).hexdigest())==COLD13,'exact whole actual13 cold source')
    tree=ast.parse(text);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
    offsets=[0]
    for line in text.splitlines(keepends=True):offsets.append(offsets[-1]+len(line))
    def span(n):return offsets[n.lineno-1]+n.col_offset,offsets[n.end_lineno-1]+n.end_col_offset
    def target(n,name):return isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id==name
    edits=[]
    def change(n,after):
        lo,hi=span(n);edits.append(dict(start=lo,end=hi,before=text[lo:hi],after=after))
    guards=[n for n in ast.walk(main)if isinstance(n,ast.Constant)and n.value=='g2_handoff_cold.py']
    need(len(guards)==1,'unique original self-source file guard');change(guards[0],repr('g3_handoff_cold.py'))
    loops=[n for n in main.body if isinstance(n,ast.For)and isinstance(n.target,ast.Name)and n.target.id=='n'
           and ast.dump(n.iter,include_attributes=False)==ast.dump(ast.parse("('sourceio.py','g1_contract.py','g2_contract.py')",mode='eval').body,include_attributes=False)]
    need(len(loops)==1,'unique original three-support byteequal gate');change(loops[0].iter,"('sourceio.py','g1_contract.py')")
    starts=[i for i,n in enumerate(main.body)if target(n,'original_channel')];ends=[i for i,n in enumerate(main.body)if target(n,'second')]
    need(len(starts)==len(ends)==1 and starts[0]<ends[0],'one complete original channel/finalizer loading block')
    first=main.body[starts[0]];last=main.body[ends[0]];lo,_=span(first);_,hi=span(last);indent=' '*first.col_offset
    replacement=["current_supports={n:m['files'][n]for n in('sourceio.py','g1_contract.py','g2_contract.py')}",
        'for r in current_supports.values():C.checked(r)','from g3_cold_namespace import replay',
        "first,second,namespace=replay(C,m,old,originals,v['evidence_source'],v['channel'])"]
    edits.append(dict(start=lo,end=hi,before=text[lo:hi],after=('\n'+indent).join(replacement)))
    keywords=[n for n in ast.walk(main)if isinstance(n,ast.keyword)and n.arg=='original_function_sources']
    need(len(keywords)==1 and isinstance(keywords[0].value,ast.Name)and keywords[0].value.id=='originals','one exact original function-source result field')
    change(keywords[0],'original_function_sources=originals,original_namespace_protocol=namespace,current_support_sources=current_supports')
    edits.sort(key=lambda e:e['start']);need(all(a['end']<=b['start']for a,b in zip(edits,edits[1:])),'disjoint narrow cold edits')
    after=text
    for e in reversed(edits):
        need(after[e['start']:e['end']]==e['before'],'exact original operand');after=after[:e['start']]+e['after']+after[e['end']:]
    inverse=after
    for e in edits:
        need(inverse.count(e['after'])==1,'unique whole cold inverse operand');inverse=inverse.replace(e['after'],e['before'],1)
    need(inverse==text and ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(tree,include_attributes=False),'whole-file and full-AST inverse restores every original cold assertion')
    ast.parse(after)
    return after,dict(schema='bole.exact-G3-isolated-saved-cold-derivation/v1',baseline_whole_bytes=COLD13[0],baseline_whole_sha256=COLD13[1],
        edits=edits,before=text,after=after,whole_text_inverse=True,whole_AST_inverse=True,original_two_function_calls_preserved=True,
        original_guard_semantics_preserved=True,production_handoff_changed=False,software_protocol_changed=False)
def patch_host_cold(text):
    before_tree=ast.parse(text);hits=[n for n in ast.walk(before_tree)if isinstance(n,ast.Constant)and n.value=='g2_handoff_cold.py']
    need(len(hits)==1 and not any(isinstance(n,ast.Constant)and n.value=='g3_handoff_cold.py'for n in ast.walk(before_tree)),'one actual host cold-script anchor after reviewed stager/V hooks')
    n=hits[0];lines=text.splitlines(keepends=True);lo=sum(map(len,lines[:n.lineno-1]))+n.col_offset;hi=sum(map(len,lines[:n.end_lineno-1]))+n.end_col_offset
    old=text[lo:hi];new=repr('g3_handoff_cold.py');after=text[:lo]+new+text[hi:]
    need(after.count(new)==1 and after.replace(new,old,1)==text,'exact post-hook host whole inverse');ast.parse(after)
    return after,dict(schema='bole.exact-G3-host-cold-path-layer/v1',before=text,after=after,before_operand=old,after_operand=new,
        whole_text_inverse=True,only_cold_script_path_changed=True,original_phase_and_success_predicates_unchanged=True)
T=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
LAYER_ROOT=T/'g3_source13_cold_layer_v1'
SOURCE13=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v13/SOURCE_BOUND.json',bytes=994678,sha256='545e09b8bd8e598830cd81ab2ba3be6c5a6b775d1d35f263ed6d3519a4145345')
COLD_REF=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v13/g2_handoff_cold.py',bytes=COLD13[0],sha256=COLD13[1])
HELPER_INPUT=T/'g3_cold_namespace_proposal_v1/g3_cold_namespace.py'
def _pairs(rows):
    result={}
    for key,value in rows:need(key not in result,'duplicate JSON field '+key);result[key]=value
    return result
def _ref(path):
    p=Path(path);a=p.lstat();need(p.is_absolute()and stat.S_ISREG(a.st_mode)and not any(q.is_symlink()for q in(p,*p.parents)),'ordinary absolute source artifact')
    data=p.read_bytes();b=p.lstat()
    need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns),'whole source artifact stable while hashing')
    return dict(path=str(p),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
def _checked(r):
    need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['path'])is str and Path(r['path']).is_absolute()
        and type(r['bytes'])is int and r['bytes']>=0 and type(r['sha256'])is str and re.fullmatch('[0-9a-f]{64}',r['sha256']),'complete strict ordinary full Ref3')
    need(_ref(r['path'])==r,'actual complete source bytes/SHA match');return Path(r['path'])
def _write(root,name,data):
    p=root/name;need(p.parent==root and not p.exists()and not p.is_symlink(),'new exclusive layer file')
    fd=os.open(str(p),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb')as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
    return _ref(p)
def _json_bytes(v):return(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def prepare(source_ref,helper_ref,output_root):
    need(source_ref==SOURCE13 and Path(output_root)==LAYER_ROOT,'only exact actual13 source/new source-only layer root')
    need(helper_ref['path']==str(HELPER_INPUT),'only MAIN-materialized reviewed namespace helper input')
    self_before=_ref(__file__);source_path=_checked(SOURCE13);helper_path=_checked(helper_ref)
    m=json.loads(source_path.read_bytes(),object_pairs_hook=_pairs)
    need(m['files']['g2_handoff_cold.py']==COLD_REF and m['default_enabled']is False and m['prepared_only']is False,'actual immutable13 original cold/defaultOFF source')
    before=_checked(COLD_REF).read_text();helper=helper_path.read_bytes();ht=ast.parse(helper)
    f=[n for n in ht.body if isinstance(n,ast.FunctionDef)and n.name=='replay']
    need(len(f)==1 and[n.arg for n in f[0].args.args]==['C','m','old','originals','evidence_source','channel_ref'],'exact new namespace replay API')
    orders=[n.value for n in ht.body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='_ORDER']
    need(len(orders)==1 and ast.literal_eval(orders[0])==('sourceio.py','g2_contract.py','g1_contract.py','g2_channel.py','g2_finalize.py'),'exact five-module dependency order')
    after,inverse=derive_cold(before);ot=ast.parse(before);nt=ast.parse(after)
    om=next(n for n in ot.body if isinstance(n,ast.FunctionDef)and n.name=='main')
    need(ast.dump(ast.Module(body=[n for n in ot.body if n is not om],type_ignores=[]),include_attributes=False)==
        ast.dump(ast.Module(body=[n for n in nt.body if not(isinstance(n,ast.FunctionDef)and n.name=='main')],type_ignores=[]),include_attributes=False),'complete AST outside main unchanged')
    offsets=[0]
    for line in before.splitlines(keepends=True):offsets.append(offsets[-1]+len(line))
    lo=offsets[om.lineno-1]+om.col_offset;hi=offsets[om.end_lineno-1]+om.end_col_offset
    need(len(inverse['edits'])==4 and all(lo<=e['start']<e['end']<=hi for e in inverse['edits']),'only four reviewed main edits')
    root=Path(output_root);need(not root.exists()and not root.is_symlink()and root.parent==T,'fresh layer leaf');root.mkdir(mode=0o700)
    namespace_ref=_write(root,'g3_cold_namespace.py',helper);cold_ref=_write(root,'g3_handoff_cold.py',after.encode())
    inverse.update(baseline_source=SOURCE13,baseline_cold_ref=COLD_REF,namespace_input_ref=helper_ref,cold_namespace_ref=namespace_ref,cold_helper_ref=cold_ref,
        actual_preparer_ref=self_before,all_edits_inside_main=True,outside_main_AST_unchanged=True,host_not_yet_patched=True,original_cold_kept_unchanged=True,
        original_production_handoff_kept_unchanged=True,prepared_only=True,NPU=False)
    derivation_ref=_write(root,'COLD_DERIVATION.json',_json_bytes(inverse))
    manifest=dict(schema='bole.G3-source13-isolated-cold-modules/v1',root=str(root),baseline_source=SOURCE13,baseline_cold_ref=COLD_REF,actual_preparer_ref=self_before,
        namespace_input_ref=helper_ref,namespace_ref=namespace_ref,helper_ref=cold_ref,derivation_ref=derivation_ref,
        files={'g3_cold_namespace.py':namespace_ref,'g3_handoff_cold.py':cold_ref,'COLD_DERIVATION.json':derivation_ref},
        host_patch=dict(implementation_ref=self_before,function='patch_host_cold',before_context='reviewed host output after G3 stager and validator hooks',
            old_literal='g2_handoff_cold.py',new_literal='g3_handoff_cold.py',unique_AST_constant=True,host_not_yet_patched=True),
        namespace_protocol='bole.explicit-G3-saved-v7-metadata-namespace/v1',original_two_functions=['g2_channel.contract','g2_finalize.owned_channel'],
        software_protocol_changed=False,production_handoff_changed=False,phase_seconds=3600,cleanup_seconds=180,software_lane_seconds=300,fixed_cutoff=1792597630,
        default_enabled=False,prepared_only=True,actual_G3_source_ready=False,actual_cold_probe_executed=False,actual_live_identity_qualified=False,
        model_ready=False,formal_success=False,NPU=False)
    mr=_write(root,'MANIFEST.json',_json_bytes(manifest))
    for r in(SOURCE13,COLD_REF,helper_ref,self_before,*manifest['files'].values(),mr):_checked(r)
    need(_ref(__file__)==self_before,'whole standalone preparer unchanged')
    return dict(module_manifest_ref=mr,namespace_ref=namespace_ref,helper_ref=cold_ref,derivation_ref=derivation_ref,
        prepared_only=True,actual_G3_source_ready=False,actual_cold_probe_executed=False,NPU=False)
def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--prepare',action='store_true')
    p.add_argument('--source-ref');p.add_argument('--helper-ref');p.add_argument('--output-root');a=p.parse_args()
    if not a.prepare:print('{"enabled":false,"NPU":false}');return 0
    need(a.source_ref and a.helper_ref and a.output_root,'exact source/helper fullRefs and new layer leaf required')
    print(json.dumps(prepare(json.loads(a.source_ref,object_pairs_hook=_pairs),json.loads(a.helper_ref,object_pairs_hook=_pairs),a.output_root)));return 0
if __name__=='__main__':raise SystemExit(main())

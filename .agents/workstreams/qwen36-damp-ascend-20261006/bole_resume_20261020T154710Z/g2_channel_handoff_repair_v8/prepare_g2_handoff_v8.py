"""New immutable four-role channel-metadata handoff source; default OFF."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
P=Path(__file__).resolve().parent
SOURCE=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v7/SOURCE_BOUND.json',bytes=542194,sha256='a1f7238ccde08744e90a69a30b316bc10bfe1995e57d3898ced46779ee067032')
FAILED_OWNER=dict(path='/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v7/RESULT.json',bytes=633477,sha256='ab8b73874ef56ddefe08d6f62d926bdad6d752c6eeb8bed0154231a1e81c9421')
CHANNEL=dict(path='/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v7/dense/receipts/STREAM/CHANNEL.json',bytes=25738,sha256='0c3a603c3374024cf1f3f68eb6c55d22f1605233d93369777c4963a28b50ed98')
ROOT=Path('/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v8');OUT=ROOT.with_name('run-'+ROOT.name)
COLLECTOR_SHA='ce4f5c41be679f0f969b7178e02667461a7f2f601d7c5c8f19c04dabb8f23dd3'
CHANGED=('g2_channel.py','host_service.py','owned_create.py','test_g2_stream.py')
ROLES=('consumer_owner_ref','model_owner_ref','consumer_inspect','model_inspect')


def need(v,s):
    if not v:raise ValueError(s)
def ref(path):
    p=Path(path);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary exact absolute file')
    before=p.stat();h=hashlib.sha256();size=0
    with p.open('rb')as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b);size+=len(b)
    after=p.stat();need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)and size==after.st_size,'stable complete source read')
    return dict(path=str(p),bytes=size,sha256=h.hexdigest())
def checked(r):
    need(type(r)is dict and set(r)=={'path','bytes','sha256'}and ref(r['path'])==r,'exact full Ref3');return Path(r['path'])
def obj(r):return json.loads(checked(r).read_bytes())
def legacy(r):
    need(type(r)is dict and set(r)in({'path','sha256'},{'path','bytes','sha256'}),'only original Ref2/3');a=ref(r['path']);need(a['sha256']==r['sha256']and('bytes'not in r or a['bytes']==r['bytes']),'actual original SHA+bytes normalization');return a
def write(p,v):
    with Path(p).open('x')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
    return ref(p)
def replace(p,v):
    if Path(p).exists():Path(p).unlink()
    return write(p,v)
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def tests(p):return sum(isinstance(n,ast.FunctionDef)and n.name.startswith('test_')for n in ast.walk(ast.parse(Path(p).read_bytes())))


def pair(text,old,new):
    need(text.count(new)==1,'one exact declared handoff edit');return text.replace(new,old,1)


def inverse(name,text):
    if name=='g2_channel.py':
        return pair(text,'',"    from g2_handoff import verify as verify_metadata\n    verify_metadata(C,source_ref,v)\n")
    if name=='host_service.py':
        a=text.index('  from g2_handoff import stage_saved_probe\n');b=text.index('  if not a.cpu_only:\n',a);block=text[a:b]
        need(block.count("summary['handoff_cold_release']=close(cold)")==1 and block.count("child(cold,'HANDOFF-COLD'")==1,'one explicit sequential Devices[] full cold gate')
        text=text[:a]+text[b:]
        text=pair(text,'',"   from g2_handoff import ChannelWriter\n   writer=ChannelWriter(C,sr)\n")
        text=pair(text,"   summary['stream_channel']=bind_stream(C,c,S,source_ref=sr,model_ctl=ctl,cpu_ctl=consumer,\n","   summary['stream_channel']=bind_stream(writer,c,S,source_ref=sr,model_ctl=ctl,cpu_ctl=consumer,\n")
        return pair(text,'',"   summary['metadata_handoff']=writer.complete(summary['stream_channel'])\n")
    if name=='owned_create.py':
        a=text.index(' excluded={}\n');b=text.index(' # Exact immutable file mounts',a);text=text[:a]+text[b:]
        return pair(text,'',"  if str(p)in excluded:\n   C.checked(r)\n   if r!=excluded[str(p)]:raise ValueError('exact known Ref only; never a prefix exemption or source-check bypass')\n   continue\n")
    if name=='test_g2_stream.py':
        start=text.index('  import g2_handoff as HANDOFF\n');end=text.index("  cr=C.write(stream/'CHANNEL.json'",start)
        text=text[:start]+"  m=dict(stream_consumer_source=consumer,stream_channel_root=str(stream),model_receipt_root=str(receipt))\n  sr=C.write(root/'source.json',m)\n"+text[end:]
        return pair(text,'    consumer_owner_ref=own,model_owner_ref=own,limits=dict(raw_cap=G2.RAW_CAP,\n',"    consumer_owner_ref=copied['consumer_owner_ref'],model_owner_ref=copied['model_owner_ref'],consumer_inspect=copied['consumer_inspect'],model_inspect=copied['model_inspect'],metadata_handoff=ledger,limits=dict(raw_cap=G2.RAW_CAP,\n")
    raise ValueError('no undeclared source inverse '+name)


def fixture_assertions(before,after):
    def methods(text):
        return{n.name:ast.dump(n,include_attributes=False)for n in ast.walk(ast.parse(text))if isinstance(n,ast.FunctionDef)and n.name.startswith('test_')}
    need(methods(before)==methods(after)and len(methods(before))==15,'all original15 stream test bodies/negative/math assertions exactly preserved; only metadata fixture extended')


def evidence(sr,owner_ref):
    need(sr==SOURCE and owner_ref==FAILED_OWNER,'only preserved actual failed v7 source/model owner, never arbitrary or future success')
    m=obj(sr);o=obj(owner_ref);ch=obj(CHANNEL);out=Path(owner_ref['path']).parent;refs=[sr,owner_ref,CHANNEL]
    need(o['source']==sr and o['primary']=="ValueError('one bounded actual model smoke client')"and o['secondary']==[]and o['cpu_only']is False and o['source_before']and o['source_before']==o['source_after']and o['source_before'].get(sr['path'])==sr['sha256'],'actual clean source-stable v7 failure, not qualification')
    need(m['service_required_sameimage_software_cases']==266 and m['service_software_scope']['new_current_cases']==52 and ch['source']==sr and o['summary']['stream_channel']==CHANNEL,'exact actual266 parent source and published channel')
    need((m['files']['g2_stream_owner.py']['bytes'],m['files']['g2_stream_owner.py']['sha256'])==(5917,'3d7d61e06e2de7e0680f4503530267bbb0cd87402b287d037cf89dd1562db8af'),'full v7 owning commandline/lifetime guard preserved')
    full={role:legacy(ch[role])for role in ROLES};refs.extend(full.values())
    owner=obj(full['consumer_owner_ref']);inspection=obj(full['consumer_inspect']);rows=json.loads(inspection['stdout']);need(len(rows)==1,'one actual retained live inspect snapshot')
    mounts={x['Destination']:[x['Source'],x['RW']]for x in rows[0]['Mounts']};need(mounts==owner['mounts']and rows[0]['Id']==owner['cid']and rows[0]['HostConfig']['Devices']in(None,[]),'actual original consumer expected/observed mounts and Devices[]')
    for role,r in full.items():need(not any(Path(r['path'])==Path(dst)or Path(r['path']).is_relative_to(Path(dst))for dst in mounts),'actual four host-exact metadata files are all outside the complete actual consumer mount closure '+role)
    src=Path(ch['consumer_source']['path']);need(any(src==Path(dst)or src.is_relative_to(Path(dst))for dst in mounts),'actual static consumer source was visible; no unknown Ref guessed')
    for role in('consumer_inspect','model_inspect'):need(set(ch[role])=={'path','sha256'},'actual original inspect Ref2 needs full-byte normalization')
    stderr=ref(out/'cpu-consumer/stream-consumer.stderr');trace=checked(stderr).read_text();need('g2_channel.py'in trace and'ordinary exact evidence bytes'in trace and'contract'in trace,'actual pre-Torch consumer full source-Ref read failure');refs.append(stderr)
    for role in('cpu-preflight','dense','cpu-consumer'):
        r=ref(out/role/'cleanup.json');v=obj(r);need(v['stopped']is True and v['retained']is True and v['errors']==[],'all actual failed owners stopped retained');refs.append(r)
    child=legacy(o['summary']['actual_software_child']);v=obj(child);need(v['exit_code']==0 and v['child_termination_observed']is True,'actual266 child completed; next source still reruns all controls');so=legacy(v['stdout_ref']);matches=[]
    for line in checked(so).read_text().splitlines():
        try:x=json.loads(line)
        except ValueError:continue
        if type(x)is dict and x.get('schema')=='bole.G2-explicit-combined-software-gate/v1':matches.append(x)
    need(len(matches)==1 and matches[0]['source']==sr and matches[0]['tests']==266 and matches[0]['historical_cases']==214 and matches[0]['current_cases']==52 and matches[0]['all_tests_passed']is True,'actual full266 software only, not a model pass')
    refs.extend([child,so,legacy(v['stderr_ref']),legacy(o['summary']['CPU_report']),*map(legacy,o['summary']['MTP_load_receipts'])])
    need(len(o['summary']['MTP_load_receipts'])==4,'all4 actual native loads occurred before downstream transport failure')
    return m,refs,dict(failed_source=sr,failed_owner=owner_ref,failed_channel=CHANNEL,failed_four_full_refs=full,total_actual_copy_bytes=sum(r['bytes']for r in full.values()),actual_all_four_original_metadata_unmounted=True,actual_static_consumer_source_visible=True,actual266_software_pass_only=True,actual_model_pass=False)


def main():
    parser=argparse.ArgumentParser(allow_abbrev=False);parser.add_argument('--execute',action='store_true')
    for n in('failed-owner-ref','prior-builder-ref','manifest-ref'):parser.add_argument('--'+n)
    a=parser.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    need(all(vars(a).values()),'exact failed owner/correct original collector/reviewed packet Refs required')
    failed,observed,cause=evidence(SOURCE,json.loads(a.failed_owner_ref));br=json.loads(a.prior_builder_ref);need(br['sha256']==COLLECTOR_SHA,'unchanged original source-owned canonical argv/readset collector');H=module('_g2_v8_original_collector',checked(br));mr=json.loads(a.manifest_ref);manifest=obj(mr);need(mr==ref(P/'MANIFEST.json'),'current externally reviewed exact packet manifest')
    for name,w in manifest['overlay_files'].items():
        actual=ref(P/name);need((actual['bytes'],actual['sha256'])==(w['bytes'],w['sha256'])and Path(w['path']).name==name,'portable actual bytes/SHA, advisory paths are lineage only '+name)
    old=Path(failed['root']);need(not any(p.exists()for p in(ROOT,OUT,Path(str(OUT)+'-CPU'))),'fresh immutable v8 source/model/CPU leaves; all failures retained')
    for name in CHANGED:need(inverse(name,(P/name).read_text())==checked(failed['files'][name]).read_text(),'exact declared whole-file metadata/lifecycle/fixture inverse '+name)
    fixture_assertions(checked(failed['files']['test_g2_stream.py']).read_text(),(P/'test_g2_stream.py').read_text())
    baseline=H.collect(SOURCE);g1=failed['g2_predecessor'];parent=obj(g1['source']);historical=H.collect(g1['source'])
    shutil.copytree(old,ROOT,ignore=shutil.ignore_patterns('__pycache__'));(ROOT/'SOURCE_BOUND.json').rename(ROOT/'FAILED_G2_V7_SOURCE_BOUND.json')
    for n in('COMMANDS.json',failed['command_scope']['compatibility_file']):(ROOT/n).rename(ROOT/('FAILED_G2_V7_'+n))
    for n in manifest['overlay_files']:shutil.copyfile(P/n,ROOT/n)
    (ROOT/'contract090.py').write_text(H.outputs((old/'contract090.py').read_text(),str(OUT)));shutil.copyfile(P/'MANIFEST.json',ROOT/'G2_HANDOFF_V8_MANIFEST.json')
    changed={*CHANGED,'contract090.py','G2_STREAM_EDITS_V1.json'}
    for n,r in failed['files'].items():
        if n not in changed:need((ROOT/n).read_bytes()==checked(r).read_bytes(),'all original math/128transactions/consumer/finalizer/argv8/source/resource/other controls unchanged '+n)
    delta={}
    for n,r in parent['files'].items():
        if(ROOT/n).is_file()and Path(r['path']).is_relative_to(Path(parent['root'])):
            before=checked(r).read_text();after=(ROOT/n).read_text()
            if before!=after:delta[n]=dict(before=r,after=ref(ROOT/n),edits=[dict(before=before,after=after)])
    replace(ROOT/'G2_STREAM_EDITS_V1.json',dict(schema='bole.exact-G2-stream-inverse-to-G1v2/v1',baseline=g1['source'],files=delta,original_math_unchanged=True,original_G1v2_full_controls_rerun_separately=True))
    replace(ROOT/'G2_HANDOFF_EDITS_V8.json',dict(schema='bole.exact-four-role-metadata-handoff-inverse/v8',baseline=SOURCE,files={n:dict(before=failed['files'][n],after=ref(ROOT/n),edits=[dict(before=(old/n).read_text(),after=(ROOT/n).read_text())])for n in(*CHANGED,'contract090.py')},all_original_stream_test_assertions_unchanged=True,whole_v7_argv_owner_byteexact=True,original_math_consumer_finalizer_resources_unchanged=True))
    m=json.loads(json.dumps(failed));m.pop('prepared_template',None);m.update(root=str(ROOT),output_root=str(OUT),model_receipt_root=str(OUT/'dense/receipts'),prepared_only=True,default_enabled=False)
    def remap(r):return ref(ROOT/Path(r['path']).relative_to(old))if Path(r['path']).is_relative_to(old)else r
    m['files']={n:remap(r)for n,r in m['files'].items()}
    for n in(*manifest['overlay_files'],'G2_HANDOFF_V8_MANIFEST.json','G2_HANDOFF_EDITS_V8.json'):m['files'][n]=ref(ROOT/n)
    for key in('service_runtime_source_snapshots','g1_overlay','g1_repair_v2_overlay','g2_overlay'):m[key]={n:remap(r)for n,r in m.get(key,{}).items()}
    for row in m['g2_builder_portability_v2']['inventory'].values():row['actual_bound']=m['files'][Path(row['actual_bound']['path']).name]
    m['stream_channel_root']=str(OUT/'dense/receipts/STREAM');m['stream_channel_contract_path']=str(OUT/'dense/receipts/STREAM/CHANNEL.json');m['stream_consumer_source']=m['files']['g2_consumer.py']
    added=sum(tests(ROOT/n)for n in manifest['overlay_files']if n.startswith('test_g2_handoff'))
    m['service_software_scope']=dict(m['service_software_scope'],new_current_cases=52+added);m['service_required_sameimage_software_cases']=266+added
    m['g2_metadata_handoff_v8']=dict(cause,manifest=mr,actual_preparer=ref(__file__),original266_fresh_rerun_required=True,new_controls=added,whole_v7_bind_argv_and8controls_byteexact=True,production_four_copy_bytes_charged_to_original64MiB_per_rank=True,sameimage_cold_before_any_NPU_required=True,cold_saved_stopped_snapshots_do_not_grant_live_identity=True,original3600_and180_unchanged=True,previous_failed_model_is_not_qualification=True)
    required=H.unique([*baseline['refs'],*historical['refs'],SOURCE,*observed,br,mr,*[ref(P/n)for n in manifest['overlay_files']]])
    m['dependencies']=H.unique([*failed['dependencies'],*required])
    for n in('SOURCE_TEMPLATE.json','SOURCE.json'):replace(ROOT/n,m)
    tr=ref(ROOT/'SOURCE_TEMPLATE.json');q=subprocess.run(['/usr/bin/python3','-I','-B',str(ROOT/'bind_model.py'),'--execute','--reviewed-template-ref',json.dumps(tr),'--component-refs-json',json.dumps(m['component_refs'])],capture_output=True,text=True,timeout=60);need(q.returncode==0,'new exact source binding failed '+q.stdout+q.stderr)
    sr=ref(ROOT/'SOURCE_BOUND.json');bound=obj(sr);sys.path.insert(0,str(ROOT));cc=module('_g2_v8_source_owned_commands',ROOT/'command_contract.py');history=obj(m['command_scope']['historical_ref'])
    commands=dict(schema='bole.G1-actual-bound-commands/v2',source=tr,bound_source=sr,**cc.expected(str(ROOT),str(OUT),sr,tr,m['component_refs']),required_sameimage_software_cases=m['service_required_sameimage_software_cases'],historical_required_sameimage_software_cases=history['required_sameimage_software_cases'],legacy_entrypoints_retained_for_inverse_tests_only=True,actual_G1_execution_claimed=False,G2_stream_protocol=True,actual_G2_execution_claimed=False)
    replace(ROOT/'COMMANDS.json',commands);replace(ROOT/m['command_scope']['compatibility_file'],dict(source=sr,template=tr,commands=ref(ROOT/'COMMANDS.json'),model=commands['model'],CPU=commands['CPU'],required_sameimage_software_cases=m['service_required_sameimage_software_cases']))
    cc.validate(cc.C,sr,bound);current=H.collect(sr);present={r['path']:r for r in current['refs']};need(all(present.get(r['path'])==r for r in required),'complete source/evidence/command/inverse readset closure')
    for f in ROOT.rglob('*.py'):compile(f.read_bytes(),str(f),'exec')
    print(json.dumps(dict(source=sr,commands=ref(ROOT/'COMMANDS.json'),prospective_sameimage_cases=m['service_required_sameimage_software_cases'],original266_fresh_rerun=True,new_controls=added,original_four_actual_copy_bytes=cause['total_actual_copy_bytes'],cold_complete_original_channel_reader_before_NPU=True,actual_sameimage_executed=False,actual_model_executed=False,model_ready=False,NPU=False)));return 0


if __name__=='__main__':raise SystemExit(main())

"""Mechanical 052→056 identity/current-authorization successor. No backend execution."""
import ast,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent/'deltalog-split-scale-numeric-new48h-20261016-052'
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-split-scale-numeric-new24h-v1-061'
OUT='/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061'
AUTH=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/NEW24H_AUTHORITY_20261016.json',bytes=3481,sha256='e8c373b6664a4bdd80012428b686227a6f15c0535b3c57a7654fb7996c02cf28')
EDITS={}
def data(v):return(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def put(n,b):
 p=P/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b.replace(b'\r\n',b'\n'))
def ref(n,b):return dict(path=ROOT+'/'+n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def change(n,a,b,count=1):
 s=(P/n).read_text(encoding='utf8');assert s.count(a)==count,(n,a,s.count(a));put(n,s.replace(a,b).encode());EDITS.setdefault(n,[]).append([a,b])
def main():
 old=json.loads((B/'SOURCE_TEMPLATE.json').read_bytes());oldroot=old['root']
 for n in old['files']:
  raw=(B/n).read_bytes();text=raw.decode()
  if n.endswith('.py')and not n.startswith(('fixtures/','fixtures043/','fixtures_repair3/'))and n not in('assemble052.py','prepare_transport.py'):
   for a,b in((oldroot,ROOT),('deltalog-split-scale-numeric-new48h-052','deltalog-split-scale-numeric-new24h-056'),('deltalog-split-scale-numeric-new48h-MAIN-052','deltalog-split-scale-numeric-new24h-MAIN-061')):
    if a in text:EDITS.setdefault(n,[]).append([a,b]);text=text.replace(a,b)
  put(n,text.encode())
 change('host.py','START,CUT=1791962297,1792135097','START,CUT=1792134133,1792220533')
 change('host.py',"AUTH_SHA='71211e77fc870a8c94a7f80424925e38e1e092b9374d3a6a1066960ea74fbf99'","AUTH_SHA='e8c373b6664a4bdd80012428b686227a6f15c0535b3c57a7654fb7996c02cf28'")
 change('bridge_io.py'," a=obj(r);need(r['sha256']=='71211e77fc870a8c94a7f80424925e38e1e092b9374d3a6a1066960ea74fbf99'and a['cutoff_epoch']==1792135097 and 1791962297<=time.time()<1792135097-2880,'fixed authority/whole owner2880 budget')"," from window056 import require_current\n require_current(r,obj)")
 change('qwen36_deltalog_fresh/provider.py',"{'start':1791962297,'cutoff':1792135097}or not 1791962297<=time.time()<1792135097","{'start':1792134133,'cutoff':1792220533}or not 1792134133<=time.time()<1792220533")
 change('qwen36_deltalog_fresh/provider.py'," life=v.admit_receipt(m['composite_source_ref'],lifecycle_ref)"," from historical022056 import admit as historical_admit\n life=historical_admit(api,m['composite_source_ref'],lifecycle_ref)")
 change('bind052.py',"receipt=api.admit_receipt(old['composite_source_ref'],old['composite_cpu_owner_ref'])","receipt=__import__('historical022056').admit(m['composite_api_ref'],old['composite_source_ref'],old['composite_cpu_owner_ref'])")
 change('bind052.py',"tr=json.loads(a.template_ref);C.need(","C.window(__import__('window056').AUTH)\n tr=json.loads(a.template_ref);C.need(")
 change('run031.py',"AUTH=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/NEW48H_AUTHORITY_20261014.json',bytes=3591,sha256='71211e77fc870a8c94a7f80424925e38e1e092b9374d3a6a1066960ea74fbf99')","from window056 import AUTH")
 change('run052.py',"run-'+a.phase+'-MAIN-20261016-001","run-'+a.phase+'-MAIN-20261016-NEW24H-001")
 change('inverse_repair3.py',' from inverse052 import undo as undo052',' from inverse056 import undo as undo056\n text=undo056(name,text)\n from inverse052 import undo as undo052')
 change('test_031.py','from inverse052 import undo','from inverse056 import through052 as undo')
 s=(P/'domain_consumer.py').read_text();tree=ast.parse(s);node=next(n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='PINNED'for t in n.targets));pins=ast.literal_eval(node.value)
 for n in pins:pins[n]=hashlib.sha256((P/n).read_bytes()).hexdigest()
 lines=s.splitlines(True);lines[node.lineno-1:node.end_lineno]=['PINNED = '+repr(pins)+'\n'];put('domain_consumer.py',''.join(lines).encode())
 put('EDITS056.json',data(EDITS))
 put('dependencies/old022_composite.py',(P.parent/'deltalog-composite-admission-new48h-20261015-022/composite.py').read_bytes())
 names=set(old['files'])|{'prepare056.py','window056.py','historical022056.py','inverse056.py','EDITS056.json','test_056.py','HANDOFF056.md','dependencies/old022_composite.py','OLD022_SOURCE.json','OLD022_OWNER.json','OLD48H_AUTHORITY.json','NEW24H_AUTHORITY.json'}
 for n in names:put(n,(P/n).read_bytes())
 m=json.loads(json.dumps(old).replace(oldroot,ROOT));m.update(root=ROOT,exact_output_root=OUT,prepared_only=True,window=dict(start=1792134133,cutoff=1792220533),authority_ref=AUTH)
 m['historical_051_build_authority_unchanged']=True;m['historical_022_role']='ABI/state predecessor only; source-derived exact archive reader removes expired current-clock condition, not old authority/window/cert gates'
 m['files']={n:ref(n,(P/n).read_bytes())for n in sorted(names)};put('SOURCE_TEMPLATE.json',data(m));tr=ref('SOURCE_TEMPLATE.json',data(m))
 cmds=json.loads((B/'COMMANDS052.json').read_bytes());cmds=json.loads(json.dumps(cmds).replace(oldroot,ROOT).replace('deltalog-split-scale-numeric-new48h-052','deltalog-split-scale-numeric-new24h-056'));cmds['template']=tr
 for args in cmds['commands'].values():args[args.index('--template-ref')+1]=json.dumps(tr)
 cmds.update(current_authority=AUTH,window=m['window'],old_window_failures_unchanged=True);put('COMMANDS056.json',data(cmds))
 files=[dict(relative_path=n,ref=r,text=(P/n).read_bytes().decode())for n,r in m['files'].items()]+[dict(relative_path='SOURCE_TEMPLATE.json',ref=tr,text=data(m).decode())]
 for v in files:
  b=v['text'].encode();assert b'\r'not in b and len(b)==v['ref']['bytes']and hashlib.sha256(b).hexdigest()==v['ref']['sha256']
  if v['relative_path'].endswith('.py'):ast.parse(b)
 put('BYTE_EXACT_DELIVERY056.json',data(dict(schema='deltalog.new24h-source-preparation/v056',template=tr,files=files,actual_CPU=False,actual_NPU=False,model_ready=False)))
 prior=P.parent/'deltalog-mixed-precast-new48h-20261015-043-repair3';pm=json.loads((prior/'SOURCE_TEMPLATE.json').read_bytes());known={r['sha256']:(n,r)for n,r in pm['files'].items()if (prior/n).is_file()and hashlib.sha256((prior/n).read_bytes()).hexdigest()==r['sha256']and(prior/n).stat().st_size==r['bytes']}
 known.update({m['reviewed_split_build_ref']['sha256']:('ACTUAL051_BUILD.json',m['reviewed_split_build_ref']),m['composite_api_ref']['sha256']:('dependencies/old022_composite.py',m['composite_api_ref']),AUTH['sha256']:('NEW24H_AUTHORITY.json',AUTH),'71211e77fc870a8c94a7f80424925e38e1e092b9374d3a6a1066960ea74fbf99':('OLD48H_AUTHORITY.json',dict(path=AUTH['path'].replace('NEW24H_AUTHORITY_20261016','NEW48H_AUTHORITY_20261014'),bytes=3591,sha256='71211e77fc870a8c94a7f80424925e38e1e092b9374d3a6a1066960ea74fbf99')),'b5f4c0798f2fab7fb3c706666c38b6eab7318fa6a55e40191dd419bb6aaacb6c':('OLD022_SOURCE.json',dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-composite-admission-new48h-v1-022/BOUND_SOURCE.json',bytes=162171,sha256='b5f4c0798f2fab7fb3c706666c38b6eab7318fa6a55e40191dd419bb6aaacb6c')),'9d6740da1d95f281aab6da1f459e1540a798652af695ee5ec6922e35d4be6c61':('OLD022_OWNER.json',dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-dl-composite022-cpu-new48h-MAIN-20261015-001/RESULT.json',bytes=1372,sha256='9d6740da1d95f281aab6da1f459e1540a798652af695ee5ec6922e35d4be6c61')),'3d24eabdd0ecdc0f76c2d8eb414a3436bd25f9f06f407db0f9751016c3ab2ed1':('REGRESSION_INPUTS.json',dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-precast-empirical-new48h-v1-016/REGRESSION_INPUTS.json',bytes=51545,sha256='3d24eabdd0ecdc0f76c2d8eb414a3436bd25f9f06f407db0f9751016c3ab2ed1'))})
 copies=[];patch=[]
 for n,r in m['files'].items():
  previous=known.get(r['sha256'])
  if previous and previous[1]['bytes']==r['bytes']:copies.append(dict(destination=r,source=previous[1],relative_path=n))
  else:patch.append(dict(relative_path=n,ref=r))
 put('EXISTING_SOURCE_COPY_MAP056.json',data(dict(template=tr,same_peer_only=True,copies=copies,apply_patch_only=patch,template_apply_patch=tr,copy_is_not_execution=True)))
 print(json.dumps(dict(template=tr,files=len(files))))
if __name__=='__main__':main()

"""Whole actual CPU owner positives; exact Ref-only local evidence transport.

Transport serves only verified original Ref bytes available in this conversation.
It never runs the qualification entry, fabricates a completed result, or changes
runtime source/owner state. Actual MAIN getter recomputes its own ordered readset.
"""
import copy,hashlib,importlib.util,json,sys,types,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
P=Path(__file__).resolve().parent;W=P.parent.parent;sys.path.insert(0,str(P))
import readback_cpu as R
FIXTURE=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/G2_V11_READER_V2_ORDERED_READSET.json',bytes=773410,sha256='33d962e58becc24e26ab133cfc5dce15083db3872724e7caf257981991979500')


class ExactTransport:
 def __init__(self):self.rows={}
 def add(self,r,path):
  path=Path(path);b=path.read_bytes()
  R.need(type(r)is dict and set(r)=={'path','bytes','sha256'}and (len(b),hashlib.sha256(b).hexdigest())==(r['bytes'],r['sha256']),'actual whole Ref-specific local transport')
  R.need(r['path']not in self.rows or self.rows[r['path']][0]==r,'no conflicting original Ref route');self.rows[r['path']]=(r,path)
 def catalog(self,root):
  root=Path(root)
  for name,r in json.loads((root/'ACTUAL_REFS.json').read_bytes()).items():self.add(r,root/name)
 def ref(self,path):
  key=str(path);R.need(key in self.rows,'unknown original Ref has no local transport '+key);r,p=self.rows[key];self.add(r,p);return r
 def checked(self,r):
  R.need(self.ref(r['path'])==r,'original full actual Ref before local materialized read');return self.rows[r['path']][1]
 def obj(self,r):return R.parse(self.checked(r).read_bytes())
 def source(self,r,name):
  body=self.checked(r).read_bytes();m=types.ModuleType(name);m.__file__=r['path'];sys.modules[name]=m;exec(compile(body,r['path'],'exec'),m.__dict__);return m


class ActualOwnerControls(unittest.TestCase):
 def setUp(self):
  self.t=t=ExactTransport()
  for root in ('g2_review_v11_source','g2_review_v11_cpu_actual','g2_review_v11_cpu_reader_v1_failure','g2_review_v8_cpu','g2_review_v7'):t.catalog(W/root)
  t.add(FIXTURE,W/'g2_review_v11_source/G2_V11_READER_V2_ORDERED_READSET.json');self.m=t.obj(R.SOURCE);m=self.m;self.ordered=t.obj(FIXTURE)
  self.assertEqual(self.ordered['source'],R.SOURCE);self.assertEqual(len(self.ordered['readset']),3379);self.assertEqual(len({r['path']for r in self.ordered['readset']}),3280)
  for name,r in self.ordered['helpers'].items():self.assertEqual(r,m['files'][name+'.py'])
  originals=m['g2_callee_contract_v10']['original025_sources']
  for name,r in originals.items():t.add(r,W/'g1_review_v2'/(name+'.py'))
  packet=W/'bole_service_proposals/g2_callee_contract_repair_v10'
  for name in ('owned_create.py','owned_substrate.py','sourceio.py','g2_handoff.py','g2_cold_parent_output.py','g2_contract.py'):t.add(m['files'][name],packet/name)
  t.add(m['files']['external025.py'],W/'g1_review_v2/external025.py');t.add(m['files']['g2_host_adapter.py'],W/'bole_service_proposals/g2_channel_handoff_repair_v8/g2_host_adapter.py')
  self.enterContext(patch.object(R,'ref',t.ref));self.enterContext(patch.object(R,'checked',t.checked))
  names=('sourceio','g2_handoff','g2_cold_parent_output','owned_create','g2_contract');saved={n:sys.modules.get(n)for n in names}
  def restore():
   for n,v in saved.items():
    if v is None:sys.modules.pop(n,None)
    else:sys.modules[n]=v
  self.addCleanup(restore)
  C=t.source(m['files']['sourceio.py'],'sourceio');C.ref=t.ref;C.checked=t.checked;C.obj=t.obj
  t.source(m['files']['g2_contract.py'],'g2_contract');t.source(m['files']['g2_handoff.py'],'g2_handoff');t.source(m['files']['g2_cold_parent_output.py'],'g2_cold_parent_output');creator=t.source(m['files']['owned_create.py'],'owned_create')
  c=t.source(originals['model_contract'],'_readback_actual_original025_facade');c.obj=t.obj;c.sha=lambda path:t.ref(path)['sha256']
  external=t.source(m['files']['external025.py'],'_readback_actual_external');ha=t.source(m['files']['g2_host_adapter.py'],'_readback_actual_CPU_adapter')
  self.c=c;self.mods=NS(owned_create=creator,actual_ordered_readset=self.ordered['readset']);self.validator=R.safety_validator(m,NS(external025=external,g2_host_adapter=ha),c)
 def actual(self,leaf):
  root=R.CPU_OUT/leaf;owned=self.t.obj(self.t.ref(root/'OWNED.json'));create=self.t.obj(R.normalize(owned['create_receipt']));return root,owned,create
 def test_two_actual_full_owner_chains_reexecute_original_ordered_create_and_inspect(self):
  v8=self.t.obj(R.V8_SOURCE);old=self.t.obj(self.m['g2_metadata_handoff_v8']['failed_source']);rows=[]
  for name,alias in (('cpu-preflight',Path(v8['output_root'])/'cpu-preflight'),('candidate',Path(old['stream_channel_root']))):
   root,owned,create=self.actual(name);expected=R.ordered_owner_expected(self.m,R.SOURCE,root,owned,self.c,self.mods);self.assertEqual(self.validator.create(expected),create['requested_argv']);self.assertEqual(len(create['requested_argv']),6000 if name=='cpu-preflight'else 5992)
   row,_,_=R.owner_chain(self.m,R.SOURCE,root,self.t.ref(root/'cleanup.json'),self.c,self.validator,alias,self.mods);rows.append(row)
  self.assertNotEqual(rows[0]['cid'],rows[1]['cid']);self.assertEqual(rows[0]['formal_deadline_monotonic'],rows[1]['formal_deadline_monotonic'])
 def test_actual_original_v1_bug_reproduces_exact_first_mount_operand86(self):
  for name in ('cpu-preflight','candidate'):
   root,owned,create=self.actual(name);wrong=self.validator.create(owned);got=create['requested_argv'];self.assertEqual(len(wrong),len(got));self.assertNotEqual(wrong,got);self.assertEqual(next(i for i,(a,b)in enumerate(zip(got,wrong))if a!=b),86);self.assertIn('destination=/usr/local/Ascend/driver,readonly',got[86]);self.assertIn('destination=/adakv-results',wrong[86])
 def test_actual_create_mount_order_source_value_extra_and_readonly_mutations_refused(self):
  for name in ('cpu-preflight','candidate'):
   root,owned,create=self.actual(name);expected=R.ordered_owner_expected(self.m,R.SOURCE,root,owned,self.c,self.mods);mounts=[i+1 for i,x in enumerate(create['requested_argv'])if x=='--mount']
   for kind in ('order','source','extra','readonly','CID'):
    bad=copy.deepcopy(create);argv=bad['requested_argv'];i,j=mounts[:2]
    if kind=='order':argv[i],argv[j]=argv[j],argv[i]
    elif kind=='source':argv[i]=argv[i].replace('source=/usr/local/Ascend/driver','source=/unknown/source')
    elif kind=='extra':argv[i:i]=['--mount','type=bind,source=/unknown,destination=/unknown,readonly']
    elif kind=='readonly':argv[i]=argv[i].removesuffix(',readonly')
    else:bad['stdout']='b'*64+'\n'
    with self.subTest(leaf=name,kind=kind),self.assertRaises(ValueError):R.create_gate(bad,owned,expected,self.validator)
 def test_actual_reconstructed_owner_mount_extra_value_readonly_changes_refused(self):
  for name in ('cpu-preflight','candidate'):
   root,owned,_=self.actual(name)
   for kind in ('source','extra','readonly'):
    bad=copy.deepcopy(owned)
    if kind=='extra':bad['mounts']['/unknown']=['/unknown',False]
    elif kind=='source':bad['mounts']['/usr/local/Ascend/driver'][0]='/unknown'
    else:bad['mounts']['/usr/local/Ascend/driver'][1]=True
    with self.subTest(leaf=name,kind=kind),self.assertRaises(ValueError):R.ordered_owner_expected(self.m,R.SOURCE,root,bad,self.c,self.mods)
 def test_actual_readset_order_change_refuses_complete_original_argv(self):
  # Source-owned source_gate recomputes this order. A caller-provided reordering
  # of two distinct RO inputs cannot be accepted by the exact create guard.
  root,owned,create=self.actual('cpu-preflight');changed=list(self.mods.actual_ordered_readset);indices=[i for i,r in enumerate(changed)if not Path(r['path']).is_relative_to(R.ROOT)]
  i,j=indices[:2];changed[i],changed[j]=changed[j],changed[i];mods=NS(owned_create=self.mods.owned_create,actual_ordered_readset=changed);expected=R.ordered_owner_expected(self.m,R.SOURCE,root,owned,self.c,mods)
  with self.assertRaises(ValueError):R.create_gate(create,owned,expected,self.validator)


if __name__=='__main__':unittest.main()

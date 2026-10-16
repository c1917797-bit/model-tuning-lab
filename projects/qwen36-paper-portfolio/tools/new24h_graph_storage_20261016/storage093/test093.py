import importlib.util,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import sealed_storage093 as S, capture093 as C
class Tests(unittest.TestCase):
 def test_cold(self):
  r=subprocess.run([sys.executable,'-I','-B',str(P/'capture093.py')],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);self.assertFalse(json.loads(r.stdout)['enabled'])
 def test_all_actual_cids_and_fail_preserved(self):
  self.assertEqual(tuple(map(len,S.CIDS)),(1,2,2));self.assertEqual(S.EXITS,((0,),(0,0),(1,0)));self.assertEqual(len(set(sum(S.CIDS,()))),5);self.assertEqual(S.OWNER_PINS[2][1],'412680c3460d4921f32edd3a0cf467186f8639d16e07ee0a1b5e89cdfed513e1')
 def test_unchanged_allocation_rows(self):
  good=dict(reservations=[dict(leaf=str(S.ROOT/n),stage='cpu'if i in(0,3)else'numeric',budget_bytes=(1 if i in(0,3)else 33)*S.GIB)for i,n in enumerate(('a','b','c','d','e','f'))]);S.rows(good)
  for mutate in(lambda r:r.append(r[0]),lambda r:r[0].update(budget_bytes=0),lambda r:r[0].update(leaf='/outside/a'),lambda r:r[0].update(ignored=True)):
   bad=json.loads(json.dumps(good));mutate(bad['reservations'])
   with self.assertRaises(ValueError):S.rows(bad)
 def test_actual_ref_detects_change(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'x';p.write_text('{}');rr=S.ref(p);self.assertEqual(S.read(rr),{});p.write_text('{"x":1}')
   with self.assertRaises(ValueError):S.read(rr)
 def test_real_write_scan_fixtures(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);leaf=root/'closed';leaf.mkdir();proc=root/'proc';p=proc/'123';(p/'fd').mkdir(parents=True);(p/'fdinfo').mkdir();(p/'maps').write_text('');f=leaf/'raw';f.write_bytes(b'x')
   # A source-bound scan must reject a shared writable mapping even without FD.
   (p/'maps').write_text('100-200 rw-s 0000 00:00 1 '+str(f)+'\n')
   with self.assertRaises(ValueError):C.write_scan(proc,[leaf])
   (p/'maps').write_text('100-200 r--s 0000 00:00 1 '+str(f)+'\n');self.assertTrue(C.write_scan(proc,[leaf])['no_open_write_fds_or_shared_writable_maps'])
 @unittest.skipUnless(sys.platform=='linux','real /proc writer check must execute in sameimage Linux preflight')
 def test_real_short_writer(self):
  with tempfile.TemporaryDirectory()as d:
   leaf=Path(d);target=leaf/'raw';ready=leaf/'ready';code="import pathlib,time;f=open(%r,'wb');pathlib.Path(%r).touch();time.sleep(10)"%(str(target),str(ready));p=subprocess.Popen([sys.executable,'-I','-B','-c',code])
   try:
    import time
    end=time.monotonic()+3
    while not ready.exists()and time.monotonic()<end:time.sleep(.02)
    self.assertTrue(ready.exists())
    with self.assertRaises(ValueError):C.write_scan(leaves=[leaf])
   finally:p.terminate();p.wait(timeout=3)
   self.assertTrue(C.write_scan(leaves=[leaf])['no_open_write_fds_or_shared_writable_maps'])
 def test_ledger7_projection(self):
  projection=P/'evidence/ledger7-observed.json';v=json.loads(projection.read_bytes());self.assertEqual(v['latest_ref'],S.BASE);self.assertEqual(len(S.rows(v['ledger'])),6);self.assertEqual(sum(x['budget_bytes']for x in v['ledger']['reservations']),102*S.GIB)
 def test_actual_chain_transition_unknown_and_edited_reject(self):
  import types
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);original=(S.ROOT,S.BASE,S.old);S.ROOT=root
   def put(n,v):
    p=root/('STORAGE_LEDGER061.%d.json'%n);p.write_text(json.dumps(v));return S.ref(p)
   row=dict(leaf=str(root/'old'),stage='cpu',budget_bytes=S.GIB);v=dict(root=str(root),authority_ref={'actual':'authority'},reservations=[row]);S.BASE=put(7,v)
   O=types.SimpleNamespace(generations=lambda r:sorted(r.glob('STORAGE_LEDGER061.*.json')),exact_ref=lambda r:Path(r['path'])if S.ref(r['path'])==r else None);S.old=lambda:O
   try:
    e={'actual':'newE'};t={'actual':'newT'};v8=dict(v,previous_ledger_ref=S.BASE,sealed_evidence_ref=e,storage069_template_ref=t);r8=put(8,v8);S.chain({},t,e)
    v9=dict(v8,previous_ledger_ref=r8,reservations=[row,dict(leaf=str(root/'new'),stage='numeric',budget_bytes=33*S.GIB)]);put(9,v9);S.chain({},t,e)
    for key,bad in(('sealed_evidence_ref',{'unknown':True}),('previous_ledger_ref',{'unknown':True}),('reservations',[dict(row,budget_bytes=0)])):
     broken=dict(v9);broken[key]=bad;put(9,broken)
     with self.assertRaises(ValueError):S.chain({},t,e)
    put(9,v9)
   finally:S.ROOT,S.BASE,S.old=original
 def test_actual_not_found_observations(self):
  p=P/'evidence/operation-notfound-observed.json';S.unavailable(S.ref(p))
  with tempfile.TemporaryDirectory()as d:
   q=Path(d)/'bad';v=json.loads(p.read_bytes());v[1]['snapshot']['found']=True;q.write_text(json.dumps(v))
   with self.assertRaises(ValueError):S.unavailable(S.ref(q))
 def test_actual_terminal_predicate_negative_fixtures(self):
  # Executes the actual verifier, using exact recorded owner/create structures.
  import copy,types
  owners=json.loads((P/'evidence/owners-observed.json').read_bytes());created=json.loads((P/'evidence/cids-observed.json').read_bytes());oldread,oldold,oldscan=S.read,S.old,S.no_writers
  for i in range(3):
   values={};o=owners[i];phase=dict(leaf=o['leaf'],owner_ref=o['owner_ref'],cleanup_refs=[],create_refs=[],container_state_refs=[{'path':'inspect'}],operation_terminal_ref=None,tree_ref={'path':'tree1'},quiescent_ref={'path':'q'})
   values[o['owner_ref']['path']]=o['owner'];states=[]
   for j,c in enumerate(created[i]['actual_created_containers']):
    cr=c['create_ref'];phase['create_refs'].append(cr);values[cr['path']]={'stdout':c['cid']};stage='native'if j==0 else'numeric';r={'path':(S.ROOT/S.NAMES[i]/stage/'cleanup-verdict.json').as_posix()};phase['cleanup_refs'].append(r);values[r['path']]=dict(resource_release_verified=True,stopped=True,retained=True,errors=[],unresolved_active_cid=None);states.append(dict(Id=c['cid'],State=c['state'],ExecIDs=c['ExecIDs']))
   values['inspect']=states;values['tree1']=values['tree2']={'root':phase['leaf'],'files':[]};values['missing']=json.loads((P/'evidence/operation-notfound-observed.json').read_bytes());values['q']=dict(schema='deltalog.actual-quiescent-closure/v093',source=S.SOURCE,leaf=phase['leaf'],owner_ref=phase['owner_ref'],historical_operation_receipt_unavailable=True,historical_operation_exit_claimed=False,no_original_commands=True,no_open_write_fds_or_shared_writable_maps=True,two_full_hashes_equal=True,first_tree_ref=phase['tree_ref'],second_tree_ref={'path':'tree2'},operation_unavailable_ref={'path':'missing'},unavailable_operation_id=S.OPERATIONS[i])
   try:
    S.read=lambda r:values[r['path']];S.old=lambda:types.SimpleNamespace();S.no_writers=lambda:True;S.verify_terminal(phase,i)
    for key,bad in(('Running',True),('Pid',123),('OOMKilled',True),('ExitCode',99)):
     original=copy.deepcopy(values['inspect']);values['inspect'][0]['State'][key]=bad
     with self.assertRaises(ValueError):S.verify_terminal(phase,i)
     values['inspect']=original
    original=copy.deepcopy(values['inspect']);values['inspect'][0]['Id']='f'*64
    with self.assertRaises(ValueError):S.verify_terminal(phase,i)
    values['inspect']=original;values['q']['historical_operation_exit_claimed']=True
    with self.assertRaises(ValueError):S.verify_terminal(phase,i)
   finally:S.read,S.old,S.no_writers=oldread,oldold,oldscan
if __name__=='__main__':unittest.main()

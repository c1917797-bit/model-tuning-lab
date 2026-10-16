import ast,copy,json,pathlib,sys,tempfile,unittest
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P));import sealed_storage069 as S
class ClosedStorage(unittest.TestCase):
 def test_actual_shaped_terminal_and_all_created_cids(self):
  from unittest import mock
  with tempfile.TemporaryDirectory()as d:
   leaf=pathlib.Path(d)/S.EXPECTED[1];leaf.mkdir();ids=['a'*64,'b'*64]
   for directory,cid in zip(('numeric','native'),ids):
    p=leaf/directory;p.mkdir();(p/'create-receipt.json').write_text(json.dumps(dict(stdout=cid+'\n')))
   owner_ref=dict(path=str(leaf/'RESULT.json'),bytes=1620,sha256='7261c6673bf6a8771119bfd2b3260a02a8480f0da10d568a40602cc104132f26')
   phase=dict(leaf=str(leaf),owner_ref=owner_ref,cleanup_refs=['cleanup'],container_state_refs=['inspect'],operation_terminal_ref='terminal')
   values=dict(cleanup=dict(resource_release_verified=True,stopped=True,retained=True,errors=[],unresolved_active_cid=None),inspect=[dict(Id=cid,ExecIDs=None,State=dict(Running=False,Pid=0,ExitCode=0,OOMKilled=False,Status='exited'))for cid in ids],terminal=dict(schema='ascend.actual-operation-terminal-observation/v1',operation_snapshot=dict(found=True,terminal=True,ok=True,status='completed',kind='exec',operation=dict(routeDecision='peer_direct',targetPeerId=S.TARGET,result=dict(record=dict(state='completed',exitCode=3,timedOut=False,cancelled=False,command='/usr/bin/python3',args=['-I','-B',S.OLDROOT+'/run052.py','--phase','numeric16'],stdout='MAIN_DLLIFECYCLE002_OWNER '+json.dumps(owner_ref)+'\n'))))))
   values['terminal']['operation_snapshot'].update(ok=False,succeeded=False,error='exit code');values['terminal']['operation_snapshot']['operation']['ok']=True
   def read(r):return dict(stopped_retained=True,secondary=[],primary='preserved old061 diagnostic failure')if r==owner_ref else values[r]
   with mock.patch.object(S,'no_old_commands',return_value={'software_fixture_only':True})as absent:
    self.assertTrue(S.verify_terminal(phase,read));self.assertEqual(absent.call_count,1)
    for edit in('running','missing','badpeer','badowner','wrongexit','transportfailure','timeout','cancelled','notterminal','false_success'):
     bad=copy.deepcopy(values)
     if edit=='running':bad['inspect'][0]['State']['Running']=True
     elif edit=='missing':bad['inspect'].pop()
     elif edit=='badpeer':bad['terminal']['operation_snapshot']['operation']['targetPeerId']='other'
     elif edit=='badowner':bad['terminal']['operation_snapshot']['operation']['result']['record']['stdout']='MAIN_DLLIFECYCLE002_OWNER {}\n'
     elif edit=='wrongexit':bad['terminal']['operation_snapshot']['operation']['result']['record']['exitCode']=0
     elif edit=='transportfailure':bad['terminal']['operation_snapshot']['operation']['ok']=False
     elif edit=='timeout':bad['terminal']['operation_snapshot']['operation']['result']['record']['timedOut']=True
     elif edit=='cancelled':bad['terminal']['operation_snapshot']['operation']['result']['record']['cancelled']=True
     elif edit=='notterminal':bad['terminal']['operation_snapshot']['terminal']=False
     else:bad['terminal']['operation_snapshot']['ok']=True
     with self.assertRaises(ValueError):S.verify_terminal(phase,lambda r:dict(stopped_retained=True,secondary=[],primary='old failed')if r==owner_ref else bad[r])
 def test_exact_inverse_and_math_bytes(self):
  import inverse069 as I
  base=P.parent/'deltalog-split-scale-numeric-new24h-20261016-061'
  for n in json.loads((P/'EDITS069.json').read_bytes()):self.assertEqual(I.undo(n,(P/n).read_bytes().decode()),(base/n).read_bytes().decode(),n)
  for n in('producer.py','oracle.py','precast.py','domain_consumer.py','preregister.py','sidecar_capture.py'):self.assertEqual((P/n).read_bytes(),(base/n).read_bytes(),n)
 def test_two_real_mapping_refs_are_files(self):
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());self.assertEqual(len(m['diagnostic_runtime_sources']),2)
  self.assertTrue(all(r in m['files'].values()for r in m['diagnostic_runtime_sources'].values()))
 def test_tree_stat_and_hash_change_reject(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d);(p/'raw').write_bytes(b'abc');rows=S.tree(p,True);before=S.tree(p,False);self.assertEqual(rows[0]['bytes'],3);self.assertEqual(before,[{k:v for k,v in rows[0].items()if k!='sha256'}]);(p/'raw').write_bytes(b'abd');self.assertNotEqual(S.tree(p,True),rows)
 def test_no_boolean_terminal_promotion(self):
  with self.assertRaises((KeyError,ValueError)):S.verify_terminal(dict(owner_ref=1,cleanup_refs=[2],leaf='bad'),lambda r:dict(stopped_retained=True,secondary=[],resource_release_verified=True,stopped=True,retained=True,errors=[],unresolved_active_cid=None))
if __name__=='__main__':unittest.main()

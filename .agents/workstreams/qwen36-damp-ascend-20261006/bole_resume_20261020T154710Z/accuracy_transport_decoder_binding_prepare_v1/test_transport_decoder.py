"""Synthetic software boundary tests. No real authority, HTTP, models or HE execution."""
import ast,copy,importlib.util,json,sys,tempfile,types,unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import transport_decoder_bridge as B
import render_transport_decoder as D
import transport_decoder_entry as E
OLD=P.parent/'accuracy_decoder_lineage_prepare_v1'
with B.isolated(('decoder_replay_contract','render_decoder')):
 sys.path.insert(0,str(OLD))
 R=B.load_module(B.ref(OLD/'decoder_replay_contract.py'),'decoder_replay_contract')
 RF=B.load_module(B.ref(OLD/'test_replay_lineage.py'),'_bridge_policy_fixture')
TRANSPORT=D.TRANSPORT
@contextmanager
def authority_fixture(fault=None):
 f=RF.fixture();policy=RF.Controls()
 if fault=='expired':f[2]['cutoff_epoch']=199
 if fault=='wrong-source':f[2]['binding_ref']={'foreign':True}
 policy.generation(f)
 def validate(m,binding_ref,seconds=0):return policy.ticket(f)
 cohort_saved=sys.modules.get('cohort_contract')
 B.load_module(B.ref(TRANSPORT/'cohort_contract.py'),'cohort_contract')
 C=B.load_module(B.ref(TRANSPORT/'http_common.py'),'_fixture_original_HTTP_common')
 original_obj=C.obj
 authority=dict(start_epoch=1,cutoff_epoch=30)
 C.obj=lambda ref:authority if ref==f[9]['authority_ref']else original_obj(ref)
 active=dict(R=types.SimpleNamespace(validate_current=validate),m={},binding_ref=f[1],
  generation=f[9],HTTP_m={'authority_ref':{'foreign':True}if fault=='wrong-generation'else f[9]['authority_ref']},C=C)
 old=B._ACTIVE;B._ACTIVE=active
 try:yield f,active
 finally:
  B._ACTIVE=old;sys.modules.pop('_fixture_original_HTTP_common',None)
  if cohort_saved is None:sys.modules.pop('cohort_contract',None)
  else:sys.modules['cohort_contract']=cohort_saved
class Controls(unittest.TestCase):
 def test_whole_source_inverse_preserves_every_lifecycle_function(self):
  b=D.render(P/'future-unbound')
  self.assertEqual(D.inverse(b),b['original'])
  old=ast.parse(b['original']);new=ast.parse(b['files']['consume_lifecycle_replay.py'])
  for name in('stop_replay','validate_one','owner_join','journal','events','unique_request','main'):
   a=next(n for n in old.body if isinstance(n,ast.FunctionDef)and n.name==name)
   c=next(n for n in new.body if isinstance(n,ast.FunctionDef)and n.name==name)
   self.assertEqual(ast.dump(a,include_attributes=False),ast.dump(c,include_attributes=False))
  bad=copy.deepcopy(b);bad['files']['consume_lifecycle_replay.py']+=b'\n# unaudited'
  with self.assertRaises(ValueError):D.inverse(bad)
 def test_defaultOFF_actual_public_main_and_proxy(self):
  with patch.object(sys,'argv',[str(P/'transport_decoder_entry.py')]):self.assertEqual(E.main(),0)
  with self.assertRaises(ValueError):B.COMMON_PROXY.source({'missing':True})
  with patch.object(sys,'argv',[str(P/'transport_decoder_entry.py'),'--execute']):
   with self.assertRaises(ValueError):E.main()
 def test_historical_recorded_time_and_current_CPU_both_required(self):
  with authority_fixture()as(f,c):
   # Current200 has a live CPU ticket; generation10..20 used its own1..30 ticket.
   self.assertEqual(B.historical_authority(f[9]['authority_ref']),dict(start_epoch=1,cutoff_epoch=30))
   with self.assertRaises(ValueError):c['C'].authority(f[9]['authority_ref']) # unchanged current-time verifier still refuses expired ticket
   with self.assertRaises(ValueError):B.historical_authority({'foreign':True})
   with self.assertRaises(ValueError):B.historical_authority(f[9]['authority_ref'],300)
 def test_current_expired_wrong_source_and_generation_rejected(self):
  for fault in('expired','wrong-source','wrong-generation'):
   with self.subTest(fault=fault),authority_fixture(fault)as(f,c):
    with self.assertRaises(ValueError):B.historical_authority(f[9]['authority_ref'])
  with authority_fixture()as(f,c):
   c['generation']['finished_epoch']=31
   with self.assertRaises(ValueError):B.historical_authority(f[9]['authority_ref'])
 def test_module_names_and_functions_restore_on_success_and_error(self):
  sentinel=types.ModuleType('sentinel');saved=sys.modules.get('_bridge_restore')
  sys.modules['_bridge_restore']=sentinel
  for bad in(False,True):
   try:
    with B.isolated(('_bridge_restore',)):
     B.load_module(B.ref(P/'transport_decoder_bridge.py'),'_bridge_restore')
     sys.modules['_HTTPv3_pure_HE_guard_synthetic']=types.ModuleType('ephemeral')
     if bad:raise ValueError('controlled downstream failure')
   except ValueError:pass
   self.assertIs(sys.modules['_bridge_restore'],sentinel)
   self.assertNotIn('_HTTPv3_pure_HE_guard_synthetic',sys.modules)
  if saved is None:sys.modules.pop('_bridge_restore',None)
  else:sys.modules['_bridge_restore']=saved
 def test_real_score_seam_preserves_whole_envelope_and_blocks_HE(self):
  with authority_fixture()as(f,c),tempfile.TemporaryDirectory(dir=P)as d:
   output=Path(d);calls=[]
   client=f[12];raw=f[8];current_source={'synthetic':'current-source'}
   def objects(ref):
    if ref==f[9]['client_ref']:return client
    raise ValueError('foreign source fixture')
   def replay(source,raw_ref,full_provenance):
    calls.append((source,raw_ref,full_provenance))
    obj=json.loads(Path(raw_ref['path']).read_text())
    self.assertEqual(R.inverse_envelope(obj,f[0]['historical_task_source_ref']),raw)
    return dict(human_eval_code_executed=False,fixture_only=True)
   c.update(binding=f[0],plan=f[7],raw=raw,decoder_source_ref=current_source,output=output,
    modules={'score_tokens':types.SimpleNamespace(replay=replay)})
   c['R']=types.SimpleNamespace(validate_current=c['R'].validate_current,obj=objects,envelope=R.envelope,inverse_envelope=R.inverse_envelope,ref=B.ref)
   self.assertTrue(B.decode_grades(f[7],client)['fixture_only']);self.assertEqual(len(calls),1)
   self.assertEqual(calls[0][0],current_source);self.assertIs(calls[0][2],False)
   with self.assertRaises(ValueError):B.decode_grades(dict(f[7],arm='OFF'),client)
 def test_historical_verifier_retains_original_budget_predicate(self):
  with authority_fixture()as(f,c):
   fn=B.historical_verifier(c['C'],20)
   self.assertEqual(fn(f[9]['authority_ref'],0),dict(start_epoch=1,cutoff_epoch=30))
   with self.assertRaises(ValueError):fn(f[9]['authority_ref'],11)
 def test_actual_rendered_packet_inverse_and_rehashed_bad_consumer(self):
  rr=lambda n:dict(path='/SYNTHETIC/'+n,bytes=1,sha256='0'*64)
  ds,hs,br,sr,gr=[rr(n)for n in('decoder','HTTP','binding','bridge','generation')]
  bundle=D.render(P,decoder_source_ref=ds,HTTP_source_ref=hs);q=bundle['manifest']
  b=dict(transport_decoder_binding_ref=sr,generation_ref=gr,required_readonly_mounts=[str(P)])
  m=dict(files={'decoder_replay_contract.py':B.ref(OLD/'decoder_replay_contract.py'),'replay_entry.py':B.ref(OLD/'replay_entry.py')})
  historical=dict(files={'consume_lifecycle.py':q['original_consumer_ref']})
  values={r['path']:v for r,v in((sr,q),(ds,m),(br,b),(gr,{'HTTP_source_ref':hs}),(hs,historical))}
  raw=bundle['files']['consume_lifecycle_replay.py'];original_checked=B.checked
  class Virtual:
   def __init__(self,raw):self.raw=raw
   def __eq__(self,p):return p==P/'consume_lifecycle_replay.py'
   def read_text(self):return self.raw.decode()
  def check(r):
   if r['path']==str(P/'consume_lifecycle_replay.py'):
    self.assertEqual(D.ref(P/'consume_lifecycle_replay.py',raw),r)
    return Virtual(raw)
   return original_checked(r)
  with patch.object(B,'obj',lambda r:values[r['path']]),patch.object(B,'checked',check):
   self.assertEqual(B.packet(sr,ds,br),(q,m,b))
   # Rehash the changed consumer/manifest operand, so this is not an old-Ref test.
   raw+=b'\n# omitted gate would be rejected';q['files']['consume_lifecycle_replay.py']=D.ref(P/'consume_lifecycle_replay.py',raw)
   with self.assertRaisesRegex(ValueError,'complete unchanged'):B.packet(sr,ds,br)
 def test_actual_public_entry_current_policy_then_bounded_stop_restores_modules(self):
  f=RF.fixture();policy=RF.Controls()
  # Explicit software IO fixture only: actual packet/inverse tested separately.
  # No MAIN source/owner qualification is claimed by this bounded entry control.
  q={'files':{'transport_decoder_entry.py':B.ref(E.__file__)}}
  m={'files':{'decoder_replay_contract.py':B.ref(OLD/'decoder_replay_contract.py'),'replay_entry.py':B.ref(OLD/'replay_entry.py')}}
  original_load=B.load_module;events=[]
  class BeforeDecoder(Exception):pass
  @contextmanager
  def stop(_):
   events.append('bounded-before-original-decoder-closure');raise BeforeDecoder('software boundary; no tokenizer/model');yield
  def load(r,name):
   module=original_load(r,name)
   if name=='decoder_replay_contract':
    module.validate_current=lambda *a,**k:policy.ticket(f)
   if name=='_current_decoder_entry':module.source_modules=stop
   return module
  names=('decoder_replay_contract','_current_decoder_entry','transport_decoder_bridge','_transport_lifecycle_replay')
  prior={n:sys.modules.get(n)for n in names}
  with tempfile.TemporaryDirectory(dir=P)as d,patch.object(B,'packet',lambda *a:(q,m,{})),patch.object(B,'load_module',load):
   out=Path(d)/'bounded'
   with self.assertRaises(BeforeDecoder):E.execute({'fixture':'source'},{'fixture':'decoder'},f[1],out)
   self.assertTrue((out/'FIRST-FAULT.json').is_file());self.assertFalse((out/'RESULT.json').exists())
   f[2]['cutoff_epoch']=199
   with self.assertRaises(ValueError):E.execute({'fixture':'source'},{'fixture':'decoder'},f[1],Path(d)/'expired')
   self.assertFalse((Path(d)/'expired').exists())
  self.assertEqual(events,['bounded-before-original-decoder-closure'])
  for n,v in prior.items():self.assertIs(sys.modules.get(n),v)

if __name__=='__main__':unittest.main()

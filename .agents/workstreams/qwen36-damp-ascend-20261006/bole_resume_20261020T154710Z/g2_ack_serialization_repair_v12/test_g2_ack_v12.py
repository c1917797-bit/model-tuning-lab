import ast,copy,json,pickle,sys,tempfile,threading,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import g2_channel as CH,g2_contract as G2,g2_ack_proof as Q
class AckWire(unittest.TestCase):
 def setUp(self):
  self.fixture,self.records=Q.fixture(P/'ACTUAL_ACK_FIXTURE.json');self.ack,self.frame,self.report=Q.actual_step(self.fixture,self.records)
 def validate(self,a):
  rr=self.fixture['records']['STREAM/REPORT-RANK-0-000001.json']['actual_ref']
  def actual_report(r):self.assertEqual(r,rr);return copy.deepcopy(self.report)
  with patch.object(CH,'load',side_effect=actual_report):return CH.validate_ack(a,self.frame,consumer_source=self.ack['consumer_source'],channel_ref=self.ack['channel_ref'],previous_ack=self.ack['previous_ack'])
 def test_actual_first_STEP_3307_canonical3197_wire2846_lossless(self):
  self.assertEqual(len((json.dumps(self.ack,sort_keys=True)+'\n').encode()),3307)
  self.assertEqual(len((json.dumps(self.ack,sort_keys=True,separators=(',',':'))+'\n').encode()),3197)
  b=CH.ack_bytes(self.ack);self.assertEqual(len(b),2846);self.assertEqual(CH.decode_ack(b),self.ack);self.assertTrue(self.validate(CH.decode_ack(b)))
 def test_all_four_actual_open_ACKs_keep_complete_semantics(self):
  for rank in range(4):
   name='STREAM/ACK-RANK-%d-000000.json'%rank;a=json.loads(self.records[name]);self.assertEqual(len(self.records[name]),2726)
   b=CH.ack_bytes(a);self.assertLessEqual(len(b),3072);self.assertEqual(CH.decode_ack(b),a);self.assertIsNone(a['previous_ack'])
 def test_actual_step_all20_fields_full_identity_and_six_Ref3_values_retained(self):
  a=CH.decode_ack(CH.ack_bytes(self.ack));self.assertEqual(set(a),set(CH.ACK_FIELDS));self.assertEqual(len(a),20)
  self.assertEqual(a['consumer_identity']['cgroup'],self.ack['consumer_identity']['cgroup']);self.assertEqual(len(a['consumer_identity']['cgroup']),1021)
  for k in CH.ACK_REF_FIELDS:self.assertEqual(a[k],self.ack[k])
 def test_actual_write_and_load_bytes_equal_the_same_budgeted_encoder(self):
  with tempfile.TemporaryDirectory()as d:
   r=CH.write(Path(d)/'ACK-RANK-0-000001.json',self.ack);self.assertEqual(r['bytes'],2846);self.assertEqual(CH.checked(r).read_bytes(),CH.ack_bytes(self.ack));self.assertEqual(CH.load(r),self.ack)
 def test_other_events_keep_original_exact_spaced_encoding(self):
  with tempfile.TemporaryDirectory()as d:
   r=CH.write(Path(d)/'REPORT.json',self.report);self.assertEqual(CH.checked(r).read_bytes(),(json.dumps(self.report,sort_keys=True,allow_nan=False)+'\n').encode());self.assertEqual(CH.load(r),self.report)
 def test_missing_extra_top_fields_and_invalid_semantic_schema_reject(self):
  for mutate in('missing','extra','schema'):
   a=copy.deepcopy(self.ack)
   if mutate=='missing':a.pop('gates')
   elif mutate=='extra':a['unknown_math_omission']=True
   else:a['schema']='bole.actual-independent-frame-ACK/v999'
   with self.assertRaises(ValueError):CH.ack_bytes(a)
 def test_every_typed_scalar_rejects_bool_as_int_or_wrong_boolean(self):
  for key,value in(('rank',True),('sequence',False),('sequence',1.),('sequence',-1),('sequence',11),('logical_tensor_bytes',True),('passed',1),('complete_frame_consumed',0),('formal_success',0),('nonce','bad'),('oracle_report_sha256','g'*64)):
   a=copy.deepcopy(self.ack);a[key]=value
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):CH.ack_bytes(a)
 def test_complete_Ref3_triples_reject_missing_extra_hash_or_bool_bytes(self):
  for key in CH.ACK_REF_FIELDS:
   for mutation in('missing','extra','bool','hash'):
    a=copy.deepcopy(self.ack)
    if mutation=='missing':a[key].pop('bytes')
    elif mutation=='extra':a[key]['unknown']=1
    elif mutation=='bool':a[key]['bytes']=True
    else:a[key]['sha256']='x'*64
    with self.subTest(key=key,mutation=mutation),self.assertRaises(ValueError):CH.ack_bytes(a)
 def test_coverage_and_identity_scalars_refuse_bool_or_missing_fields(self):
  for section,key,value in(('coverage','generation',True),('coverage','ordinal',True),('coverage','processed_nodes',[0,True]),('coverage','emitted_tokens',[True]),('consumer_identity','pid',True),('consumer_identity','start_ticks',False),('consumer_identity','cgroup',None),('gates','layers',True),('gates','original_FA_bounds',1)):
   a=copy.deepcopy(self.ack);a[section][key]=value
   with self.subTest(section=section,key=key),self.assertRaises(ValueError):CH.ack_bytes(a)
  for section in('coverage','consumer_identity','gates'):
   a=copy.deepcopy(self.ack);a[section].pop(next(iter(a[section])))
   with self.assertRaises(ValueError):CH.ack_bytes(a)
 def test_duplicate_wire_keys_and_nested_duplicate_keys_refuse(self):
  b=CH.ack_bytes(self.ack)
  for raw in(b.replace(b'"schema":',b'"schema":"duplicate","schema":',1),b.replace(b'"generation":1',b'"generation":1,"generation":1',1)):
   with self.assertRaises(ValueError):CH.decode_ack(raw)
 def test_noncanonical_whitespace_array_length_and_illegal_wire_types_reject(self):
  b=CH.ack_bytes(self.ack);w=json.loads(b)
  for raw in(b+b'\n',json.dumps(w).encode(),b.replace(b'"values":[',b'"values":{',1)):
   with self.assertRaises(ValueError):CH.decode_ack(raw)
  for value in(w['values'][:-1],w['values']+[False],{},True):
   with self.assertRaises(ValueError):CH.decode_ack((json.dumps(dict(w,values=value),sort_keys=True,separators=(',',':'))+'\n').encode())
 def test_original3072_exact_boundary_and3073_rejection_not_truncation(self):
  a=copy.deepcopy(self.ack);a['consumer_identity']['cgroup']+='X'*226;b=CH.ack_bytes(a);self.assertEqual(len(b),3072);self.assertEqual(CH.decode_ack(b),a)
  a['consumer_identity']['cgroup']+='X'
  with self.assertRaisesRegex(ValueError,'3072'):CH.ack_bytes(a)
  with self.assertRaisesRegex(ValueError,'3072'):CH.decode_ack(b+b'X')
 def test_legacy_oversize_semantic_ACK_cannot_bypass_new_wire_dispatch(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'ACK-RANK-0-000001.json';p.write_text(json.dumps(self.ack,sort_keys=True)+'\n')
   with self.assertRaisesRegex(ValueError,'legacy size-cap bypass'):CH.load(CH.ref(p))
 def test_original_validator_still_rejects_wrong_source_hash_coverage_previous_and_gates(self):
  for key in('source','oracle_report_sha256','coverage','previous_ack','gates','passed'):
   a=copy.deepcopy(self.ack)
   if key in('source','previous_ack'):a[key]['sha256']='0'*64
   elif key=='oracle_report_sha256':a[key]='0'*64
   elif key=='coverage':a[key]['emitted_tokens'][0]=1
   elif key=='gates':a[key]['original_FA_bounds']=False
   else:a[key]=False;a['complete_frame_consumed']=False;a['gates']=dict(kind='step')
   decoded=CH.decode_ack(CH.ack_bytes(a))
   with self.subTest(key=key),self.assertRaises(ValueError):self.validate(decoded)
 def test_whole_two_actor_operands_and_all_original_sender_validator_functions_inverse(self):
  for n in Q.ORIGINALS:Q.check_pair(n,(P/n).read_bytes(),(P/('ORIGINAL_V11_'+n+'.txt')).read_bytes())
  names=Q.preserved_functions((P/'g2_channel.py').read_bytes(),(P/'ORIGINAL_V11_g2_channel.py.txt').read_bytes());self.assertIn('validate_ack',names);self.assertIn('Sender',names)
  with self.assertRaises(ValueError):Q.check_pair('g2_consumer.py',(P/'g2_consumer.py').read_bytes()+b'\n# undeclared change\n',(P/'ORIGINAL_V11_g2_consumer.py.txt').read_bytes())
 def test_finalizer_has_only_exact_ACK_operand_decode_delta(self):
  self.assertEqual(Q.inverse('g2_finalize.py',(P/'g2_finalize.py').read_bytes()),(P/'ORIGINAL_V11_g2_finalize.py.txt').read_bytes())
  self.assertNotIn("ack=C.obj(event['ack'])",(P/'g2_finalize.py').read_text());self.assertIn("ack=CH.load(event['ack'])",(P/'g2_finalize.py').read_text())
 def _sender(self,bad=False):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);base=root/'receipts';base.mkdir();stream=base/'STREAM';stream.mkdir();source=root/'SOURCE.json';source.write_text(json.dumps(dict(model_receipt_root=str(base))))
   sr=CH.ref(source);channel=root/'CHANNEL.json';channel.write_text('{}');cr=CH.ref(channel)
   s=object.__new__(CH.Sender);s.C=NS(obj=CH.load);s.source=sr;s.channel_ref=cr;s.value=dict(nonce=self.ack['nonce'],consumer_source=CH.ref(P/'g2_consumer.py'));s.rank=0;s.root=stream;s.sequence=0;s.previous_ack=None;s.events=[];s.active=None
   cov=dict(generation=1,request='pure-protocol-control');errors=[]
   def consumer():
    try:
     manifest=stream/'FRAME-RANK-0-000000.json';end=time.monotonic()+2
     while not manifest.exists():
      if time.monotonic()>end:raise ValueError('test bounded complete frame')
      time.sleep(.005)
     m=CH.load(CH.ref(manifest));rr=CH.write(stream/'REPORT-RANK-0-000000.json',dict(source=sr,raw=m['raw'],coverage=cov,passed=True,pure_protocol_control=True,numerical_model_qualification=False))
     a=dict(self.ack,source=sr,consumer_source=s.value['consumer_source'],channel_ref=cr,rank=0,sequence=0,kind='open',raw=m['raw'],logical_tensor_bytes=0,previous_ack=None,coverage=cov,oracle_report=rr,oracle_report_sha256='0'*64 if bad else rr['sha256'],gates=dict(kind='open'))
     CH.write(stream/'ACK-RANK-0-000000.json',a)
    except BaseException as e:errors.append(e)
   t=threading.Thread(target=consumer,daemon=True);t.start()
   with patch.object(G2,'ACK_TIMEOUT_SECONDS',2):
    if bad:
     with self.assertRaises(ValueError):s.send(NS(save=lambda obj,f:f.write(pickle.dumps(obj))),dict(logical_tensor_bytes=0,payload={}),kind='open',coverage=cov)
     self.assertEqual(s.sequence,0);self.assertEqual(s.events,[]);self.assertTrue(s.active.is_file());self.assertFalse(list(stream.glob('RELEASE-*')))
    else:
     e=s.send(NS(save=lambda obj,f:f.write(pickle.dumps(obj))),dict(logical_tensor_bytes=0,payload={}),kind='open',coverage=cov)
     self.assertEqual(s.sequence,1);self.assertIsNone(s.active);self.assertFalse((stream/'FRAME-RANK-0-000000.pt').exists());self.assertEqual(CH.load(e['ack'])['oracle_report_sha256'],CH.load(e['ack'])['oracle_report']['sha256']);self.assertTrue(CH.load(e['release'])['released_after_successful_ACK'])
   t.join(3);self.assertFalse(t.is_alive());self.assertEqual(errors,[])
 def test_real_original_sender_durable_wire_report_then_release_once(self):self._sender(False)
 def test_real_original_sender_wrong_report_hash_keeps_raw_without_advancement(self):self._sender(True)
 def test_original_caps_and_same_300_lane_functions_remain_exact(self):
  self.assertEqual(G2.EVENT_METADATA_CAP,2048+3072+G2.RELEASE_CAP+G2.REPORT_CAP);self.assertEqual(G2.RAW_CAP,2**30);self.assertEqual(G2.METADATA_CAP,64*2**20)
  import g2_software_stages as S
  self.assertEqual(S.CAPS,dict(parent279=120.,controls=60.,metadata=120.));self.assertEqual(S.LANE_CAP,300.);self.assertEqual(S.PHASE,3600.);self.assertEqual(S.CLEANUP,180.)
if __name__=='__main__':unittest.main()

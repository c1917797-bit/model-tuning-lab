"""Controlled in-memory SSE fixtures. No HTTP/model/formal qualification."""
import copy,email.message,hashlib,io,json,pathlib,subprocess,tempfile,unittest
import fixed1024_client as C
import independent_reader as R
from evidence import ref,obj,exclusive_json
P=pathlib.Path(__file__).resolve().parent
IDS=list(range(131));RID='cmpl-controlled-fixture'
def event(v,crlf=False):
 b=b'data: '+(v if type(v)is bytes else json.dumps(v,ensure_ascii=False).encode())+b'\n\n';return b.replace(b'\n',b'\r\n')if crlf else b

def chunks_wire(*,token_batch=2,role=True,crlf=False,finish='length',usage=True,done=True,count=1024):
 rows=[];base=dict(id=RID,object='text_completion',created=1,model=C.MODEL)
 if role:rows.append(event(dict(base,choices=[dict(index=0,text='',delta=dict(role='assistant'),token_ids=[])]),crlf))
 for start in range(0,count,token_batch):
  ids=list(range(start,min(count,start+token_batch)));choice=dict(index=0,text='树',token_ids=ids,finish_reason=finish if start+len(ids)==count else None)
  if start==0:choice['prompt_token_ids']=IDS
  rows.append(event(dict(base,choices=[choice]),crlf))
 if usage:rows.append(event(dict(base,choices=[],usage=dict(prompt_tokens=131,completion_tokens=count,total_tokens=131+count)),crlf))
 if done:rows.append(event(b'[DONE]',crlf))
 return rows
class Clock:
 def __init__(self):self.t=100
 def __call__(self):self.t+=10;return self.t
class Response:
 status=200
 def __init__(self,parts):self.parts=list(parts);self.headers=email.message.Message();self.headers['Content-Type']='text/event-stream; charset=utf-8'
 def read1(self,n):
  if not self.parts:return b''
  data=self.parts.pop(0)
  if len(data)>n:self.parts.insert(0,data[n:]);data=data[:n]
  return data
class SSETests(unittest.TestCase):
 def capture(self,parts):
  t=tempfile.TemporaryDirectory(dir=P);self.addCleanup(t.cleanup);root=pathlib.Path(t.name);r=C.observe_response(Response(parts),root,request_start_ns=100,request_id=RID,input_ids=IDS,clock=Clock());return root,r,R.read_observation(r)
 def test_delta_tokens_preserve1024_order_and_independent_metrics(self):
  root,r,v=self.capture(chunks_wire());self.assertEqual(v['ordered_token_ids'],list(range(1024)));self.assertEqual(v['TPOT_denominator'],1023);self.assertEqual(v['T_total_ns'],v['TTFT_ns']+v['TPOT_numerator_ns']);self.assertFalse(v['formal_qualification'])
 def test_role_usage_done_and_prompt_ids_never_count_as_generated(self):
  root,r,v=self.capture(chunks_wire());trace=obj(r);self.assertEqual(len(trace['ordered_token_ids']),1024);self.assertEqual(sum(e['kind']=='non-token'for e in trace['events']),2);self.assertEqual(trace['events'][0]['token_ids'],[]);self.assertLess(v['request_start_monotonic_ns']+v['T_total_ns'],v['eof_monotonic_ns'])
 def test_multi_token_same_event_same_real_time_no_interpolation(self):
  root,r,v=self.capture(chunks_wire(token_batch=1024));self.assertEqual(len(set(v['token_receive_monotonic_ns'])),1);self.assertEqual(v['TPOT_numerator_ns'],0);self.assertGreater(v['T_total_ns'],0)
 def test_split_every_boundary_CRLF_UTF8_uses_complete_event_chunk_time(self):
  wire=b''.join(chunks_wire(token_batch=128,crlf=True));pieces=[wire[i:i+17]for i in range(0,len(wire),17)];root,r,v=self.capture(pieces);self.assertEqual(v['ordered_token_ids'],list(range(1024)));self.assertGreater(v['TPOT_numerator_ns'],0)
 def test_complete_raw_and_every_read_chunk_hash_offsets_reopened(self):
  root,r,v=self.capture(chunks_wire());trace=obj(r);rows=[json.loads(x)for x in(root/'CHUNKS.jsonl').read_text().splitlines()];raw=(root/'SSE.raw').read_bytes();self.assertEqual(sum(x['bytes']for x in rows),len(raw));self.assertTrue(rows[-1]['eof']);self.assertEqual(rows[-1]['bytes'],0)
  (root/'SSE.raw').write_bytes(raw+b'x')
  with self.assertRaises(ValueError):R.read_observation(r)
 def test_missing_done_or_truncated_frame_retains_failed_trace(self):
  for parts in (chunks_wire(done=False),[b'data: {"unfinished":']):
   with tempfile.TemporaryDirectory(dir=P)as td:
    root=pathlib.Path(td)
    with self.assertRaises(ValueError):C.observe_response(Response(parts),root,request_start_ns=100,request_id=RID,input_ids=IDS,clock=Clock())
    self.assertTrue((root/'SSE.raw').is_file());self.assertIsNotNone(obj(ref(root/'CLIENT_TRACE.json'))['primary'])
 def test_nonstream_json_and_2048_output_never_qualify(self):
  for parts in ([b'{"choices":[{"token_ids":[1]}]}'],chunks_wire(count=2048)):
   with tempfile.TemporaryDirectory(dir=P)as td:
    with self.assertRaises(ValueError):C.observe_response(Response(parts),pathlib.Path(td),request_start_ns=100,request_id=RID,input_ids=IDS,clock=Clock())
 def test_early_stop_instead_of_ignoreEOS_length_rejected_by_independent_reader(self):
  with tempfile.TemporaryDirectory(dir=P)as td:
   r=C.observe_response(Response(chunks_wire(finish='stop')),pathlib.Path(td),request_start_ns=100,request_id=RID,input_ids=IDS,clock=Clock())
   with self.assertRaises(ValueError):R.read_observation(r)
 def test_missing_usage_or_wrong_usage_count_rejected(self):
  for parts in (chunks_wire(usage=False),chunks_wire(count=1023)):
   with tempfile.TemporaryDirectory(dir=P)as td:
    r=C.observe_response(Response(parts),pathlib.Path(td),request_start_ns=100,request_id=RID,input_ids=IDS,clock=Clock())
    with self.assertRaises(ValueError):R.read_observation(r)
 def test_duplicate_done_or_duplicate_json_key_retains_failure(self):
  for parts in (chunks_wire()+[event(b'[DONE]')],[event(b'{"id":"a","id":"b","choices":[]}')]):
   with tempfile.TemporaryDirectory(dir=P)as td:
    with self.assertRaises(ValueError):C.observe_response(Response(parts),pathlib.Path(td),request_start_ns=100,request_id=RID,input_ids=IDS,clock=Clock())
 def test_tampered_client_metrics_cannot_replace_raw_recomputation(self):
  root,r,v=self.capture(chunks_wire());trace=obj(r);trace['T_total_ns']=1;bad=exclusive_json(root/'BAD_TRACE.json',trace)
  with self.assertRaises(ValueError):R.read_observation(bad)
 def test_reordered_token_ids_or_nonstream_options_rejected(self):
  root,r,v=self.capture(chunks_wire());trace=obj(r)
  for key in('ordered_token_ids','request'):
   bad=copy.deepcopy(trace)
   if key=='request':bad[key]['stream']=False
   else:bad[key][0],bad[key][1]=bad[key][1],bad[key][0]
   rr=exclusive_json(root/(key+'.json'),bad)
   with self.assertRaises(ValueError):R.read_observation(rr)
 def test_ledger_gap_or_backwards_clock_rejected_even_with_new_hash(self):
  root,r,v=self.capture(chunks_wire());trace=obj(r);rows=[json.loads(x)for x in(root/'CHUNKS.jsonl').read_text().splitlines()]
  for key,new in(('offset',1),('received_monotonic_ns',1),('bytes',0)):
   copied=copy.deepcopy(rows);copied[0][key]=new;f=root/(key+'.jsonl');f.write_text(''.join(json.dumps(x)+'\n'for x in copied));bad=dict(trace,chunks=ref(f));rr=exclusive_json(root/(key+'-trace.json'),bad)
   with self.assertRaises(ValueError):R.read_observation(rr)
 def test_raw_suffix_after_DONE_or_wrong_request_identity_rejected(self):
  parts=chunks_wire();parts[1]=parts[1].replace(RID.encode(),b'cmpl-foreign')
  with tempfile.TemporaryDirectory(dir=P)as td:
   r=C.observe_response(Response(parts),pathlib.Path(td),request_start_ns=100,request_id=RID,input_ids=IDS,clock=Clock())
   with self.assertRaises(ValueError):R.read_observation(r)
 def test_one_bad_HTTP_status_or_existing_output_does_not_overwrite(self):
  with tempfile.TemporaryDirectory(dir=P)as td:
   root=pathlib.Path(td);(root/'SSE.raw').write_bytes(b'keep')
   with self.assertRaises(ValueError):C.observe_response(Response([]),root,request_start_ns=100,request_id=RID,input_ids=IDS,clock=Clock())
   self.assertEqual((root/'SSE.raw').read_bytes(),b'keep')
 def test_public_execute_and_formal_compare_hard_refuse_pending_actual_refs(self):
  with self.assertRaises(ValueError):C.execute()
  with self.assertRaises(ValueError):R.qualified_three_pairs()
  self.assertTrue(all(x is None for x in R.MODEL_FOUR_REFS.values()));self.assertIsNone(R.CAPTURE_OFF_PRODUCTION_QUALIFICATION)
  for file in('fixed1024_client.py','independent_reader.py'):
   off=subprocess.run(['/usr/bin/python3','-I','-B',str(P/file)],capture_output=True);self.assertEqual(off.returncode,0)
   live=subprocess.run(['/usr/bin/python3','-I','-B',str(P/file),'--execute'],capture_output=True);self.assertNotEqual(live.returncode,0)
 def test_fabricated_nonnull_refs_or_enable_flag_cannot_open_execute(self):
  from unittest.mock import patch
  with patch.object(C,'LIVE_EXECUTION_ENABLED',True):
   with self.assertRaises(ValueError):C.execute()
  with patch.dict(R.MODEL_FOUR_REFS,{k:{}for k in R.MODEL_FOUR_REFS}),patch.object(R,'CAPTURE_OFF_PRODUCTION_QUALIFICATION',{}),patch.object(R,'FIXED1024_CORRECTNESS_QUALIFICATION',{}),patch.object(R,'PAIRED_OWNER_REF',{}),patch.object(R,'SOURCE_BOUND_OWNER_REVIEWER_REF',{}):
   with self.assertRaisesRegex(ValueError,'future owner review interface'):R.qualified_three_pairs()
class PairArithmeticControls(unittest.TestCase):
 def fixture(self):
  def rr(n):return dict(path='/synthetic/'+n,bytes=1,sha256='0'*64)
  pairs=[];start=100
  for pair in range(3):
   row=dict(pair_index=pair)
   for mode,total in(('OFF',1100),('ON',1000)):
    ident=dict(image='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1',model=C.MODEL,input_ref=rr('input'),source_ref=rr('source'),runtime_refs=dict(serving=rr('serving')),process_options_ref=rr('options'),resource_profile_ref=rr('resources'),concurrency=1,capture_off_qualification_ref=rr('captureoff'),main_clock_ref=rr('clock'),mode=mode,capture_mode='OFF',actual_input_ids=IDS,frontend_pid=500+pair,worker_processes=[dict(host_pid=1000+i,start_ticks=1,physical=4+i)for i in range(4)],work_start_ns=1,work_deadline_ns=100000)
    value=dict(request=R.expected_request(IDS),ordered_token_ids=list(range(1024)),request_id='cmpl-synthetic-%d-%s'%(pair,mode),request_start_monotonic_ns=start,eof_monotonic_ns=start+total+1,TTFT_ns=100,TPOT_numerator_ns=total-100,TPOT_denominator=1023,T_total_ns=total)
    row[mode]=dict(identity=ident,observation=value);start+=total+10
   pairs.append(row)
  return pairs
 def test_each_pair_exact_E2E_11over10_and_TTFT_TPOT_separate(self):
  value=R._after_full_qualification_math(self.fixture());self.assertEqual(len(value['pairs']),3);self.assertTrue(value['all_three_E2E_at_least_1_10']);self.assertFalse(value['extra_TTFT_threshold_imposed']);self.assertFalse(value['formal_qualification'])
 def test_E2E_target_does_not_invent_a_TPOT_or_TTFT_threshold(self):
  pairs=self.fixture()
  for pair in pairs:
   pair['OFF']['observation'].update(TTFT_ns=1000,TPOT_numerator_ns=100)
   pair['ON']['observation'].update(TTFT_ns=800,TPOT_numerator_ns=200)
  value=R._after_full_qualification_math(pairs);self.assertTrue(value['all_three_E2E_at_least_1_10']);self.assertEqual(value['pairs'][0]['TPOT_ratio'],'1/2')
 def test_fast_TPOT_cannot_replace_one_failed_E2E_pair(self):
  pairs=self.fixture();pairs[1]['OFF']['observation'].update(T_total_ns=1099,TPOT_numerator_ns=999);pairs[1]['ON']['observation'].update(TTFT_ns=990,TPOT_numerator_ns=10)
  with self.assertRaises(ValueError):R._after_full_qualification_math(pairs)
 def test_two_big_ratios_do_not_average_away_one_bad_pair(self):
  pairs=self.fixture();pairs[0]['OFF']['observation'].update(T_total_ns=2000,TPOT_numerator_ns=1900);pairs[2]['OFF']['observation'].update(T_total_ns=2000,TPOT_numerator_ns=1900);pairs[1]['OFF']['observation'].update(T_total_ns=900,TPOT_numerator_ns=800)
  with self.assertRaises(ValueError):R._after_full_qualification_math(pairs)
 def test_wrong_source_input_image_or_capture_mode_rejected(self):
  for key,value in(('source_ref',{}),('input_ref',{}),('image','sha256:'+'0'*64),('capture_mode','DIAGNOSTIC')):
   pairs=self.fixture();pairs[1]['ON']['identity'][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):R._after_full_qualification_math(pairs)
 def test_missing_pair_overlapping_request_or_missing_rank_rejected(self):
  pairs=self.fixture()
  with self.assertRaises(ValueError):R._after_full_qualification_math(pairs[:2])
  for field in('overlap','rank'):
   p=copy.deepcopy(pairs)
   if field=='overlap':p[1]['OFF']['observation']['request_start_monotonic_ns']=1
   else:p[1]['OFF']['identity']['worker_processes'].pop()
   with self.assertRaises(ValueError):R._after_full_qualification_math(p)
if __name__=='__main__':unittest.main()

import copy,importlib.util,json,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('M',P/'checked_pair_math.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
class Tests(unittest.TestCase):
 def fixture(self):
  ids=[1]*131;data={};pairs=[];start=100
  env={'need':M.need,'MODEL':'qwen36-mxr-eager'}
  _,nodes=M.functions(M.READER,M.READER_SHA,{'expected_request'},env);exec(compile(__import__('ast').Module(body=nodes,type_ignores=[]),'actual-reader','exec'),env)
  base=['python3','-m','vllm.entrypoints.openai.api_server','--model','/models/Qwen3.6-27B','--tensor-parallel-size','4','--max-num-seqs','1','--enforce-eager','--no-enable-prefix-caching','--no-async-scheduling']
  for mode,arm in [('OFF','native_ar'),('ON','bole')]:
   m=dict(performance_arm=arm,common_collective_configuration=dict(schema='bole.common-collective-configuration/v1',hccl_deterministic='true',applies_to=['native_ar','bole']),common=dict(HF32=False,async_scheduling=False,eager=True,mamba_cache_mode='none',prefix_cache=False,profiling=False),performance_profile={'scope':{'output_tokens':1024}},performance_client_contract=dict(output_tokens=1024,input_tokens=131,concurrency=1),
    checkpoint_config_ref='samecfg',checkpoint_index_ref='sameindex',installed_sources='sameinstalled',cache_memory_config='samecache')
   data[arm]=m;data['cmd'+mode]=dict(source=arm,performance_arm=arm,native_MTP=arm=='bole',num_speculative_tokens=8 if arm=='bole' else 0,argv=base+(['--speculative-config',json.dumps(dict(method='mtp',num_speculative_tokens=8))]if arm=='bole' else []))
  for i in range(3):
   pair={'pair_index':i}
   for mode,arm,total in [('OFF','native_ar',1100),('ON','bole',1000)]:
    identity=dict(image='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1',model='qwen36-mxr-eager',input_ref='sameinput',source_ref=arm,server_command_ref='cmd'+mode,execution_arm=arm,runtime_refs='same',process_options_ref='same',resource_profile_ref='same',concurrency=1,capture_off_qualification_ref='pending_fixture_only',main_clock_ref='same',mode=mode,capture_mode='OFF',actual_input_ids=ids,frontend_pid=1,worker_processes=[dict(host_pid=k+1,start_ticks=1,physical=k+4)for k in range(4)],work_start_ns=1,work_deadline_ns=100000)
    observation=dict(request=dict(env['expected_request'](ids),seed=0),ordered_token_ids=[1]*1024,request_id='cmpl-fixture-'+str(i)+mode,request_start_monotonic_ns=start,eof_monotonic_ns=start+total+1,TTFT_ns=100,TPOT_numerator_ns=total-100,TPOT_denominator=1023,T_total_ns=total)
    pair[mode]=dict(identity=identity,observation=observation);start+=total+10
   pairs.append(pair)
  return pairs,data
 def test_distinct_sources_all3_correct_units(self):
  p,d=self.fixture();r=M.checked_math(p,obj=lambda k:d[k])
  self.assertFalse(r['formal_qualification']);self.assertEqual(len(r['pairs']),3)
  self.assertAlmostEqual(r['pairs'][0]['rates']['ON']['TPOT_ms'],900/1023/1e6)
  self.assertAlmostEqual(r['pairs'][0]['rates']['ON']['throughput_tokens_per_second'],1024*1e9/1000)
 def test_refuse_observeroff_short8_tp2_common_drift(self):
  for k in ('observer','short','TP','HCCL','precision','checkpoint','argv'):
   p,d=self.fixture()
   if k=='observer':d['native_ar']['performance_arm']='bole'
   if k=='short':d['bole']['performance_client_contract']['output_tokens']=8
   if k=='TP':d['cmdON']['argv'][d['cmdON']['argv'].index('--tensor-parallel-size')+1]='2'
   if k=='HCCL':d['native_ar']['common_collective_configuration']['hccl_deterministic']='false'
   if k=='precision':d['bole']['common']['HF32']=True
   if k=='checkpoint':d['bole']['checkpoint_config_ref']='foreign'
   if k=='argv':d['cmdON']['argv'].append('--additional-setting')
   with self.subTest(k=k),self.assertRaises(ValueError):M.checked_math(p,obj=lambda n:d[n])
 def test_missing_duplicate_request_pair_overlap(self):
  for k in ('missing','request','pair','overlap','rank','tokens'):
   p,d=self.fixture()
   if k=='missing':p.pop()
   if k=='request':p[1]['OFF']['observation']['request_id']=p[0]['OFF']['observation']['request_id']
   if k=='pair':p[1]['pair_index']=0
   if k=='overlap':p[1]['OFF']['observation']['request_start_monotonic_ns']=1
   if k=='rank':p[0]['OFF']['identity']['worker_processes'].pop()
   if k=='tokens':p[1]['ON']['observation']['ordered_token_ids'].pop()
   with self.subTest(k=k),self.assertRaises(ValueError):M.checked_math(p,obj=lambda n:d[n])
 def test_bad_E2E_not_hidden_by_averaging_or_TPOT(self):
  p,d=self.fixture();p[1]['OFF']['observation'].update(T_total_ns=1099,TPOT_numerator_ns=999)
  with self.assertRaises(ValueError):M.checked_math(p,obj=lambda n:d[n])
if __name__=='__main__':unittest.main()

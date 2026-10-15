"""DL-only CPU saved-raw domain audit DRAFT. Default OFF; never admission.

Unchanged native chunk may be a shared reference component, not a replacement
for testing DeltaLog's changed recurrence/flush or whole-core peer gates.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time

FIELDS = ('base', 'k_log', 'u_log', 'lambda_log', 'decay', 'length')
AUX = FIELDS[1:]
PINNED = {
 'direct_round.py': '60f64d53aae1e126f1a4de244a3cb224facc881e277386bf120d6a5b2988278d',
 'oracle.py': 'cd395a05dbfcb21f1104d617afb1fab6f80374016585e9096ca24d85c2cae97a',
 'consume.py': '4c2c290181cee3d8c41dcac11fcc1d5dfd5d939c90d171fcf028950494e8a2c4',
 'consume_increment.py': '6350f0ee18f29fcd3e2848f8af18ce005e5e41191d44a98a32123a30727aaaf9',
'qwen36_deltalog_fresh/native_fixture.py': 'a19e49b0295e03df4b5771910932e59018d4353623f2edd27a5e7d8a1b2a46e6',
'qwen36_deltalog_fresh/capture_evidence.py': 'a9a8c6c0f65e147ecbfe3245f000ed9a2170f4320387ef2889433aebd26a6b64',
'producer.py': '8884b0011dad98a7ba8e256acb985c78c17f8e408c7a57f45f9fca2665a8844d',
 'qwen36_deltalog_fresh/transform.py': 'b9230fde5a7a45db8fe69af9c1acc7104b7082da81c022a76f594c0c389a899f',
 'qwen36_deltalog_fresh/runtime_helpers.py': '5fcd586ca26b4ef8daa1723d32ad206dcebd527c1b0484bfc2656f5ccb1b20d5',
 'qwen36_deltalog_fresh/provider.py': '55851946ff81b2d8a12c303444d17df3608464af0782e38d6ae7ce3fb9985289',
 'qwen36_deltalog_fresh/primitives.py': 'bc88725f4443ef97886d71dfeb6105a1fc8f5bf762b164fafead81b7b7bce05b',
 'qwen36_deltalog_fresh/contract.py': '60ce142f1467720fbaec93a612a0c806bf982e022e69a74671bcbf5f7fd9dbee',
 'qualification.py': 'fb650e89815133771dd56dbd746b2d3ac57b610d9d6777e6b5882833319b1dd6',
 'flush_increment.py': '1ab2346e32170e679e708056625cabe47df3a3859c7e89a4239192e23d49ec31',
}

def need(value, message):
 if not value: raise ValueError(message)

def ref(path):
 p = Path(path); h = hashlib.sha256(); n = 0
 with p.open('rb') as stream:
  for block in iter(lambda: stream.read(1048576), b''): h.update(block); n += len(block)
 return dict(path=str(p), bytes=n, sha256=h.hexdigest())

def checked(r):
 need(isinstance(r, dict) and set(r) == {'path', 'bytes', 'sha256'}, 'exact Ref3 schema')
 p = Path(r['path']); need(p.is_absolute() and not p.is_symlink() and ref(p) == r, 'exact Ref3 bytes')
 return p

def obj(r): return json.loads(checked(r).read_bytes())

def load(r, name):
 spec = importlib.util.spec_from_file_location(name, checked(r))
 module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def same(torch, a, b):
 return a.dtype == b.dtype and a.shape == b.shape and torch.equal(a.contiguous().view(torch.uint8), b.contiguous().view(torch.uint8))

def pluszero(torch, x): return same(torch, x, torch.zeros_like(x))

def relative(torch, a, b):
 need(bool(torch.isfinite(a).all() and torch.isfinite(b).all()), 'live finite')
 return float((a.double()-b.double()).norm()/max(float(b.double().norm()), 1e-30))

def bounded(metrics, R):
 need(all(k in metrics and type(metrics[k]) in(int,float) and math.isfinite(metrics[k]) for k in('state_error','output_error')),'complete finite numeric metric schema')
 return all(math.isfinite(float(v)) and float(v) <= limit for v, limit in
            ((metrics.get('state_error', 0), R.STATE_LIMIT), (metrics.get('output_error', 0), R.OUTPUT_LIMIT)))

def copy_bounded(metrics,R):
 # Copy has no output readout; do not synthesize an unmeasured output metric.
 need('state_error'in metrics and type(metrics['state_error'])in(int,float)and math.isfinite(metrics['state_error']),'complete finite copy state metric')
 return metrics['state_error']<=R.STATE_LIMIT and all(type(metrics.get(k))is bool and metrics[k] for k in('bitwise','untouched_bitwise','conv_bitwise','descriptors_exact'))

def live_flush_payload(torch, before, after, slot):
 """Only dead k/u poisoning is allowed before the capture; no live writes."""
 for head in range(12):
  length = int(before['length'][slot, head, 0]); need(0 <= length <= 7, 'previous live length')
  need(same(torch, before['u_log'][slot, head, :length], after['u_log'][slot, head, :length]), 'flush rewrote live u')
  need(same(torch, before['k_log'][slot, head//3, :length], after['k_log'][slot, head//3, :length]), 'flush rewrote live k')
 need(same(torch, before['lambda_log'][slot], after['lambda_log'][slot]), 'flush changed lambda payload')

def fingerprint(torch,tensor):
 cpu=tensor.detach().cpu().contiguous()
 return dict(dtype=str(cpu.dtype),shape=list(cpu.shape),sha256=hashlib.sha256(cpu.view(torch.uint8).numpy().tobytes()).hexdigest())

def runtime_source_checked(r,manifest):
 mapping=manifest.get('diagnostic_runtime_sources',{}).get(r['path'])
 if mapping is None:return checked(r)
 need(mapping in manifest['files'].values() and mapping['bytes']==r['bytes'] and mapping['sha256']==r['sha256'],'explicit runtime/container -> host snapshot bytes/SHA source binding')
 return checked(mapping)

def control_proof(torch,controls,manifest):
 need(controls['output_final_state'] is True and controls['head_first'] is False,'native full final state/non-headfirst controls')
 need(controls['metadata_class']=='vllm_ascend.ops.gdn_attn_builder.GDNChunkedPrefillMetadata','actual official metadata type')
 need(controls['metadata_source']['sha256']=='42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16','pinned official metadata source');runtime_source_checked(controls['metadata_source'],manifest)
 meta=controls['metadata'];need(set(meta)=={'cu_seqlens_host','chunk_indices_chunk64_host','chunk_indices_chunk64','chunk_offsets_chunk64','update_chunk_offsets_chunk64','final_chunk_indices_chunk64','chunk_indices_large_block','block_indices_cumsum','num_decodes','cu_seqlens_kern','keep_meta'},'full metadata inventory')
 need(meta['cu_seqlens_host']==dict(kind='tuple',values=[0,64]) and meta['num_decodes']==dict(kind='int',value=0),'actual single64 nondecode prefill metadata')
 need(meta['keep_meta']==dict(kind='none') and meta['cu_seqlens_kern']==dict(kind='none'),'legitimate no-empty-segment None metadata')
 for name in ('chunk_indices_chunk64','chunk_offsets_chunk64','update_chunk_offsets_chunk64','final_chunk_indices_chunk64','chunk_indices_large_block','block_indices_cumsum'):
  row=meta[name];need(row['kind']=='tensor' and type(row['data_ptr']) is int and row['data_ptr']>=0,'real bounded metadata tensor '+name)
  dtype={'torch.int32':torch.int32,'torch.int64':torch.int64,'torch.bool':torch.bool}.get(row['fingerprint']['dtype']);need(dtype is not None,'metadata index dtype')
  value=torch.tensor(row['values'],dtype=dtype).reshape(row['fingerprint']['shape']);need(value.numel()<=1024 and (value.numel()==0 or row['data_ptr']>0) and fingerprint(torch,value)==row['fingerprint'],'metadata values/raw byte fingerprint')
 need(meta['chunk_indices_chunk64_host']['kind']=='tuple' and meta['chunk_indices_chunk64_host']['values']==[0,0],'one registered chunk host index')

def runtime_proof(torch,cap,step,pid,manifest=None):
 manifest={} if manifest is None else manifest
 c=cap['native_call'];need(c['schema']=='deltalog.native-chunk-dispatch/v030' and c['actual_original_call_returned'] is True,'actual original native chunk returned')
 b,a=c['before'],c['after'];need(b['schema']==a['schema']=='deltalog.native-chunk-callable/v030','native callable schema')
 need(b['counter']==step and a['counter']==step+1 and b['pid']==a['pid']==pid,'each actual candidate chunk invocation identity/count')
 for proof in (b,a):
  ids=[proof[key] for key in ('original_id','gdn_alias_id','chunk_alias_id')]
  need(type(ids[0]) is int and ids[0]>0 and ids==[ids[0]]*3,'three actual native callable aliases')
  need(proof['module_file']['sha256']=='6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5','actual native chunk source hash')
  runtime_source_checked(proof['module_file'],manifest)
  chain=proof['unwrap_chain'];need(1<=len(chain)<=16 and len({x['object_id'] for x in chain})==len(chain),'real bounded unwrap chain')
  need(chain[0]['object_id']==ids[0] and chain[-1]['object_id']==proof['unwrapped_id'] and chain[-1]['code_file']==proof['module_file']['path'],'actual unwrapped function source')
 need(all(a[k]==b[k] for k in ('original_id','gdn_alias_id','chunk_alias_id','module_file','unwrapped_id','unwrap_chain')),'callee stable across native return')
 need(a['controls']==b['controls'],'native controls before/after unchanged');control_proof(torch,b['controls'],manifest)
 need(set(b['operands'])==set(cap['inputs']),'complete recorded kwargs source')
 for name,value in cap['inputs'].items():
  op=b['operands'][name]
  if isinstance(value,torch.Tensor):
   need(op['actual']==op['captured']==fingerprint(torch,value) and op['device'].startswith('npu:') and op['data_ptr']>0,'actual argument/raw operand join '+name)
   need(a['input_fingerprints'][name]==op['actual'],'actual native input unchanged after return '+name)
  else:need(type(value) is bool and op==dict(value=value),'native scalar argument identity')
 need(c['returned_output']==fingerprint(torch,cap['output']) and c['returned_state']==fingerprint(torch,cap['final_state']),'native returned output/state raw byte fingerprints')
 return True

def initial_anchor(torch,anchor,source_ref,producer,manifest,batch):
 need(anchor['schema']=='deltalog.independent-initial-anchor/v030' and anchor['source']==source_ref and anchor['plan']==producer['plan'],'source/plan-bound independent initial anchor')
 need(anchor['fixture_source']==manifest['files']['qwen36_deltalog_fresh/native_fixture.py'],'actual fixture source anchor')
 checked(anchor['fixture_source']);need(anchor['config_source']['sha256']=='69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c','actual checkpoint config source');checked(anchor['config_source'])
 return initial_values(torch,anchor,batch)

def initial_values(torch,anchor,batch):
 need(anchor['batch']==batch and anchor['seed']==260815535+batch and anchor['before_any_candidate_dispatch'] is True,'registered independent initial seed/order')
 need(anchor['geometry']==dict(slots=2*batch+4,key_heads=4,value_heads=12,key_dim=128,value_dim=128,conv_dim=2560),'actual initial geometry')
 generator=torch.Generator().manual_seed(260815535+batch)
 base=(torch.randn((2*batch+4,12,128,128),generator=generator)*.005).float()
 conv=(torch.randn((2*batch+4,3,2560),generator=generator)*.01).bfloat16()
 need(same(torch,anchor['generated_base'],base) and same(torch,anchor['generated_conv'],conv),'independently regenerated CPU input anchor')
 state=anchor['candidate_state'];need(set(state)==set(FIELDS)|{'conv'},'complete actual initial state fields')
 need(same(torch,state['base'],base) and same(torch,anchor['native_initial'],base) and same(torch,state['conv'],conv),'generated/native/candidate current initial load identity')
 for name in AUX:
  expected=torch.zeros_like(state[name]);expected[-2:].fill_(13)
  need(same(torch,state[name],expected),'initial aux zero/registered guard bytes '+name)
 need(set(anchor['pointer_identity'])==set(state) and all(type(x) is int and x>0 for x in anchor['pointer_identity'].values()),'actual initial pointer inventory')
 return dict(step=-1,identity=(batch,'eager','mixed-prefill-decode'),state=state,pointer_after=anchor['pointer_identity'])

def transition(torch, R, raw, previous=None,anchor=None):
 """Validate a local mixed transition. Missing global anchors remain missing."""
 ids = raw['ids'].flatten().tolist(); batch = len(ids)-1; slot = raw['prefill_slot']
 need(batch in (1,16) and len(ids) == len(set(ids)) and ids[-1] == slot, 'mixed distinct decode/prefill geometry')
 need(raw['identity'] == (batch, 'eager', 'mixed-prefill-decode'), 'fixture eager identity')
 state = raw['state']; slots = state['base'].shape[0]
 need(slots == 2*batch+4 and all(0 <= x < slots-2 for x in ids), 'registered slot/guard mapping')
 dc = raw['captures']['decode']; pc = raw['captures']['prefill']
 need(len(dc) == len(pc) == 1, 'exact native/candidate dispatch captures')
 d, p = dc[0], pc[0]; before = d['before']; i = d['inputs']
 for st in (state,before):
  for selected in ids:
   length=st['length'][selected,:,0]
   need(bool((length>=0).all() and (length<=7).all()) and same(torch,length,length[:1].expand_as(length)), 'head lengths/capacity')
   need(pluszero(torch,st['length'][selected,:,1:]) and pluszero(torch,st['decay'][selected,:,1:]) and pluszero(torch,st['lambda_log'][selected,:,7:]), 'metadata padding unchanged +0')
 need(i['ssm_state_indices'].flatten().tolist() == ids[:-1], 'decode raw indices join')
 need(i['actual_seq_lengths'].flatten().tolist() == [0]+[1]*batch, 'one-token native individual-length decode sequence ABI')
 need(same(torch, raw['before_base'], before['base'][ids[:-1]]), 'before-base capture join')
 need(same(torch, raw['before_length'], before['length'][ids[:-1], :, 0]), 'before-length capture join')
 need(same(torch, d['output'], raw['candidate_output'][:batch]), 'decode-output writeback join')
 missing = []
 if previous is None and anchor is not None:previous=anchor
 if previous is None:
  need(raw['step'] == 0, 'no previous raw except step0')
  missing.append('independently_saved_initial_full_state_anchor')
 else:
  need(previous['step']+1 == raw['step'] and previous['identity'] == raw['identity'], 'sequential same-fixture raw chain')
  prev = previous['state']
  need(previous['pointer_after'] == raw['pointer_before'], 'cross-step storage identity')
  # Conv was already updated before decode capture. It is checked against
  # native whole-core, not incorrectly compared with the prior turn.
  untouched = [s for s in range(slots) if s != slot]
  need(all(same(torch, prev[n][untouched], before[n][untouched]) for n in FIELDS), 'pre-decode foreign/unflushed state continuity')
  flush_error = relative(torch, before['base'][slot], R.restore(torch, prev, slot))
  need(flush_error <= R.STATE_LIMIT, 'independent prefill flush original FP32 gate')
  need(pluszero(torch, before['decay'][slot]) and pluszero(torch, before['length'][slot]), 'materialization reset +0')
  live_flush_payload(torch, prev, before, slot)
 pi = p['inputs']; expected_initial = before['base'][slot].transpose(-1,-2).unsqueeze(0).contiguous()
 if raw['prefill_has_initial_state']:
  need(same(torch, pi['initial_state'], expected_initial), 'native prefill received flushed initial state')
 else:
  need(pluszero(torch, pi['initial_state']), 'reset reaches native chunk as strict +0')
 need(same(torch, p['final_state'][0].transpose(-1,-2).contiguous(), state['base'][slot]), 'native final-state physical base writeback')
 need(same(torch, p['output'][0], raw['candidate_output'][batch:]), 'native prefill output writeback')
 for name in AUX:
  need(pluszero(torch, state[name][slot]) and same(torch, state[name][slot], raw['prefill_aux_after'][name]), 'prefill aux reset byte join '+name)
 need(raw['pointer_before'] == raw['pointer_after'], 'in-turn actual pointers stable')
 need(same(torch, state['conv'], raw['native_conv']), 'unchanged convolution native peer')
 free = [s for s in range(slots) if s not in ids]
 need(all(same(torch, state[n][free], v) for n,v in raw['unchosen'].items()), 'unchosen strict bytes')
 need(all(same(torch, state[n][-2:], v) for n,v in raw['guards'].items()), 'guard strict bytes')
 need(all(same(torch, raw['inputs'][n], v) for n,v in raw['original_inputs'].items()), 'original input strict bytes')
 # Captures attest operands/results, not runtime function-object identity.
 if 'native_call' not in p:missing.append('native_chunk_runtime_callable_source_and_before_after_counter_certificate')
 return dict(local_transition_pass=True, missing=missing,
             prefill_cpu64_role='retained-diagnostic-not-recurrent-FP32-admission')

def copy_strict(torch, raw):
 before, after = raw['before'], raw['after']; pairs = raw['pairs']; dest = {d for s,d in pairs}
 need(len(dest) == len(pairs) and all(s not in dest for s,d in pairs), 'registered nonoverlapping native copy')
 need(all(same(torch, before[n][s], after[n][d]) for n in before for s,d in pairs), 'copy full base/aux bytes')
 need(all(same(torch, before[n][s], after[n][s]) for n in before for s in range(before['base'].shape[0]) if s not in dest), 'copy source/foreign strict bytes')
 need(all(same(torch, raw['before_conv'][s], raw['after_conv'][d]) for s,d in pairs), 'copy conv bytes')
 need(all(same(torch, raw['before_conv'][s], raw['after_conv'][s]) for s in range(before['base'].shape[0]) if s not in dest), 'copy foreign conv bytes')

def static_proof(manifest):
 """Pinned static evidence only; never upgrades runtime call proof."""
 for name, digest in PINNED.items():
  need(manifest['files'][name]['sha256'] == digest, 'only reviewed DL024 math/oracle '+name)
  checked(manifest['files'][name])
 for item in manifest['files'].values(): checked(item)
 checked(manifest['probe_ref']); checked(manifest['library_ref'])
 f = ast.parse(checked(manifest['files']['qwen36_deltalog_fresh/native_fixture.py']).read_text())
 wrapper = next(n for n in ast.walk(f) if isinstance(n, ast.FunctionDef) and n.name == 'captured_chunk')
 need(sum(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'original_chunk' for n in ast.walk(wrapper)) == 1, 'one direct original chunk invocation in capture wrapper')
 return dict(pinned_static_source=True, native_chunk_runtime_identity_proven=False,
             DL_only=True, MXR_not_qualified=True)

def per_request_metrics(torch,R,raw,D):
 """Independent local readouts; no batch aggregation can hide a request."""
 state=raw['state'];ids=raw['ids'].flatten().tolist();batch=len(ids)-1;rows=[]
 dc=raw['captures']['decode'];need(len(dc)==1,'one decode capture')
 cap=dc[0];i=cap['inputs'];slots=i['ssm_state_indices'].flatten().tolist()
 need(slots==ids[:-1] and len(slots)==len(set(slots)), 'independent row/slot input mapping')
 need(math.isclose(float(i['scale']),128**-.5,rel_tol=0,abs_tol=1e-12),'fixed original recurrence scale')
 for j,s in enumerate(slots):
  expected,o=R.advance(torch,R.restore(torch,cap['before'],s),i,j)
  rounded=D.round_bf16(torch,o)
  need(cap['output'][j].shape==rounded.shape==(12,128) and cap['output'][j].dtype==torch.bfloat16,'actual BF16 readout exact shape; broadcasting forbidden')
  need(bool(torch.isfinite(o).all() and torch.isfinite(rounded).all() and torch.isfinite(cap['output'][j]).all()),'finite CPU64/direct-RNE/actual readout; overflow rejected')
  row=dict(kind='independent-decode',request=j,uncast_CPU64_output_error=float((cap['output'][j].double()-o).abs().max()/max(float(o.abs().max()),1e-30)),BF16_RNE_floor=float((rounded.double()-o).abs().max()/max(float(o.abs().max()),1e-30)),state_error=relative(torch,R.restore(torch,state,s),expected),output_error=float((cap['output'][j].double()-rounded.double()).abs().max()/max(float(rounded.double().abs().max()),1e-30)))
  row['request_pass']=bounded(row,R);rows.append(row)
 for j,s in enumerate(ids):
  a=raw['candidate_output'][j:j+1]if j<batch else raw['candidate_output'][batch:]
  b=raw['native_output'][j:j+1]if j<batch else raw['native_output'][batch:]
  need(bool(torch.isfinite(a).all()and torch.isfinite(b).all()),'peer live output finite')
  row=dict(kind='whole-core-native-peer',request=j,state_error=relative(torch,R.restore(torch,state,s),raw['native_state'][s]),output_error=float((a.double()-b.double()).abs().max()/max(float(b.double().abs().max()),1e-30)))
  row['request_pass']=bounded(row,R);rows.append(row)
 return rows

def run(source_ref, producer_ref, strict_ref, output):
 need(Path(output).is_absolute() and Path(output).parent.is_dir() and not Path(output).exists(), 'new exclusive absolute output')
 m = obj(source_ref); producer = obj(producer_ref); old = obj(strict_ref)
 need(m['schema'] == 'deltalog.deadpayload-native-bridge-source/v024' and m['default_enabled'] is False, 'only reviewed defaultOFF DL024 source')
 need(producer['schema'] == 'deltalog.actual-fresh-bridge/v5' and producer['source'] == source_ref and producer['NPU'] is True and producer['graph'] is False and producer['fullmodel'] is False, 'actual source-bound eager primitive producer')
 need(old['schema'] == 'deltalog.fresh-bridge-consumption/v5' and old['source'] == source_ref and old['producer'] == producer_ref and old['NPU_reexecuted'] is False and type(old['pass_gate']) is bool, 'actual original strict consumer first; no future PASS')
 proof = static_proof(m)
 # Reuse only independent unchanged scalar/raw consumers, no candidate import.
 sys.path.insert(0, str(checked(m['files']['consume.py']).parent))
 R = load(m['files']['oracle.py'], 'dl029_independent_oracle')
 L = load(m['files']['consume.py'], 'dl029_original_strict_metrics')
 F = load(m['files']['consume_increment.py'], 'dl029_independent_dead_flush')
 D = load(m['files']['direct_round.py'], 'dl035_independent_direct_integer_RNE')
 import torch
 torch.set_num_threads(1); rows=[]; previous={}; anchors={}; errors=[]; missing=set(); started=time.monotonic()
 records=producer['records']; seen=set()
 for record in records:
  need(time.monotonic()-started < 600, 'draft CPU600s budget')
  row=dict(record=record, domain_checks_pass=False)
  try:
   raw=torch.load(checked(record['raw']), map_location='cpu', weights_only=False)
   kind=record['kind']; batch=record['batch']; seen.add((kind,batch))
   if kind == 'mixed':
    need(raw['step'] == record['step'] and raw['prefill_has_initial_state'] is (record['step'] not in (5,33,73,113)), 'source-bound step/reset')
    metrics=L.mixed(torch,R,raw)
    row.update(metrics=metrics,original_prefill_CPU64_pass=all(bounded(x,R) for x in metrics['prefill']))
    # Original whole-core peer and independently changed decode/flush stay hard.
    need(bounded(metrics,R), 'original whole-core native peer gates; uncast decode metrics retained diagnostic')
    need(all(type(metrics[k])is bool and metrics[k] for k in('conv_bitwise','untouched_bitwise','guard_bitwise','inputs_bitwise','pointers_bitwise','prefill_aux_reset_bitwise')),'original strict byte flag schema')
    row['per_request']=per_request_metrics(torch,R,raw,D)
    need(all(x['request_pass'] for x in row['per_request']),'per-request direct-RNE decode/state and original native-peer gates')
    row['all_requests_pass']=True
    if batch not in anchors:
     ar=raw['initial_anchor_ref'];av=torch.load(checked(ar),map_location='cpu',weights_only=False)
     initial=initial_anchor(torch,av,source_ref,producer,m,batch);anchors[batch]=(ar,av,initial)
    ar,av,initial=anchors[batch];need(raw['initial_anchor_ref']==ar,'one immutable initial anchor per batch')
    runtime_proof(torch,raw['captures']['prefill'][0],raw['step'],av['pid'],m)
    row['runtime_operand_immutability_pass']=True
    transition_result=transition(torch,R,raw,previous.get(batch),initial); previous[batch]=raw
    missing.update(transition_result['missing'])
    row.update(transition=transition_result)
   elif kind == 'dead_flush':
    row['metrics']=F.check(torch,raw)
    for slot in raw['ids'].flatten().tolist():
     need(pluszero(torch,raw['after']['decay'][slot]) and pluszero(torch,raw['after']['length'][slot]), 'flush strict +0 reset')
   elif kind == 'copy':
    row['metrics']=L.copied(torch,R,raw); copy_strict(torch,raw)
    need(copy_bounded(row['metrics'],R), 'original copy independent gate')
   else: raise ValueError('unknown raw kind')
   row['domain_checks_pass']=True
  except Exception as error:
   row['failure']=repr(error); errors.append(dict(record=record,error=repr(error)))
  rows.append(row)
 try:
  need(producer['primary'] is None and producer['steps'] in (16,160), 'complete actual producer')
  need(seen == {(k,b) for k in ('mixed','copy','dead_flush') for b in (1,16)}, 'all domain/batch coverage')
  for b in (1,16):
   need([r['step'] for r in records if r['kind']=='mixed' and r['batch']==b] == list(range(producer['steps'])), 'all mixed steps no duplicate/gap')
   need([r['length'] for r in records if r['kind']=='copy' and r['batch']==b] == [1,7], 'copy length1/7')
   flush=[r['metrics'] for r in rows if r['record']['kind']=='dead_flush' and r['record']['batch']==b and r['domain_checks_pass']]
   need(len(flush)==2 and any(x['length0'] for x in flush) and any(x['partial_live'] for x in flush), 'real zero/partial dead flush')
 except Exception as error: errors.append(dict(coverage_error=repr(error)))
 result=dict(schema='deltalog.direct-RNE-domain-audit/v035',source=source_ref,producer=producer_ref,original_strict_consumer=strict_ref,
  original_strict_result_preserved=dict(pass_gate=old['pass_gate'],primary=old['primary']),static_source=proof,rows=rows,failures=errors,
  missing_evidence=sorted(missing),domain_checks_pass=not errors,complete_proof=False,diagnostic_qualified=False,model_ready=False,
  performance_ready=False,NPU_reexecuted=False,preregistration_required=True,
  prefill_CPU64_diagnostic_only=True,old_thresholds_unchanged=True,MXR_qualification=False,validation_contract=dict(schema='deltalog.independent-CPU64-operational-recurrence-direct-integer-BF16-RNE/v035',output_limit=.00303,state_limit=7.92e-7,per_request_worst=True,seed_base=260815535,uncast_metrics_diagnostic_only=True),
  anchors={str(b):r[0] for b,r in anchors.items()},
  remaining='actual NPU execution/independent review/preregistration; not algorithm success')
 with Path(output).open('x',encoding='utf8',newline='\n') as stream: json.dump(result,stream,sort_keys=True,allow_nan=False)
 return result

def main():
 if '--execute' not in sys.argv: print('disabled: DL-only diagnostic draft; no qualification'); return 0
 parser=argparse.ArgumentParser(allow_abbrev=False);parser.add_argument('--execute',action='store_true')
 for key in ('source-ref','producer-ref','strict-consumer-ref','output'): parser.add_argument('--'+key,required=True)
 args=parser.parse_args()
 run(json.loads(args.source_ref),json.loads(args.producer_ref),json.loads(args.strict_consumer_ref),args.output)
 return 0

if __name__ == '__main__': raise SystemExit(main())

"""Review exact actual installed wire sources. Local files only."""
import ast,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent.parent

def ref(p):b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
R=P/'references';S=R/'completion_serving.py';Q=R/'completion_protocol.py';I=R/'NATIVE_INDEX.json';C=R/'NATIVE_COPY_RECEIPT.json';A=W/'g2_review_v11_source/SOURCE_BOUND.json'
for p,w in [(S,(27822,'c67bff55fa29c5f89000c3afdc9c7c66305612b13a8a1d85976e5872cee086d7')),(Q,(21247,'93c720549f2a9ef217d7c2a60710225c862032517520dd9ba693d4820f55365c')),(I,(7574,'c928f1d9d9240ee07e18895628cab916c4d64ab9e720b9819830d794fafdb18e')),(C,(7053,'60758ecec7b80235ce6aa645b826b48a38b2502ceac34ec129b0159d937583ec')),(A,(824421,'0cb8a78ee572778434b7b64f494fa42de46cdf4561c235effce3440a8b294f01'))]:
 r=ref(p);assert(r['bytes'],r['sha256'])==w
idx=json.loads(I.read_bytes());receipt=json.loads(C.read_bytes());m=json.loads(A.read_bytes());serv=idx['completion_serving']
assert serv['runtime_ref']['path']=='/vllm-workspace/vllm/vllm/entrypoints/openai/completion/serving.py'
assert(serv['runtime_ref']['bytes'],serv['runtime_ref']['sha256'])==(ref(S)['bytes'],ref(S)['sha256'])==(serv['snapshot_ref']['bytes'],serv['snapshot_ref']['sha256'])
assert next(r for r in receipt['files']if r['name']=='completion_serving')==dict(name='completion_serving',requested_path=serv['runtime_ref']['path'],copy=serv['snapshot_ref'])
assert receipt['image']=='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
assert(m['runtime_sources']['completion_protocol']['bytes'],m['runtime_sources']['completion_protocol']['sha256'])==(ref(Q)['bytes'],ref(Q)['sha256'])==(m['files']['evidence/service_runtime/completion_protocol.py']['bytes'],m['files']['evidence/service_runtime/completion_protocol.py']['sha256'])
anchors={}
for f,ranges in [(S,[(224,235),(398,436),(451,474)]),(Q,[(145,154),(335,343),(527,555)])]:
 lines=f.read_text().splitlines();anchors[f.name]=dict(full_source=ref(f),exact_lines=[dict(line=i,text=lines[i-1])for a,b in ranges for i in range(a,b+1)])
v=dict(schema='bole.fixed1024-SSE-actual-installed-source-review/v1',status='SOURCE_ONLY',actual_image=receipt['image'],actual_stopped_copy_CID=receipt['cid'],serving=serv,protocol_runtime_ref=m['runtime_sources']['completion_protocol'],protocol_actual_host_snapshot=m['files']['evidence/service_runtime/completion_protocol.py'],actual_v11_full_SOURCE=ref(A),snapshot_closure_local=ref(I),snapshot_copy_receipt_local=ref(C),before_inspect_ref=receipt['before'],after_inspect_ref=receipt['after'],full_inspect_local_copy_present=False,source_anchors=anchors,wire_inference='Actual request.stream selects completion_stream_generator; return_token_ids yields output.token_ids as per-event delta in choices[0].token_ids; optional prompt_token_ids is separate; usage choices=[] and [DONE] contain no generated tokens.',timing_boundary_inference='Assign a completed SSE event the receive_monotonic_ns of the actual read1 chunk containing its terminal blank line; every delta token shares that event time, without interpolation.',actual_MODEL_four_Refs=None,actual_production_qualification=None,actual_HTTP=False,formal_success=False,NPU=False)
fixed=P.parent/'g3_long_output_v3/service_client.py';text=fixed.read_text();tree=ast.parse(text);method=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='inputs');body=ast.get_source_segment(text,method)
assert "'Explain how trees grow. '*256"in body and 'add_special_tokens=False'in body and 'return ids[:131]'in body
v['fixed_input_recipe_source']=dict(full_original_source=ref(fixed),exact_inputs_function=body,actual_tokenizer_input_Ref_pending=True)
v['fixed_input_recipe_exact']=dict(text='Explain how trees grow. '*256,add_special_tokens=False,take_first_tokens=131,tokenizer='/models/Qwen3.6-27B',actual_tokenizer_required=True)
v['explicit_streaming_changes_from_current_nonstream_client']=['stream=True','stream_options.include_usage=True','echo=False explicitly matches protocol default']
(P/'SOURCE_REVIEW.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(source_review=ref(P/'SOURCE_REVIEW.json'),actual_HTTP=False,NPU=False)))

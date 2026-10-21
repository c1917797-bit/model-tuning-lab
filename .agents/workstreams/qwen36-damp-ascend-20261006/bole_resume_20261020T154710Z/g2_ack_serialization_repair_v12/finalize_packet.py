from pathlib import Path
import ast,hashlib,json,sys,subprocess
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import g2_ack_proof as Q
OVERLAY=['g2_channel.py','g2_consumer.py','g2_finalize.py','g2_software_stages.py','g2_exact_controls.py','g2_ack_proof.py','test_g2_ack_v12.py','ACTUAL_ACK_FIXTURE.json','prepare_g2_ack_v12.py','audit_source_v12.py','ORIGINAL_V11_g2_channel.py.txt','ORIGINAL_V11_g2_consumer.py.txt','ORIGINAL_V11_g2_finalize.py.txt']
def ref(p):
 p=Path(p).resolve();assert p.is_file()and not any(q.is_symlink()for q in(p,*p.parents));b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
pairs={n:Q.check_pair(n,(P/n).read_bytes(),(P/('ORIGINAL_V11_'+n+'.txt')).read_bytes())for n in Q.ORIGINALS}
kept=Q.preserved_functions((P/'g2_channel.py').read_bytes(),(P/'ORIGINAL_V11_g2_channel.py.txt').read_bytes())
assert 'Sender'in kept and 'validate_ack'in kept
py=list(P.glob('*.py'))
for p in py:compile(p.read_bytes(),str(p),'exec')
N=sum(isinstance(n,ast.FunctionDef)and n.name.startswith('test_')for n in ast.walk(ast.parse((P/'test_g2_ack_v12.py').read_bytes())))
assert N==19
checks=[]
for n in('prepare_g2_ack_v12.py','audit_source_v12.py','g2_exact_controls.py','g2_software_stages.py'):
 for flags in ([],['--help']):
  p=subprocess.run(['/usr/bin/python3','-I','-B',str(P/n),*flags],capture_output=True,text=True,timeout=20)
  checks.append(dict(file=n,flags=flags,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
  assert p.returncode==0,(n,flags,p.stderr)
(P/'MAIN_AST_OFF_HELP.json').write_text(json.dumps(dict(AST_files=len(py),cold_checks=checks,actual_NPU=False,actual_sameimage=False),indent=2)+'\n')
(P/'ACK_CODEC_INVERSE.json').write_text(json.dumps(dict(schema='bole.actual-v11-to-v12-lossless-ACK-inverse/v1',baseline=Q.SOURCE,pairs=pairs,original_complete_Sender_and_validator_functions=kept,old_wire_3307=True,canonical_still3197=True,new_wire2846=True,original3072_wire_cap_unchanged=True,all20_semantic_fields_and_full_Ref3_and_cgroup_retained=True,numerical_model_qualification=False),sort_keys=True,indent=2)+'\n')
(P/'README.md').write_text('''G2-v12 is an explicit lossless ACK-wire/v3 repair. Actual v11 first STEP rank0 completed original numerical oracles, then failed before its ACK: default JSON3307B, canonical JSON3197B, original limit3072B. New positional20-field/six-full-Ref3 wire is2846B and strictly reconstructs the complete original semantic ACK/v2 before the unchanged validator. Full cgroup/gates/coverage/oracle hashes remain. Sender and validator AST are unchanged; finalizer only changes ACK C.obj to CH.load. Unknown/missing/duplicate fields, illegal scalar types/bool-as-int, malformed sequences, noncanonical or oversized wire reject. Failed/unACK raw remains; release follows durable validated ACK.
New software is FOUR genuinely executed contexts: source8 279 + source10 25 + source11 18 + current12 19 =341. Only the source8 original whole software entry is rerun; source10/source11 use exact readonly unittest namespaces with no new parent-output RWalias. Metadata5292B stays in its separate120 stage. Original lane300=120+60+120, MAIN firstentry3600/shared cleanup180/cutoff1792597630, byteexact original128 transactions/math thresholds/resources/guest-B CANN remain. No phase renewal, skipped coverage or cached PASS.
MAIN host19 controls are an explicit host-only check, not same-image/model qualification. Actual sourceprepare/audit, fresh341 software/native parser/actual saved cold handoff must pass before a NEW finite TP4 model. All model/all-frame/task/performance/formal qualification stays pending. Old v11 failures and retained raw remain immutable. Future G3 cost and final ACK readers must explicitly use the new source-owned CH.load; old v11 MODEL helper cannot accept v12 or the failed v11 MODEL.
''')
m=dict(schema='bole.G2-lossless-ACK-wire-source-only-packet/v12',frozen=True,default_enabled=False,baseline=Q.SOURCE,overlay_files={n:ref(P/n)for n in OVERLAY},inventory_paths_are_actual_MAIN_packet_refs=True,actor_whole_inverse=pairs,original_sender_and_validator_AST=kept,new_included_controls=19,prospective_sameimage_cases=341,software_sources_fresh=dict(source8=279,source10=25,source11=18,current12=19),allocation_seconds=dict(parent279=120.,controls=60.,metadata=120.),aggregate_cap_seconds=300,phase_seconds=3600,cleanup_seconds=180,wire_schema='bole.actual-independent-frame-ACK-wire/v3',semantic_schema='bole.actual-independent-frame-ACK/v2',ACK_wire_cap_bytes=3072,actual_reconstructed_STEP_wire_bytes=2846,original128_transactions_and_math_unchanged=True,actual_sameimage_executed=False,actual_model_executed=False,actual_successful_MODEL_ref=None,numerical_model_qualification=False,formal_success=False,NPU=False)
assert not(P/'MANIFEST.json').exists()
(P/'MANIFEST.json').write_text(json.dumps(m,sort_keys=True,indent=2)+'\n')
flat=dict(schema='bole.G2-v12-exact-flat-transfer/v1',files={n:(P/n).read_text()for n in [*OVERLAY,'sourceio.py','g1_contract.py','g2_contract.py','g2_cold_clock.py','README.md','ACK_CODEC_INVERSE.json','MANIFEST.json']})
(P/'FLAT_TRANSFER.json').write_text(json.dumps(flat,sort_keys=True)+'\n')
print(json.dumps(dict(manifest=ref(P/'MANIFEST.json'),flat=ref(P/'FLAT_TRANSFER.json'),prospective_sameimage=341,AST_files=len(py),OFF_help_checks=len(checks),actual_model_qualified=False)))

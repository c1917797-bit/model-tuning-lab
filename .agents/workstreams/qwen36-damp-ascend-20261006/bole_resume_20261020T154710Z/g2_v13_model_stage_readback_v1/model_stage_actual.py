"""Readonly stdlib CPU qualification; never launch work or accept caller PASS."""
import argparse
import ast
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys
from types import SimpleNamespace as NS

ROOT=Path('/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v11')
SOURCE=dict(path=str(ROOT/'SOURCE_BOUND.json'),bytes=824421,sha256='0cb8a78ee572778434b7b64f494fa42de46cdf4561c235effce3440a8b294f01')
OUT=ROOT.with_name('run-'+ROOT.name)
CPU_OUT=Path(str(OUT)+'-CPU')
RESULT=dict(path=str(CPU_OUT/'RESULT.json'),bytes=1070384,sha256='dfaed25ecf0b2bff4807cd2ce7a5c86e800aaab6416ef09a01c9ccf74f776fb8')
V11_MANIFEST=(10521,'bf3c31c8b13fc2de9e795456aebad2a50455feec675f1721eeaec2e47be74dcd')
V10_SOURCE=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v10/SOURCE_BOUND.json',bytes=752323,sha256='af907e01b7143a476459095fad32db5110a940392584c40a4886763a03a9081c')
V9_SOURCE=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v9/SOURCE_BOUND.json',bytes=682545,sha256='7dafb83330946b4690824d188f688db8f445270e3c1f86d119c0728e269fef1f')
V8_SOURCE=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v8/SOURCE_BOUND.json',bytes=612583,sha256='ae03ae1e05711105642b4d07763384f38ed190f1defa4a9ac748389e88daa601')
CUTOFF='2026-10-21T15:47:10+00:00'
ROLES=('consumer_owner_ref','model_owner_ref','consumer_inspect','model_inspect')
# Explicit actual source10 declared-host snapshot names, retained byteexact in source11.
RUNTIME_HOST_KEYS={'ascend_attention': 'evidence/ascend_attention.py',
 'ascend_forward_context': 'evidence/ascend_forward_context.py',
 'ascend_vocab': 'evidence/actual660_ascend_vocab_parallel_embedding.py',
 'attention': 'evidence/attention.py',
 'base_proposer': 'evidence/service_runtime/base_proposer.py',
 'base_runner': 'evidence/base_runner.py',
 'block_table': 'evidence/block_table.py',
 'completion_protocol': 'evidence/service_runtime/completion_protocol.py',
 'contextlib': 'evidence/contextlib.py',
 'forward_context': 'evidence/forward_context.py',
 'gdn': 'evidence/gdn.py',
 'gdn_base': 'evidence/gdn_base.py',
 'gpu_input_batch': 'evidence/service_runtime/gpu_input_batch.py',
 'logits_processor': 'evidence/actual660_logits_processor.py',
 'mtp': 'evidence/mtp.py',
 'npu_input_batch': 'evidence/service_runtime/npu_input_batch.py',
 'outputs': 'evidence/service_runtime/outputs.py',
 'proposer': 'evidence/proposer.py',
 'qwen35': 'evidence/qwen3_5.py',
 'qwen_gdn': 'evidence/qwen_gdn_linear_attn.py',
 'qwen_next': 'evidence/qwen3_next.py',
 'qwen_next_mtp_patch': 'evidence/worker_patch/patch_qwen3_next_mtp.py',
 'qwen_patch': 'evidence/root_witness_actual_patch.py',
 'rotary': 'evidence/service_runtime/rotary_embedding.py',
 'runner': 'evidence/runner.py',
 'sampling_metadata': 'evidence/service_runtime/sampling_metadata.py',
 'sampling_params': 'evidence/service_runtime/sampling_params.py',
 'torch_contextlib': 'evidence/service_runtime/torch_contextlib.py',
 'torch_grad_mode': 'evidence/service_runtime/torch_grad_mode.py',
 'vocab_parallel': 'evidence/actual660_vocab_parallel_embedding.py',
 'worker': 'evidence/worker.py',
 'worker_patch_init': 'evidence/worker_patch/__init__.py'}
READS={}


import subprocess
V11_SOURCE=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v11/SOURCE_BOUND.json',bytes=824421,sha256='0cb8a78ee572778434b7b64f494fa42de46cdf4561c235effce3440a8b294f01')

ROOT=Path('/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v12')

OUT=Path('/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v12')

CPU_OUT=Path(str(OUT)+'-CPU')

SOURCE=dict(path=str(ROOT/'SOURCE_BOUND.json'),bytes=908497,sha256='6c925c8e827b4761926645b89c5897ef25d7e81a80664cb4b4def75076c05d15')

RESULT=None

ACK_MANIFEST=(6678,'90b8fbfaa69cd2075fd596224f51ef822020115fa189c6e7356376daaecaa46f')

ACK_AUDIT=(4613,'8fea08308fc18a817481a236694a636c5eec6f9ec1ee24f365c7839f0b1f870c')

ACK_PREPARER=(14137,'decce5414b917d26b1e9c5d2627aa37e228223111c031b2b62150578937ab4cb')

RESULT={'path': '/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v12-CPU/RESULT.json', 'bytes': 1202315, 'sha256': 'd7f90208d7faf168fda68d61b08e15c066e00b0e37da54111445bd41b9b34cee'}
UNIT_REF={'path': '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/G2_V12_CPU_SYSTEMD_TERMINAL.json', 'bytes': 361, 'sha256': 'f98de0d3d059dd979f24ab662d50c8908d1be5caa604825372c3aeceb69341c3'}

import ast
SOURCE12=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v12/SOURCE_BOUND.json',bytes=908497,sha256='6c925c8e827b4761926645b89c5897ef25d7e81a80664cb4b4def75076c05d15')

ROOT=Path('/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v13')

OUT=Path('/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v13')

CPU_OUT=OUT

SOURCE=dict(path=str(ROOT/'SOURCE_BOUND.json'),bytes=994678,sha256='545e09b8bd8e598830cd81ab2ba3be6c5a6b775d1d35f263ed6d3519a4145345')

RESULT=None

UNIT_REF=None

HTTP_MANIFEST=(1321,'5b29f5fe4647587a8e49e65291061c79a46e57709e62398bec234d6d11e1c6f7')

HTTP_FILES={'g2_http_visibility_v13.py':(4644,'226f447e2944081dd0310ebe1b93e1b6253c76a2bf33dc99c9e68d61011cddbf'),'prepare_g2_http_v13.py':(14693,'9a5dd3de8fab53bd48807f44ff733678e8ce643dd16ffd5f2e1a48dc123634c1'),'test_g2_ack_http.py':(7694,'2151bd877bc0511b9339169e5fc675915dbdb80ad45652ed9c67732482302972')}

SAVED_CPU341=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/G2_V12_CPU_READBACK.json',bytes=787650,sha256='259c07e794a336f66678b1c9caceb8c8200b157b897764f6e980c28c63904a5a')

CPU341_READER=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/g2_v12_cpu_readback_v2/readback_cpu.py',bytes=51180,sha256='bbd3f5502ab28f9fe5957c678114faaf34a9a5b70419c97c8681f22f83e18c33')

CPU341_RESULT=dict(path='/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v12-CPU/RESULT.json',bytes=1202315,sha256='d7f90208d7faf168fda68d61b08e15c066e00b0e37da54111445bd41b9b34cee')

FAILED_MODEL12=dict(path='/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v12/RESULT.json',bytes=1205776,sha256='046dd18f22d6e1df8ea138253fedfdc9862f89ba04e61858d2892dae008b7c0d')

RESULT={'path': '/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v13/RESULT.json', 'bytes': 1340078, 'sha256': 'e326a53f47c65aff4a498ac30da5568009c22e81cd9e469b2f46a28f086ebb67'}
UNIT_REF={'path': '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/G2_V13_MODEL_SYSTEMD_TERMINAL.json', 'bytes': 277, 'sha256': 'a3f485ff01bfafffae781a09054e0cda4b5f2a7b7e31a7c20073341f5dd15f93'}

STAGE_SUMMARY_KEYS=('actual_software_child', 'CPU_child', 'CPU_report', 'CPU_release', 'handoff_saved_stage', 'handoff_cold_child', 'handoff_cold_report', 'handoff_cold_release')
MODEL_SUMMARY_KEYS=('CPU_child', 'CPU_release', 'CPU_report', 'MTP_load', 'MTP_load_receipts', 'actual_client_terminal', 'actual_software_child', 'canary', 'handoff_cold_child', 'handoff_cold_release', 'handoff_cold_report', 'handoff_saved_stage', 'independent', 'independent_release', 'metadata_handoff', 'model_release', 'stream_channel', 'stream_consumer_terminal', 'stream_resource_profile', 'worker_bindings')
MODEL_CONTEXT_HOST_REF={'path': '/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v13/host_service.py', 'bytes': 16157, 'sha256': '62b963b1b96b37d4320bfae5757d7526628c8613e31f6c6a75b5d24687022c41'}

def need(v,message):
    if not v:raise ValueError(message)

def parse(data):
    def pairs(rows):
        result={}
        for k,v in rows:need(k not in result,'unique actual JSON keys');result[k]=v
        return result
    return json.loads(data,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in()).throw(ValueError(x)))

def ref(path):
    p=Path(path);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary absolute file, no symlink')
    a=p.stat();h=hashlib.sha256();size=0
    with p.open('rb')as stream:
        for data in iter(lambda:stream.read(2**20),b''):h.update(data);size+=len(data)
    b=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns)and size==b.st_size,'stable complete actual bytes')
    return dict(path=str(p),bytes=size,sha256=h.hexdigest())

def checked(r):
    need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['path'])is str and type(r['bytes'])is int and r['bytes']>=0 and type(r['sha256'])is str and re.fullmatch('[0-9a-f]{64}',r['sha256']),'strict complete typed Ref3')
    need(ref(r['path'])==r,'actual full path/bytecount/SHA, never caller assertion');READS[r['path']]=r;return Path(r['path'])

def obj(r):return parse(checked(r).read_bytes())

def normalize(r):
    need(type(r)is dict and set(r)in({'path','sha256'},{'path','bytes','sha256'}),'only producer actual Ref2 or Ref3')
    actual=ref(r['path']);need(actual['sha256']==r['sha256']and('bytes'not in r or actual['bytes']==r['bytes']),'whole-byte actual Ref2 normalization');checked(actual);return actual

def one(data,schema):
    rows=[]
    for line in data.splitlines():
        try:v=parse(line)
        except(UnicodeDecodeError,ValueError):continue
        if type(v)is dict and v.get('schema')==schema:rows.append(v)
    need(len(rows)==1,'unique complete actual '+schema+'; no last-line or cached PASS inference');return rows[0]

def finite(v):return type(v)in(int,float)and math.isfinite(v)

def module(r,name):
    p=checked(r);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def source_modules(m):
    sys.path.insert(0,str(ROOT));loaded={}
    names=('sourceio','component_gate','predecessor118t','bind_model','command_contract','g2_cold_parent_output','g2_callee_proof','g2_cold_clock','g2_handoff','g2_contract','g2_host_adapter','external025','g2_ack_proof','g2_software_stages','prepare_g2_phases_v11','g2_executor_proof','owned_create','prepare_g2_ack_v12','g2_http_visibility_v13','prepare_g2_http_v13')
    for name in names:
        need(name not in sys.modules,'fresh independent reader source namespace '+name)
        value=importlib.import_module(name);need(ref(value.__file__)==m['files'][name+'.py'],'exact actual source-owned original helper '+name);loaded[name]=value
    return NS(**loaded)




def runtime_routes(m):
    need(set(m['runtime_sources'])==set(RUNTIME_HOST_KEYS),'all and only exact declared installed-to-host source routes; no prefix/hash fallback')
    rows={}
    for key,name in RUNTIME_HOST_KEYS.items():
        actual=m['runtime_sources'][key];host=m['files'][name];checked(host)
        need(type(actual)is dict and set(actual)=={'path','bytes','sha256'}and type(actual['path'])is str and Path(actual['path']).is_absolute()and type(actual['bytes'])is int and actual['bytes']>0 and type(actual['sha256'])is str and re.fullmatch('[0-9a-f]{64}',actual['sha256']),'strict declared installed Ref3, never a host path substitution')
        need(host['path']==str(Path(m['root'])/name)and(host['bytes'],host['sha256'])==(actual['bytes'],actual['sha256']),'explicit declared whole-byte host snapshot for installed '+key)
        rows[key]=dict(runtime_ref=actual,host_snapshot_ref=host)
    return rows


def source_gate(sr):
    need(SOURCE is not None and sr==SOURCE,'only actual fully pinned prepared/audited SOURCE13, never caller substitution')
    m=obj(sr);need(m['root']==str(ROOT)and m['output_root']==str(OUT)and m['prepared_only']is False and m['default_enabled']is False and m['service_required_sameimage_software_cases']==349,'actual defaultOFF source13 software349 profile')
    for r in(*m['files'].values(),*m['dependencies']):checked(r)
    runtime_snapshots=runtime_routes(m);parent=obj(SOURCE12)
    for r in(*parent['files'].values(),*parent['dependencies']):checked(r)
    proof=m['g2_http_visibility_v13'];need(proof['parent_source']==SOURCE12,'exact actual source12 parent layer')
    manifest_ref=proof['manifest'];need((manifest_ref['bytes'],manifest_ref['sha256'])==HTTP_MANIFEST,'exact frozen new HTTP source layer manifest');obj(manifest_ref)
    for name,wanted in HTTP_FILES.items():r=m['files'][name];need((r['bytes'],r['sha256'])==wanted,'whole reviewed new HTTP layer '+name)
    preparer=proof['actual_preparer'];need((preparer['bytes'],preparer['sha256'])==HTTP_FILES['prepare_g2_http_v13.py']and checked(preparer).read_bytes()==checked(m['files']['prepare_g2_http_v13.py']).read_bytes(),'exact producer and byteequal source-owned preparer copy')
    need(proof['new_HTTP_controls']==8 and proof['original_ACK_controls']==19 and proof['current_ACK_pattern_cases']==27 and proof['HTTP_output_relative']=='dense/receipts/STREAM'and proof['original_phase_seconds']==3600 and proof['cleanup_seconds']==180 and proof['fixed_cutoff']==1792597630,'explicit eight new HTTP controls, unchanged scope/budgets')
    for k in('actual_current_stage_source_is_SOURCE_BOUND','inherited_current12_label_is_runner_compatibility_only','inherited_ACK_v12_descriptor_is_historical_layer','all_original341_test_files_byteexact','HTTP_files_counted_by_unchanged_finalizer','no_new_mount','no_new_RW_alias'):need(proof[k]is True,'explicit HTTP migration scope '+k)
    changed={'host_service.py','contract090.py','G2_STREAM_EDITS_V1.json'};ledger=obj(proof['whole_current_inverse'])
    need(ledger==obj(m['files']['G2_HTTP_EDITS_V13.json'])and ledger['schema']=='bole.exact-G2-HTTP-output-visibility-inverse/v13'and ledger['baseline']==SOURCE12 and set(ledger['files'])==changed,'complete exact three-file HTTP layer inverse')
    for name,row in ledger['files'].items():need(row['before']==parent['files'][name]and row['after']==m['files'][name]and row['edits']==[dict(before=checked(row['before']).read_text(),after=checked(row['after']).read_text())],'complete original/current inverse operands '+name)
    for name,r in parent['files'].items():
        if name not in changed:need(checked(r).read_bytes()==checked(m['files'][name]).read_bytes(),'all source12 tests/ACK/runner/math128/client/finalizer/identity/clock whole bytes '+name)
    mods=source_modules(m);H=mods.g2_http_visibility_v13;need(H.SOURCE12==SOURCE12 and H.HOST_REF==parent['files']['host_service.py'],'actual source-bound original HTTP host operands')
    host_proof=H.audit_host(checked(parent['files']['host_service.py']).read_text(),checked(m['files']['host_service.py']).read_text());need(host_proof['whole_file_inverse']is True and host_proof['whole_AST_inverse']is True,'only actual producer output/readback two-anchor delta')
    required=dict(parent['service_software_scope']);required['new_current_cases']=27
    need(m['service_software_scope']==required and required['parent_source']==V8_SOURCE and required['controls_source']==V10_SOURCE and required['historical_stage_source']==V11_SOURCE,'same four source contexts; current12 label actually source13/27')
    mods.g2_software_stages.scope(m,sr)
    saved=obj(SAVED_CPU341);need(saved['source']==SOURCE12 and saved['result_ref']==CPU341_RESULT and saved['reader_ref']==CPU341_READER and saved['sameimage_341_parser_and_actual_cold_handoff_pass']is True and saved['all_owned_stopped_retained']is True and saved['reader_source_before_after_equal']is True and saved['numerical_model_qualification']is False,'exact actual source12 CPU341 qualification only')
    checked(CPU341_READER)
    for r in saved['independent_readback_refs']:checked(r)
    C=mods.sourceio;canonical=C.ref(sr['path']);need(canonical==sr,'canonical source13 Ref for exact argv order')
    collector_ref=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/g2_control_ref_repair_v5/prepare_g2_control_v5.py',bytes=16604,sha256='ce4f5c41be679f0f969b7178e02667461a7f2f601d7c5c8f19c04dabb8f23dd3')
    collector_rows=[r for r in parent['dependencies']if r==collector_ref]
    need(len(collector_rows)==1,'one exact canonical original collector Ref; other historical same-byte paths are separate evidence')
    checked(collector_ref)
    collector=mods.prepare_g2_http_v13.collector(parent);need(ref(collector.__file__)==collector_ref,'exact source-owned original collector, never current-root binder for old namespace')
    baseline=collector.collect(SOURCE12);oldrefs=baseline['refs'];oldcomplete={}
    need(baseline['commands']==ref(Path(parent['root'])/'COMMANDS.json')and obj(baseline['commands'])['required_sameimage_software_cases']==341,'actual original COMMANDS and literal argv checked in fresh exactsource12 subprocess')
    for r in oldrefs:checked(r);need(r['path']not in oldcomplete or oldcomplete[r['path']]==r['sha256'],'no conflicting source12 closure');oldcomplete[r['path']]=r['sha256']
    oldresult=obj(CPU341_RESULT);need(oldresult['source']==SOURCE12 and oldresult['cpu_only']is True and oldresult['primary']is None and oldresult['secondary']==[]and oldresult['source_before']==oldresult['source_after']==oldcomplete and oldcomplete and saved['source_readset_count']==len(oldcomplete),'actual original341 owner/source closure reopened')
    failed=obj(FAILED_MODEL12);need(failed['source']==SOURCE12 and failed['cpu_only']is False and failed['primary']is not None and failed['secondary']==[]and failed['source_before']==failed['source_after']==oldcomplete,'actual failed MODEL12 retained only as failure provenance')
    need(checked(m['files']['g2_ack_proof.py']).read_bytes()==checked(parent['files']['g2_ack_proof.py']).read_bytes(),'unchanged exact ACK fixture/inverse proof helper')
    ack_parent,ack_observed,ack_cause=mods.prepare_g2_ack_v12.evidence();ack=parent['g2_ack_serialization_v12']
    need(mods.prepare_g2_ack_v12.SOURCE==V11_SOURCE and ack['parent_source']==V11_SOURCE and all(ack[k]==v for k,v in ack_cause.items()),'original failed11 ACK-cause proof reexecuted from unchanged helper')
    def top(source,name):
        found=[n for n in ast.parse(source).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name==name];need(len(found)==1,'one exact original definition '+name);return ast.dump(found[0],include_attributes=False)
    oldchannel=checked(ack_parent['files']['g2_channel.py']).read_text();currentchannel=checked(m['files']['g2_channel.py']).read_text()
    for name in('Sender','validate_ack'):need(top(oldchannel,name)==top(currentchannel,name),'original sender/semantic ACK validator unchanged '+name)
    snapshot=mods.g2_callee_proof.verify_snapshot(m);need(snapshot['snapshot_imported_as_controller']is False and snapshot['original_ref']==parent['g2_callee_contract_v10']['original025_sources']['safety_host']and m['g2_callee_contract_v10']['original025_sources']==parent['g2_callee_contract_v10']['original025_sources'],'genuine original025 API and CPU snapshot, never fake controller')
    need(mods.g2_executor_proof.consume(m['stream_executor_sources'])==m['stream_executor_proof']and mods.g2_executor_proof.installed(m['stream_executor_sources'])==m['stream_runtime_sources'],'same actual launcher/CPU3 installed proof')
    clock=mods.g2_cold_clock.validate(checked(m['files']['host_service.py']).read_text());need(clock['one_main_entry_clock']is True and clock['phase_seconds']==3600 and clock['shared_cleanup_seconds']==180 and clock['fixed_cutoff']==1792597630,'unchanged original cold entry/remaining/shared cleanup clock')
    refs=[*mods.bind_model.readset(canonical),*m['dependencies'],*mods.command_contract.validate(C,canonical,m)];complete={}
    for r in refs:checked(r);need(r['path']not in complete or complete[r['path']]==r['sha256'],'no conflicting current closed readset');complete[r['path']]=r['sha256']
    mods.actual_ordered_readset=refs
    for path,digest in oldcomplete.items():need(complete.get(path)==digest,'complete original source12 closure retained in current immutable readset')
    need(complete.get(FAILED_MODEL12['path'])==FAILED_MODEL12['sha256'],'actual failed12 predecessor in immutable closure')
    for r in ack_observed:need(complete.get(r['path'])==r['sha256'],'original ACK failure evidence closed in current readset')
    commands=obj(ref(ROOT/'COMMANDS.json'));need(commands['required_sameimage_software_cases']==349,'actual current349 runnable command scope')
    argv=[sys.executable,'-I','-B',str(checked(m['files']['prepare_g2_http_v13.py'])),'--source-audit','--source-ref',json.dumps(canonical)]
    q=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=600,check=False);need(q.returncode==0,'actual new HTTP-layer readonly source audit reexecuted')
    audited=one(q.stdout,'bole.G2-v13-HTTP-visibility-source-audit/v1');need(audited['source']==sr and audited['readset_count']==len(complete),'new source audit exact source and full current closure')
    audit_record=dict(preparer_ref=m['files']['prepare_g2_http_v13.py'],argv=argv,returncode=q.returncode,stdout=q.stdout.decode('utf-8','strict'),stderr=q.stderr.decode('utf-8','strict'),result=audited)
    authority=dict(source=SOURCE12,CPU341_qualification_ref=SAVED_CPU341,CPU341_reader_ref=CPU341_READER,CPU341_owner_ref=CPU341_RESULT,source12_readset_count=len(oldcomplete),source12_collector_ref=collector_ref,source12_commands_ref=baseline['commands'],all_retained_authority_refs_reopened=True,reused_as_current349_PASS=False,failed_MODEL12_ref=FAILED_MODEL12)
    return m,mods,complete,commands,clock,dict(snapshot,runtime_host_snapshots=runtime_snapshots,HTTP_host_proof=host_proof,source12_unchanged_layer_authority=authority,v13_readonly_source_audit_reexecuted=audit_record)




def metadata(v,sr,source=None):
    need(v['schema']=='bole.service-installed-class-protocol-devicefree/v1'and v['source']==sr and v['NPU']is False and v['actual_model_constructed']is False and v['actual_batch_constructed']is False and v['actual_scheduler_executed']is False and v['model_ready']is False and v['actual_torch_context_class_checked']is True and len(v['classes'])==len(v['complete_native_sources_compiled'])==6 and all(x['full_source_compiled']is True and x['import_executed']is False for x in v['complete_native_sources_compiled']),'actual all installed metadata/complete native compile gates')
    if source is not None:
        refs=source['runtime_sources'];classes=[('vllm.v1.sample.metadata.SamplingMetadata','sampling_metadata'),('vllm.v1.outputs.SamplerOutput','outputs'),('vllm.v1.outputs.ModelRunnerOutput','outputs'),('vllm.entrypoints.openai.completion.protocol.CompletionRequest','completion_protocol'),('vllm.entrypoints.openai.completion.protocol.CompletionResponseChoice','completion_protocol'),('vllm.sampling_params.SamplingParams','sampling_params')]
        need(v['classes']==[dict(cls=cls,source=refs[key])for cls,key in classes],'all six actual installed metadata class source identities')
        compiled=[('worker','NPUWorker',['load_model']),('runner','NPUModelRunner',['_prepare_inputs','_sample','propose_draft_token_ids','sample_tokens','_update_states']),('npu_input_batch','NPUInputBatch',['__init__']),('gpu_input_batch','InputBatch',['no_thinking_budget','_make_sampling_metadata']),('proposer','AscendSpecDecodeBaseProposer',['_propose','set_inputs_first_pass','prepare_inputs_padded']),('base_proposer','SpecDecodeBaseProposer',['_get_positions'])]
        need(v['complete_native_sources_compiled']==[dict(source=refs[key],cls=cls,methods=methods,full_source_compiled=True,import_executed=False)for key,cls,methods in compiled],'six exact complete original native source/method compile operands')
        need(v['actual_HTTP_sampling_params']==dict(n=1,temperature=0.0,top_p=1.0,top_k=0,min_p=0.0,repetition_penalty=1.0,frequency_penalty=0.0,presence_penalty=0.0,max_tokens=4,min_tokens=0,ignore_eos=True,stop=[],stop_token_ids=[],bad_words=[],_bad_words_token_ids=None,logprobs=None,prompt_logprobs=None,logprob_token_ids=None,structured_outputs=None,logit_bias=None,allowed_token_ids=None,extra_args=None,thinking_token_budget=None,repetition_detection=None),'actual native HTTP neutral greedy full4 output sampling policy')

def zero_skip(data,count):
    text=data.decode('utf8','strict');need(re.search(r'^Ran '+str(count)+r' tests? in [0-9.]+s$',text,re.M)is not None and re.search(r'^OK$',text,re.M)is not None and 'skipped='not in text and re.search(r'^FAILED',text,re.M)is None,'actual raw unittest count/success/zero skips '+str(count))

def child(record_ref,c,cid,args,leaf,label):
    rr=normalize(record_ref);v=obj(rr);need(v['child_termination_observed']is True and v['exit_code']==0 and type(v['child_host_pid'])is int and v['child_host_pid']>0,'actual completed original child '+label)
    wanted=c.docker_argv(cid,args);need(v['requested_argv']==wanted and v['actual_host_argv']==['/usr/bin/prlimit','--as=unlimited','--',*wanted],'exact actual CANN original-B child argv '+label)
    so=normalize(v['stdout_ref']);se=normalize(v['stderr_ref']);need(so['path']==str(leaf/(label+'.stdout'))and se['path']==str(leaf/(label+'.stderr')),'complete owned actual child streams '+label)
    return dict(record=rr,value=v,stdout=so,stderr=se)


def safety_validator(m,mods,c):
    # Reexecute the unchanged actual derived inspect/create functions, without
    # importing a controller or calling resource/observe/create/cleanup methods.
    originals=m['g2_callee_contract_v10']['original025_sources'];body=checked(originals['safety_host']).read_bytes();external=mods.external025;external.OUT=CPU_OUT
    text,pairs=mods.g2_host_adapter.derive(body,external);tree=ast.parse(text);wanted={'environment','labels','device_map','create_argv','validate_inspect'};nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name in wanted];need({n.name for n in nodes}==wanted,'exact complete native create/inspect helpers')
    scope=dict(c=c,re=re,Path=Path,MEM=32*2**30,OWNER='bole-root-r6-20261017-001',PHYSICAL=(4,5,6,7),DOCKER='/usr/bin/docker',_EXTERNAL=NS(environment=external.environment,LOG=external.LOG))
    exec(compile(ast.Module(body=nodes,type_ignores=[]),originals['safety_host']['path']+'#source-owned-exact-derived-readback','exec'),scope)
    original_env=scope['environment'];owned=ast.parse(checked(m['files']['owned_substrate.py']).read_text());load=next(n for n in owned.body if isinstance(n,ast.FunctionDef)and n.name=='load');env=next(n for n in load.body if isinstance(n,ast.FunctionDef)and n.name=='environment')
    scope['original_env']=original_env;exec(compile(ast.Module(body=[env],type_ignores=[]),m['files']['owned_substrate.py']['path']+'#exact-original-environment','exec'),scope)
    return NS(validate=scope['validate_inspect'],create=scope['create_argv'],source=originals['safety_host'],derive_pairs=pairs)


def inspect_row(r,cid):
    rr=normalize(r);v=obj(rr);need(v['exit_code']==0 and v.get('error')in(None,'')and v['requested_argv']==['/usr/bin/docker','inspect',cid],'actual exact inspect call')
    rows=parse(v['stdout']);need(type(rows)is list and len(rows)==1,'one complete actual inspect row');return rr,v,rows[0]


class ReadonlyCreateBoundary(RuntimeError):pass


def ordered_owner_expected(m,sr,leaf,owned,c,mods):
    # Persisted OWNED is JSON sort_keys=True. Recreate the original insertion
    # sequence from the actual creator and original ordered source readset;
    # never take mount order from the observed create argv.
    need(Path(leaf)in(CPU_OUT/'cpu-preflight',CPU_OUT/'candidate')and ref(mods.owned_create.__file__)==m['files']['owned_create.py'],'exact source-owned two-helper read-only creator')
    refs=mods.actual_ordered_readset
    need(type(refs)is list and refs and all(type(r)is dict and set(r)=={'path','bytes','sha256'}for r in refs),'actual original source-owned ordered full Ref3 readset')
    calls=[]
    def boundary(label,argv,**kwargs):
        need(label=='unique-name'and argv==['/usr/bin/docker','ps','-a','--filter','name=^/'+owned['name']+'$','--format','{{.ID}}']and not kwargs,'original first exact unique-name boundary; no resource/Docker call executed')
        calls.append((label,argv));raise ReadonlyCreateBoundary('original creator stopped before first resource command')
    ctl=NS(out=Path(leaf),name=owned['name'],expected=None,call=boundary)
    original=m['g2_callee_contract_v10']['original025_sources']['safety_host'];checked(original)
    S=NS(__file__=original['path'],DOCKER='/usr/bin/docker')
    try:mods.owned_create.create(c,S,ctl,sr,refs,'cpu-preflight',ROOT)
    except ReadonlyCreateBoundary:pass
    else:raise ValueError('original creator did not stop at exact first read-only boundary')
    need(len(calls)==1 and type(ctl.expected)is dict and ctl.expected['cid']is None,'genuine original expected captured exactly once before create/start/inspect')
    expected=ctl.expected
    need(set(expected)=={'cid','name','image','arm','source','host_sha256','guest_cpus','mounts'}and all(owned[k]==v for k,v in expected.items()if k not in('cid','mounts')),'actual original expected core owner values exactly match retained OWNED')
    need({key:list(value)for key,value in expected['mounts'].items()}==owned['mounts'],'complete original reconstructed mount keys/source/readonly/alias values equal retained OWNED; no unknown/extra mounts')
    return dict(expected,cid=owned['cid'])


def create_gate(create,owned,expected,validator):
    need(create['exit_code']==0 and create['stdout'].strip()==owned['cid']and create['requested_argv']==validator.create(expected),'actual complete source-owned original create argv and full CID; original insertion order preserved')


def owner_chain(m,sr,leaf,release_ref,c,validator,extra_alias,mods):
    owned_ref=ref(leaf/'OWNED.json');owned=obj(owned_ref);cid=owned['cid'];need(type(cid)is str and re.fullmatch('[0-9a-f]{64}',cid)and owned['source']==sr and owned['arm']=='cpu-preflight'and owned['image']==c.IMAGE and owned['name']=='adakv-tp4-'+CPU_OUT.name+'-'+leaf.name and owned['guest_cpus']==[145]and owned['host_sha256']==validator.source['sha256']and owned['sources']=={'safety_host.py':validator.source['sha256']},'actual exact current CPU owner/source/name/image/controller')
    mounts=owned['mounts'];need(mounts[str(ROOT)]==[str(ROOT),False]and mounts[str(leaf)]==[str(leaf),True]and mounts['/adakv-results']==[str(leaf),True]and mounts[str(extra_alias)]==[str(leaf),True]and all(not rw or Path(p)==leaf for p,rw in mounts.values()),'exact expected CPU owned leaf/readonly source/single declared alias')
    guest_ref=ref(leaf/'GUEST_CPU.json');guest=obj(guest_ref);need(guest['effective_cpus']==[145]and guest['effective_capacity']==1 and guest['cgroup']=='/docker/'+cid and '/docker/'+cid in guest['process']['cgroup']and type(guest['process']['pid'])is int and guest['process']['pid']>0,'actual Devices[] helper CPU/cgroup identity')
    create_ref=normalize(owned['create_receipt']);create=obj(create_ref);expected=ordered_owner_expected(m,sr,leaf,owned,c,mods);create_gate(create,owned,expected,validator)
    release_ref=normalize(release_ref);release=obj(release_ref);need(release['container']==cid and release['stopped']is True and release['retained']is True and release['deleted']is False and release['errors']==[]and release['primary_error']is None and release['protected_boundary']['own_on_protected']is False,'actual clean stopped-retained CPU helper release')
    before_ref,before_raw,before=inspect_row(release['before_inspect'],cid);after_ref,after_raw,after=inspect_row(release['after_inspect'],cid)
    for actual in(before,after):validator.validate(actual,owned)
    need(before['State']['Running']is True and before['State']['Pid']==guest['process']['pid']and not before['State'].get('OOMKilled')and after['State']['Running']is False and after['State']['Pid']==0 and not after.get('ExecIDs')and not after['State'].get('OOMKilled'),'actual CPU init running→stopped and no remaining exec/OOM')
    stop_ref=normalize(release['stop_receipt']);stop=obj(stop_ref);need(stop['exit_code']==0 and stop['requested_argv']==['/usr/bin/docker','stop','--time','15',cid],'actual exact validated own-CID stop; never foreign stop')
    smi_ref=normalize(release['release_smi']);smi=obj(smi_ref);need(smi['exit_code']==0 and smi['requested_argv']==['/usr/local/sbin/npu-smi','info'],'original readonly release observation')
    deadlines=[]
    for v in(before_raw,after_raw,stop,smi):
        need(v['cleanup_safety_only']is True and v['original_admission_failures']==[]and v['formal_cutoff']==CUTOFF and finite(v['formal_deadline_monotonic'])and 0<=v['cleanup_remaining_seconds']<=180 and v['cleanup_resource_snapshot']['formal_limit_bytes']==512*2**20 and v['cleanup_resource_snapshot']['aggregate_peak_rss_kib']<=512*1024,'actual original cleanup/cold deadline/RSS assertions')
        deadlines.append(v['formal_deadline_monotonic'])
    need(len(set(deadlines))==1,'one actual controller clock across cleanup calls')
    return dict(owner_ref=owned_ref,guest_ref=guest_ref,create_ref=create_ref,release_ref=release_ref,before_inspect_ref=before_ref,after_inspect_ref=after_ref,stop_ref=stop_ref,release_smi_ref=smi_ref,cid=cid,formal_deadline_monotonic=deadlines[0],source_owned_original_inspect_and_create_reexecuted=True),owned,before


def stage(sr,row,root,label,argv,cap,lane_start,lane_deadline):
    need(row==dict(terminal=ref(root/'TERMINAL.json'),stdout=ref(root/'STDOUT.raw'),stderr=ref(root/'STDERR.raw')),'exact current stage full raw/terminal paths, never prior run')
    t=obj(row['terminal']);need(t['schema']=='bole.actual-software-stage-terminal/v11'and t['source']==sr and t['label']==label and t['actual_argv']==argv and type(t['child_pid'])is int and t['child_pid']>0 and t['returncode']==0 and t['timed_out']is False and t['primary']is None and t['stdout']==row['stdout']and t['stderr']==row['stderr']and t['complete_streams_retained']is True and t['cached_PASS_reused']is False,'actual exact source/argv/completed original stage')
    need(all(finite(t[k])for k in('start_monotonic','end_monotonic','elapsed_seconds','allocated_seconds'))and 0<t['allocated_seconds']<=cap and 0<=t['elapsed_seconds']<=t['allocated_seconds']and t['end_monotonic']==t['start_monotonic']+t['elapsed_seconds']and lane_start<=t['start_monotonic']<=t['end_monotonic']<=lane_deadline,'actual stage wait/kill time is inside finite stage/common MAIN lane')
    need(row['stdout']['bytes']+row['stderr']['bytes']<=32*2**20,'full retained streams within original explicit byte bound')
    return t


def software_args(sr,phase_deadline):
    r=ref(CPU_OUT/'cpu-preflight/SOFTWARE-ADMISSION.json');a=obj(r)
    need(a['schema']=='bole.actual-host-software-allocation/v11'and a['source']==sr and finite(a['phase_entry'])and a['phase_entry']+3600==phase_deadline and a['allocation_seconds']==dict(parent279=120.,controls=60.,metadata=120.)and a['aggregate_cap_seconds']==300. and a['original_phase_seconds']==3600. and a['original_cleanup_seconds']==180.,'actual host source-bound original firstentry lane admission')
    need(all(finite(a[k])for k in('lane_start','lane_deadline','allocated_seconds'))and a['phase_entry']<=a['lane_start']and 0<a['allocated_seconds']<=300 and a['lane_deadline']==a['lane_start']+a['allocated_seconds']and a['lane_deadline']<=phase_deadline-180+.01,'one finite host lane never renews original phase')
    args=[str(ROOT/'service_entry.py'),'--software','--phase-entry',repr(a['phase_entry']),'--lane-start',repr(a['lane_start']),'--lane-deadline',repr(a['lane_deadline'])]
    need(a['requested_args']==args,'exact actual source-owned software CLI numeric arguments')
    return r,a,args


def software(sr,m,mods,outer,c,admission_ref,admission):
    value=one(checked(outer['stdout']).read_bytes(),'bole.actual-G2-four-source-staged-software-gate/v12');root=CPU_OUT/'cpu-preflight/G2-V12-SOFTWARE'
    need(value['source']==sr and value['tests']==349 and value['source8_fresh_cases']==279 and value['source10_fresh_cases']==25 and value['source11_fresh_cases']==18 and value['current12_fresh_cases']==27 and value['all_tests_passed']is True and value['parent_source']==V8_SOURCE and value['NPU']is False and value['model_ready']is False and value['actual_scheduler_executed']is False and value['timing_is_formal']is False and value['source_validated']['source_validated']is True,'actual full four-source349 result; no cached PASS or source-context conflation')
    start=admission['lane_start'];deadline=admission['lane_deadline'];need(value['phase_entry']==admission['phase_entry']and value['lane_start']==start and value['lane_deadline']==deadline and value['allocation_seconds']==admission['allocation_seconds']and value['aggregate_cap_seconds']==300.,'same host admitted MAIN/stage clock reaches completed result')
    need(finite(value['elapsed_seconds'])and 0<=value['elapsed_seconds']<=admission['allocated_seconds']and finite(value['controls_total_elapsed_seconds'])and 0<=value['controls_total_elapsed_seconds']<=60,'actual total/control clocks fit original finite allocation')
    guest_ref=value['admission'];need(guest_ref==ref(root/'ADMISSION.json'),'exact actual guest admission path');guest=obj(guest_ref)
    need(guest['schema']=='bole.actual-four-source-software-admission/v12'and guest['source']==sr and guest['phase_entry']==admission['phase_entry']and guest['lane_start']==start and guest['lane_deadline']==deadline and guest['allocation_seconds']==admission['allocation_seconds']and guest['aggregate_cap_seconds']==300. and guest['original_phase_seconds']==3600. and guest['original_cleanup_seconds']==180. and guest['fixed_cutoff']==1792597630 and finite(guest['guest_entry'])and start<=guest['guest_entry']<=deadline and finite(guest['validation_elapsed_before_parent'])and 0<=guest['validation_elapsed_before_parent']<=60,'source validation and guest entry charged to same original host lane')
    parent=obj(V8_SOURCE);oldroot=Path(parent['root']);oldalias=Path(parent['output_root'])/'cpu-preflight';actual=CPU_OUT/'cpu-preflight';ev=value['parent_software_evidence']['stage']
    parent_t=stage(sr,ev,root/'PARENT279','parent279',[c.PY,'-I','-B',str(oldroot/'service_entry.py'),'--software'],120.,start,deadline)
    raw=checked(ev['stdout']).read_bytes();stderr=checked(ev['stderr']).read_bytes();prior=mods.g2_cold_parent_output.extract(raw,V8_SOURCE,parent)
    need(prior==value['parent_software_result']and prior['tests']==279 and prior['historical_cases']==214 and prior['current_cases']==65,'actual exact original source8 suite279 summary');zero_skip(stderr,65);metadata(prior['actual_installed_metadata'],V8_SOURCE,parent)
    er=value['parent_software_evidence']['extraction'];need(er==ref(root/'PARENT279/EXTRACTION.json'),'actual current original extraction path');extraction=obj(er)
    need(extraction['schema']=='bole.actual-three-source-parent-extraction/v11'and extraction['source']==sr and extraction['parent_source']==V8_SOURCE and extraction['stage']==ev and extraction['original_summary']==prior and extraction['original_source_owned_extract_used']is True and extraction['original_G1_and_G2_controls_really_rerun']is True and extraction['NPU']is False,'actual complete source-owned parent original extractor')
    expected=list(prior['parent_software_evidence'].values());exports=extraction['original_guest_evidence_to_actual_host_refs'];need(len(exports)==4 and len({r['original_guest_ref']['path']for r in exports})==4,'exact four whole-byte original nested214 evidence exports')
    mapping={}
    for row in exports:
        old=row['original_guest_ref'];new=row['actual_host_ref'];need(old in expected and set(old)==set(new)=={'path','bytes','sha256'}and Path(old['path']).is_relative_to(oldalias)and new['path']==str(actual/Path(old['path']).relative_to(oldalias))and(old['bytes'],old['sha256'])==(new['bytes'],new['sha256']),'only declared exact original guest Ref → byteequal current host export')
        path=checked(new);st=path.stat();need(row['same_device_inode']==[st.st_dev,st.st_ino],'actual retained host export inode');mapping[old['path']]=(old,new)
    def exported(r):
        need(r['path']in mapping and r==mapping[r['path']][0],'only four exact known original guest aliases; no path-prefix bypass');return mapping[r['path']][1]
    inner=prior['parent_software_evidence'];g1_stdout=exported(inner['stdout']);g1_stderr=exported(inner['stderr']);g1_terminal_ref=exported(inner['terminal']);g1_extraction_ref=exported(inner['extraction'])
    g1_term=obj(g1_terminal_ref);g1_ext=obj(g1_extraction_ref);g1=obj(parent['service_software_scope']['parent_source']);original=prior['parent_software_result'];g1_raw=checked(g1_stdout).read_bytes()
    helper=module(parent['files']['parent_software_output.py'],'_g2_readback_original_source_owned_G1_summary')
    parsed,summary_line=helper.summary(mods.sourceio,g1_raw,parent_source=parent['service_software_scope']['parent_source'],expected_tests=214)
    need(parsed==original and one(g1_raw,'bole.g1-cold-aggregate-software/v1')==original,'actual fresh nested full214 original stdout');zero_skip(checked(g1_stderr).read_bytes(),214)
    need(g1_term['schema']=='bole.actual-fresh-parent-software-terminal/v4'and g1_term['source']==V8_SOURCE and g1_term['parent_source']==parent['service_software_scope']['parent_source']and g1_term['argv']==[c.PY,'-I','-B',str(Path(g1['root'])/'service_entry.py'),'--software']and g1_term['returncode']==0 and g1_term['primary']is None and g1_term['timed_out']is False and g1_term['complete_streams_retained']is True and g1_term['reused_cached_PASS']is False and g1_term['stdout']==inner['stdout']and g1_term['stderr']==inner['stderr']and finite(g1_term['elapsed'])and 0<=g1_term['elapsed']<=120,'actual original nested214 terminal/argv/freshness/retained streams')
    need(g1_ext['schema']=='bole.unique-exact-parent-software-extraction/v4'and g1_ext['source']==V8_SOURCE and g1_ext['parent_source']==g1_term['parent_source']and g1_ext['terminal']==inner['terminal']and g1_ext['stdout']==inner['stdout']and g1_ext['stderr']==inner['stderr']and g1_ext['summary']==original and g1_ext['summary_line']==summary_line and g1_ext['exactly_one_expected_schema']is True and g1_ext['complete_original_gates_checked']is True and g1_ext['non_JSON_lines_retained']is True and g1_ext['reused_cached_PASS']is False,'complete actual nested214 extraction of original raw result')

    need(set(value['controls'])=={'source10','source11','current12'},'all three exact-source current control stages required')
    last=parent_t['end_monotonic'];control_rows={}
    for role,count,test_source,pattern in(('source10',25,V10_SOURCE,'test_g2_cold*.py'),('source11',18,V11_SOURCE,'test_g2_stage*.py'),('current12',27,sr,'test_g2_ack*.py')):
        row=value['controls'][role];argv=[c.PY,'-I','-B',str(ROOT/'g2_exact_controls.py'),'--execute','--source-ref',json.dumps(sr),'--role',role]
        t=stage(sr,row['stage'],root/role,role,argv,60.,start,deadline);need(last<=t['start_monotonic'],'actual stages execute serially in declared order');last=t['end_monotonic']
        v=one(checked(row['stage']['stdout']).read_bytes(),'bole.actual-exact-source-only-unittest/v12')
        expected=dict(schema='bole.actual-exact-source-only-unittest/v12',source=sr,test_source=test_source,role=role,pattern=pattern,tests=count,all_tests_passed=True,skipped=0,cached_PASS_reused=False,original_software_entry_invoked=False,NPU=False)
        need(v==expected==row['result'],'actual selected-source complete count/zero skip receipt');zero_skip(checked(row['stage']['stderr']).read_bytes(),count);control_rows[role]=dict(stage=row['stage'],result=v)
    meta=value['metadata_stage'];mr=value['actual_installed_metadata_ref'];need(mr==ref(root/'METADATA.json'),'actual original current metadata output file')
    argv=[c.PY,'-B',str(ROOT/'service_metadata.py'),'--execute','--source-ref',json.dumps(sr),'--output',str(root/'METADATA.json')]
    meta_t=stage(sr,meta,root/'METADATA','metadata',argv,120.,start,deadline);need(last<=meta_t['start_monotonic'],'metadata runs after all three complete fresh controls')
    installed=obj(mr);metadata(installed,sr,m);need(installed==value['actual_installed_metadata']==one(checked(meta['stdout']).read_bytes(),'bole.service-installed-class-protocol-devicefree/v1'),'unchanged original full metadata CLI actually completed and full stdout/file/result join')
    controls_min=meta_t['end_monotonic']-start-parent_t['elapsed_seconds']-meta_t['elapsed_seconds']
    need(0<=controls_min<=value['controls_total_elapsed_seconds']and meta_t['end_monotonic']<=start+value['elapsed_seconds']and guest['validation_elapsed_before_parent']<=parent_t['start_monotonic']-start,'all source/hash/export/control/wait costs charged with no common clock reset')
    result_ref=ref(root/'RESULT.json');need(obj(result_ref)==value,'complete guest retained result equals actual outer stdout, not caller summary')
    return dict(outer_child=outer['record'],outer_stdout=outer['stdout'],outer_stderr=outer['stderr'],host_admission_ref=admission_ref,guest_admission_ref=guest_ref,result_ref=result_ref,source8_fresh279_evidence=value['parent_software_evidence'],source10_fresh25=control_rows['source10'],source11_fresh18=control_rows['source11'],current12_fresh27=control_rows['current12'],metadata_ref=mr,metadata_stage=meta,nested214_actual_host_exports=[g1_stdout,g1_stderr,g1_terminal_ref,g1_extraction_ref],source_owned_original_summary_readers_reexecuted=True,all_raw_zero_skip=True,tests=349,actual_original_3600_and_cleanup180_clock_preserved=True)




def cold_gate(sr,m,mods,summary,c,owner,before):
    stage_ref=summary['handoff_saved_stage'];report_ref=summary['handoff_cold_report'];stage=mods.g2_handoff.verify_saved_probe(mods.sourceio,sr,stage_ref,guest=False);report=obj(report_ref);root=CPU_OUT/'candidate'
    need(stage['actual_probe_root']==str(root)and stage_ref['path']==str(root/'COLD-SAVED-HANDOFF.json')and report_ref['path']==str(root/'HANDOFF-COLD.json'),'actual current candidate leaf complete cold probe')
    proof=m['g2_metadata_handoff_v8'];old=obj(proof['failed_source']);originals={n:old['files'][n]for n in('g2_channel.py','g2_finalize.py','sourceio.py','g1_contract.py','g2_contract.py')}
    need(report['schema']=='bole.actual-Devices0-full-channel-handoff-cold/v1'and report['source']==sr and report['stage']==stage_ref and report['evidence_source']==proof['failed_source']and report['original_function_sources']==originals and report['original_functions']==['g2_channel.contract','g2_finalize.owned_channel']and report['all_four_original_files_guest_absent']is True and report['complete_saved_metadata_handoff']is True and report['original_owner_inspection_source_resource_and_mount_assertions_preserved']is True and report['Ref2_inspect_actual_bytes_normalized']is True and report['original_source_and_copies_unchanged']is True and report['Devices']==[]and report['Torch_imported']is False and report['actual_live_identity_qualified']is False and report['saved_stopped_capture_only']is True and report['model_ready']is False and report['formal_success']is False and report['NPU']is False,'actual full source-owned cold CLI executed original readers in Devices[], not a caller flag')
    mounts={x['Destination']:[x['Source'],x['RW']]for x in before['Mounts']};need(mounts==owner['mounts']and mounts[stage['guest_channel_root_alias']]==[str(root),True]and not before['HostConfig'].get('Devices'),'actual cold container readonly visibility and sole declared guest alias')
    for role in ROLES:
        r=stage['roles'][role]['original_actual_ref'];checked(r)
        need(not any(Path(r['path'])==Path(dst)or Path(r['path']).is_relative_to(Path(dst))for dst in mounts),'all four originals absent from actual complete guest mount closure '+role)
    stage_argument=mods.sourceio.ref(stage_ref['path']);need(stage_argument==stage_ref,'exact actual stage Ref rebuilt by original sourceIO key order before argv check')
    args=[str(ROOT/'g2_handoff_cold.py'),'--execute','--source-ref',json.dumps(sr),'--stage-ref',json.dumps(stage_argument),'--output',str(root/'HANDOFF-COLD.json')]
    observed=child(summary['handoff_cold_child'],c,owner['cid'],args,root,'HANDOFF-COLD');printed=[]
    for line in checked(observed['stdout']).read_bytes().splitlines():
        try:v=parse(line)
        except(UnicodeDecodeError,ValueError):continue
        if type(v)is dict and v.get('result')==report_ref:printed.append(v)
    need(len(printed)==1 and printed[0]['NPU']is False and printed[0]['model_ready']is False,'actual completed cold CLI emitted exactly this report')
    for name in('sourceio.py','g1_contract.py','g2_contract.py'):need((m['files'][name]['bytes'],m['files'][name]['sha256'])==(originals[name]['bytes'],originals[name]['sha256']),'whole original cold reader support unchanged '+name)
    # Import no controller or accelerator: compile only the exact old functions.
    def function(r,name,scope):
        tree=ast.parse(checked(r).read_bytes());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name==name];need(len(nodes)==1,'one original reader function '+name);exec(compile(ast.Module(body=nodes,type_ignores=[]),r['path']+'#unchanged-original-readback','exec'),scope);return scope[name]
    ch=function(originals['g2_channel.py'],'contract',dict(need=need,Path=Path,G2=mods.g2_contract))
    first=ch(mods.sourceio,proof['failed_source'],stage['channel'])
    own=function(originals['g2_finalize.py'],'owned_channel',dict(CH=NS(contract=ch),C=mods.sourceio,Path=Path,json=json))
    second=own(old,proof['failed_source'],stage['channel']);need(first==second==obj(stage['channel']),'independent CPU reexecutes original CH.contract and full owned_channel on whole copied metadata')
    mods.g2_handoff.verify_saved_probe(mods.sourceio,sr,stage_ref,guest=False)
    return dict(stage_ref=stage_ref,report_ref=report_ref,child_ref=observed['record'],stdout_ref=observed['stdout'],stderr_ref=observed['stderr'],original_function_sources=originals,all_four_originals_unmounted_in_actual_guest=True,source_bound_guest_absence_check_completed=True,original_CH_contract_and_owned_channel_reexecuted=True,actual_live_identity_qualified=False,saved_snapshots_only=True,total_actual_copy_bytes=stage['total_copy_bytes'])


def execute(sr,result_ref,unit_ref):
    need(RESULT is not None and UNIT_REF is not None,"actual successful source13 MODEL result/unit pins pending; stage-only reader never qualifies")
    need(result_ref==RESULT and unit_ref==UNIT_REF,"only exact actual fully pinned MODEL result and unit")
    m,mods,complete,commands,clock,snapshot=source_gate(sr);sr=mods.sourceio.ref(sr['path'])
    need(result_ref==RESULT,'exact actual pinned MODEL output RESULT, never CPU/previous/caller-rewritten result')
    result=obj(result_ref);need(result['schema']=='bole.actual-three-node-model-owned/v131'and result['source']==sr and result['cpu_only']is False and result['primary']is None and result['secondary']==[]and result['source_before']and result['source_before']==result['source_after']==complete and result['phase_seconds']==3600 and result['cleanup_seconds']==180 and finite(result['cleanup_spent'])and 0<=result['cleanup_spent']<=180 and finite(result['elapsed'])and 0<=result['elapsed']<=3600 and result['model_ready']is False and result['timing_is_formal']is False and result['formal_performance']is False and result['task_accuracy']is False and result['actual_host_argv']==commands['model'][3:],'actual clean source-owned MODEL owner and exact command; this proof consumes only its two CPU stages')
    summary=result['summary'];model_extra_roles=model_summary(summary)
    declared=m['g2_callee_contract_v10']['original025_sources'];c=module(declared['model_contract'],'_g2_independent_original025_readback_facade');need(not hasattr(c,'need')and callable(c.require),'actual whole original025 facade, never a fake need module')
    validator=safety_validator(m,mods,c);v8=obj(V8_SOURCE);parent_alias=Path(v8['output_root'])/'cpu-preflight'
    first,first_owned,_=owner_chain(m,sr,CPU_OUT/'cpu-preflight',summary['CPU_release'],c,validator,parent_alias,mods)
    old=obj(m['g2_metadata_handoff_v8']['failed_source']);second,second_owned,before=owner_chain(m,sr,CPU_OUT/'candidate',summary['handoff_cold_release'],c,validator,Path(old['stream_channel_root']),mods)
    need(first['cid']!=second['cid']and first['formal_deadline_monotonic']==second['formal_deadline_monotonic'],'distinct sequential CPU owners share one actual cold-main original phase deadline')
    admission_ref,admission,args=software_args(sr,first['formal_deadline_monotonic']);outer=child(summary['actual_software_child'],c,first['cid'],args,CPU_OUT/'cpu-preflight','SOFTWARE');sw=software(sr,m,mods,outer,c,admission_ref,admission)
    cpu_report_ref=summary['CPU_report'];need(cpu_report_ref['path']==str(CPU_OUT/'cpu-preflight/CPU.json'),'actual current native parser report');cpu=obj(cpu_report_ref)
    need(cpu['source']==sr and cpu['pass_preflight']is True and cpu['Devices']==[]and cpu['native_runtime_parser_checked']is True and cpu['registry_arch_enumerated']is True and cpu['NPU']is False and cpu['torch_NPU_initialized']is False and cpu['weights_loaded']is False and cpu['registry_class_imported']is False and cpu['model_config_constructed']is False and cpu['full_engine_config_constructed']is False and cpu['actual_speculative_config']==m['native_speculative_config']and cpu['actual_cache_memory_config']==m['cache_memory_config'],'actual current-source device-free native runtime parser')
    parser_child=child(summary['CPU_child'],c,first['cid'],[str(ROOT/'preflight114.py'),'--execute','--source-ref',json.dumps(sr),'--output',str(CPU_OUT/'cpu-preflight/CPU.json')],CPU_OUT/'cpu-preflight','CPU')
    cold=cold_gate(sr,m,mods,summary,c,second_owned,before)
    unit=unit_gate(unit_ref)
    for r in list(READS.values()):checked(r)
    # Reopen the exact original source/command closure after all evidence reads.
    source_after={r['path']:r['sha256']for r in[*mods.bind_model.readset(mods.sourceio.ref(sr['path'])),*m['dependencies'],*mods.command_contract.validate(mods.sourceio,mods.sourceio.ref(sr['path']),m)]};need(source_after==complete,'complete nonempty source/command input closure remained unchanged during readback')
    need(not any(n=='torch'or n.startswith(('torch.','torch_npu','acl','numpy'))for n in sys.modules),'stdlib-only independent reader, no ML/accelerator import')
    return dict(schema='bole.actual-G2-v13-MODEL-stage-independent-readback/v1',source=sr,result_ref=result_ref,sameimage_349_parser_and_actual_cold_handoff_stage_pass=True,two_stage_CPU_helpers_stopped_retained=True,software=sw,native_parser=dict(report_ref=cpu_report_ref,child_ref=parser_child['record'],stdout_ref=parser_child['stdout'],stderr_ref=parser_child['stderr']),cold_handoff=cold,finite_unit_ref=unit_ref,finite_unit=unit,CPU_owners=[first,second],stage_only=True,unconsumed_model_summary_roles=model_extra_roles,model_summary_host_ref=MODEL_CONTEXT_HOST_REF,source_nonempty_before_after_equal=True,source_readset_count=len(complete),firstentry_clock=clock,shared_actual_cleanup_deadline_monotonic=first['formal_deadline_monotonic'],actual_elapsed=result['elapsed'],actual_cleanup_spent=result['cleanup_spent'],CPU_source_snapshot=snapshot,independent_readback_refs=list(READS.values()),reader_ref=ref(__file__),stdlib_only=True,actual_live_identity_qualified=False,model_ready=False,numerical_model_qualification=False,formal_success=False,NPU=False)





def write_exclusive(path,value):
    path=Path(path);need(path.is_absolute()and path==Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/G2_V13_MODEL_STAGE_READBACK.json')and path.parent.is_dir()and not any(p.is_symlink()for p in(path,*path.parents))and not path.exists()and not any(path.is_relative_to(x)for x in(ROOT,OUT,CPU_OUT,Path(V10_SOURCE['path']).parent,Path(V9_SOURCE['path']).parent,Path(V8_SOURCE['path']).parent)),'exact new ordinary qualification output; never overwrite source/evidence')
    data=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode();fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb')as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return ref(path)




def unit_gate(unit_ref):
    need(UNIT_REF is not None and unit_ref==UNIT_REF,'exact actual source13 MODEL finite-unit terminal Ref; no caller boolean')
    value=obj(unit_ref)
    need(set(value)=={'schema','observed_epoch','properties'} and value['schema']=='bole.actual-finite-unit-terminal/v1' and finite(value['observed_epoch']) and value['observed_epoch']>0,'actual full finite-unit terminal object')
    wanted=dict(Id='bole-g2-v13-model-20261020t154710z.service',Type='exec',Restart='no',MainPID='0',ControlPID='0',Result='success',ExecMainStatus='0',ActiveState='active',SubState='exited')
    need(value['properties']==wanted,'actual exact MODEL unit success, no remaining Main/Control PID, no restart')
    return value



def model_summary(summary):
    need(type(summary)is dict and all(type(k)is str for k in summary),'actual source-owned MODEL summary object')
    need(set(summary)==set(MODEL_SUMMARY_KEYS),'complete twenty successful source13 roles; no failure-only or unknown role')
    return sorted(set(summary)-set(STAGE_SUMMARY_KEYS))

def review(sr,owner_ref):
    need(RESULT is not None and UNIT_REF is not None,'actual successful source13 MODEL/unit pins are pending')
    need(owner_ref==RESULT and owner_ref['path']==str(OUT/'RESULT.json'),'only fully pinned actual source13 MODEL owner')
    reader_before=ref(__file__);proof=execute(sr,owner_ref,UNIT_REF)
    need(proof['schema']=='bole.actual-G2-v13-MODEL-stage-independent-readback/v1'and proof['source']==SOURCE and proof['result_ref']==owner_ref and proof['numerical_model_qualification']is False,'MODEL-parent two-CPU-stage proof only')
    need(ref(__file__)==reader_before==proof['reader_ref'],'whole stage reader source remained unchanged')
    evidence={reader_before['path']:reader_before}
    for r in READS.values():need(r['path']not in evidence or evidence[r['path']]==r,'no conflicting actual stage evidence');evidence[r['path']]=r
    evidence_refs=list(evidence.values())
    for r in evidence_refs:checked(r)
    proof['reader_source_before_after_equal']=True;proof['full_evidence_refs']=evidence_refs
    return proof,evidence_refs

def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--result-ref');p.add_argument('--unit-terminal-ref');p.add_argument('--output');p.add_argument('--stdout-only',action='store_true');a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    need(a.source_ref and a.result_ref and a.unit_terminal_ref and (a.stdout_only != bool(a.output)),'actual full source/MODEL/unit refs and exactly one output mode required')
    sr=parse(a.source_ref);owner_ref=parse(a.result_ref);unit_ref=parse(a.unit_terminal_ref);checked(sr);checked(owner_ref);checked(unit_ref)
    need(UNIT_REF is not None and unit_ref==UNIT_REF,'actual fully pinned MODEL unit terminal required')
    proof,evidence_refs=review(sr,owner_ref)
    if a.stdout_only:print(json.dumps(proof,sort_keys=True));return 0
    r=write_exclusive(a.output,proof);print(json.dumps(dict(schema='bole.actual-G2-v13-MODEL-stage-readback-execution/v1',qualification_ref=r,source=proof['source'],result_ref=owner_ref,finite_unit_ref=UNIT_REF,stage_only=True,numerical_model_qualification=False,model_ready=False,NPU=False)));return 0





if __name__=='__main__':raise SystemExit(main())

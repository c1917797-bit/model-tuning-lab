"""Pure exact-source renderers for one reviewed ON boundary diagnostic child.

No file write, import of model code, owner creation, or device operation.
The caller supplies helper hashes only after independent MAIN review.
"""
import ast
import hashlib
import json

WORKSTREAM = '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z'
PARENT_ROOT = WORKSTREAM + '/bole_performance_profile_prepare_20261021/successor_layer/bound-short-ON-v2'
PARENT_REF = dict(path=PARENT_ROOT + '/SOURCE_BOUND.json', bytes=1503149,
    sha256='a285ac43d953cf257255ec4848d8719b613010bf339491e2a39d20d2f3b73b8f')
OLD_SHORT_DELTA_REF = dict(path=PARENT_ROOT + '/short_binding_delta.py', bytes=1851,
    sha256='4406fdeaff1965c2c3ce2adf859b1969bd29c102344c1f51204da037b81470d9')
OLD_VALIDATOR_REF = dict(path=PARENT_ROOT + '/performance_validate.py', bytes=6933,
    sha256='c45e114ab03fd35a47c85c8dd6f70bb71bbc406fa08be151222d082d8d57d824')
OLD_SOFTWARE_COORDINATOR_REF = dict(path=PARENT_ROOT + '/performance_software_stages.py',
    bytes=5440, sha256='b862faa3ac7763c34af4055e48fef2c3d1140eea023e10de71d73770d13f05cd')
CHILD_ROOT = "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-reduction-OFF-v5_20261022T200000Z"
CHILD_OUTPUT = "/opt/host/vnf/austinov/run-bole-reduction-OFF-v5_20261022T200000Z"
CHILD_BATCH = "MAIN-BOLE-REDUCTION-20261022T200000Z-OFF-V5"
CHILD_AUTHORITY_SCOPE = "OFF only; two bounded eight-token text-only requests; complete projection pre/post-reduce raw diagnostic; no performance admission"
PREPARATION_ROOT = "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/reduction_probe_prepare_v5_20261022T200000Z/OFF"
# Actual locally frozen authorization bytes; remote deployment is still pending.
AUTHORIZATION_REF = {"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/reduction_probe_prepare_v5_20261022T200000Z/OFF/AUTHORIZATION_CONTINUATION.json","bytes":1923,"sha256":"1b1f8f19d1c78aa3b2d90c8fec586f388da1ae6096b98d9a53f47dc9764b47f4"}
AUTHORIZATION_DOCUMENT_REF = {"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/reduction_probe_prepare_v5_20261022T200000Z/OFF/AUTHORIZATION_CONTINUATION.md","bytes":1362,"sha256":"0d8f69b4d7035ad162a613e1019b3db9ce869d66d077c19dbab2e96b9fca9a12"}
START_EPOCH = 1792689000
CUTOFF_EPOCH = 1792710600
CUTOFF_ISO = '2026-10-22T23:10:00+00:00'
OLD_REPORT_CUTOFF = 1792672721
PHASE_SECONDS = 3600
CLEANUP_SECONDS = 180
ORIGINAL_VALIDATOR_AUTHORITY_GATE = " C.need(authority['schema']=='bole.short-state-authority/v1' and authority['start_epoch']==1792586321 and authority['cutoff_epoch']==1792672721 and authority['phase_seconds']==3600 and authority['cleanup_seconds']==180,'explicit new user24h authority; fixed phase cleanup')\n"
CONTINUATION_VALIDATOR_AUTHORITY_GATE = " C.need(authority['schema']=='bole.short-state-authority/v1' and authority['start_epoch']==1792689000 and authority['cutoff_epoch']==1792710600 and authority['phase_seconds']==3600 and authority['cleanup_seconds']==180,'explicit user continuation; finite new batch with fixed phase cleanup')\n"
OLD_RUNTIME = ('service_runner.py', 'live_owner.py', 'bole_performance_profile.py',
    'performance_service_client.py', 'host_service.py', 'performance_host.py', 'command_contract.py')
EXTRA_RUNTIME = ('prefill_tail.py', 'model_process_calibration.py', 'g3_budget.py')
RUNTIME = OLD_RUNTIME + EXTRA_RUNTIME
REVIEWED_HELPERS = ('boundary_probe_v1.py', 'boundary_delta.py',
                    'boundary_integration.py', 'boundary_validation.py', 'projection_probe_v1.py', 'projection_raw_v1.py')
FLAG = 'BOLE_NATIVE_BOUNDARY_PROBE_ENABLE'
MANIFEST_FIELDS = ('boundary_parent_source', 'boundary_probe_profile',
                   'boundary_reviewed_helpers', 'boundary_control_refs', 'projection_probe_profile',
                   'text_only_config', 'text_only_preparation_evidence')
TEXT_ONLY_CONFIG = dict(language_model_only=True, skip_mm_profiling=False,
                        enable_mm_embeds=False, limit_mm_per_prompt={})
TEXT_ONLY_PREPARATION_EVIDENCE = {'failed_startup_result': {'path': '/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z/RESULT.json', 'bytes': 2375646, 'sha256': '4ad705377892c1136dbc945c8353904739e6189ed4b52dea2df3cc12731ef1da'}, 'actual_cpu_parser_caller': {'bytes': 5282, 'path': '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-boundary-ON-v3-continuation_20261022T120055Z/preflight114.py', 'sha256': '0207b0a4f628be6e5c460cc54868d0daf1f12fdf8dbe61f3dd02b9d85901fcf6'}, 'native_source_receipts': [{'path': '/opt/host/vnf/austinov/run-bole-startup-native-source-read-v1-20261022T134900Z/READ.json', 'bytes': 12036, 'sha256': '12496fb8365271f6cf04255cc27bac305d4bcf297f8d8e842798169b2ab605bb'}, {'path': '/opt/host/vnf/austinov/run-bole-textonly-source-and-failure-read-v1-20261022T171200Z/READ.json', 'bytes': 80593, 'sha256': '3a57d8026278b31c11083773469f3fe754ce033d6e5b380528d0e1a180be91c3'}], 'native_source_snapshots': {'/vllm-workspace/vllm/vllm/v1/worker/gpu_model_runner.py': {'path': '/opt/host/vnf/austinov/run-bole-startup-native-source-read-v1-20261022T134900Z/0_gpu_model_runner.py', 'bytes': 334736, 'sha256': '6250ca0670c4593aa2f7c4567c9c71d6cb3d8182624a985d4d4e33d5bf054666'}, '/vllm-workspace/vllm/vllm/model_executor/models/qwen3_vl.py': {'path': '/opt/host/vnf/austinov/run-bole-startup-native-source-read-v1-20261022T134900Z/1_qwen3_vl.py', 'bytes': 111366, 'sha256': '2935e09be47a893f09176cddb1beb6ed2e73666459de2bfbb08aca50b3e08969'}, '/vllm-workspace/vllm/vllm/config/multimodal.py': {'path': '/opt/host/vnf/austinov/run-bole-startup-native-source-read-v1-20261022T134900Z/2_multimodal.py', 'bytes': 13957, 'sha256': '2ca78ef40f8bdae73ef26af648b6384c1ece4108d1fcfda27cd00e60c013ca14'}, '/vllm-workspace/vllm/vllm/engine/arg_utils.py': {'path': '/opt/host/vnf/austinov/run-bole-startup-native-source-read-v1-20261022T134900Z/3_arg_utils.py', 'bytes': 111675, 'sha256': '3ade2488897d08b5c1fd4ddb815eb5743169907d59741a47867185caab7f250d'}, '/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py': {'path': '/opt/host/vnf/austinov/run-bole-startup-native-source-read-v1-20261022T134900Z/4_model_runner_v1.py', 'bytes': 258160, 'sha256': '94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968'}, '/vllm-workspace/vllm-ascend/vllm_ascend/worker/worker.py': {'path': '/opt/host/vnf/austinov/run-bole-startup-native-source-read-v1-20261022T134900Z/5_worker.py', 'bytes': 48290, 'sha256': 'c392da56095b255d47fe5ad7ffdfbedd269fe69851690e89a8d2ed44c073f6c3'}, '/vllm-workspace/vllm/vllm/multimodal/encoder_budget.py': {'bytes': 7111, 'path': '/opt/host/vnf/austinov/run-bole-textonly-source-and-failure-read-v1-20261022T171200Z/0_encoder_budget.py', 'sha256': '76aaf25bb8755f7232c5f89cd15173a2bb08d8cdaaaa10797199a49448a5b49b'}, '/vllm-workspace/vllm/vllm/multimodal/registry.py': {'bytes': 12967, 'path': '/opt/host/vnf/austinov/run-bole-textonly-source-and-failure-read-v1-20261022T171200Z/1_registry.py', 'sha256': 'd4627c89d3459ce35a729e0940a0c5be5b54793b40192c1c068416b57a0a82fd'}, '/vllm-workspace/vllm/vllm/model_executor/models/qwen3_5.py': {'bytes': 29662, 'path': '/opt/host/vnf/austinov/run-bole-textonly-source-and-failure-read-v1-20261022T171200Z/2_qwen3_5.py', 'sha256': '04f3de5372973770d71c5c05f2e8a5e221ec52b62cca7a1e302d9201b61b8adc'}, '/vllm-workspace/vllm/vllm/model_executor/models/interfaces.py': {'bytes': 52512, 'path': '/opt/host/vnf/austinov/run-bole-textonly-source-and-failure-read-v1-20261022T171200Z/3_interfaces.py', 'sha256': '62ae344c350b8445f364bded9cf5a0a3887caae062873d266487aedfd55e3dd7'}, '/vllm-workspace/vllm/vllm/model_executor/models/utils.py': {'bytes': 30902, 'path': '/opt/host/vnf/austinov/run-bole-textonly-source-and-failure-read-v1-20261022T171200Z/4_utils.py', 'sha256': '5c4b438be5dee3478b1a1445cb9ec2cfa6362992bd7290bde7113b43cb57e880'}, '/vllm-workspace/vllm/vllm/config/model.py': {'bytes': 91921, 'path': '/opt/host/vnf/austinov/run-bole-textonly-source-and-failure-read-v1-20261022T171200Z/5_model.py', 'sha256': 'cf5aeb9e16d6cac82426cf7e8d140741b35c503ae8b9e1fc9ba3dde53c585a62'}}}
TEXT_ONLY_CONTROL_CONTRACT_REF = dict(path=PARENT_ROOT+'/contract090.py', bytes=4301,
    sha256='15cef57335428e4c0419bc10f0dbab4c43d9ec1d563e4cbc6fda18f436a8394c')


def need(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('utf-8')


def pinned_text(text, reference):
    need(type(text) is str, 'source text must be an exact decoded string')
    data = text.encode('utf-8')
    need(len(data) == reference['bytes'] and hashlib.sha256(data).hexdigest() == reference['sha256'],
         'exact actual old ON source bytes: ' + reference['path'])
    return text


def once(text, before, after):
    need(text.count(before) == 1, 'one exact source fragment: ' + before[:72])
    return text.replace(before, after, 1)


ARM = 'OFF'


def expected_profile(parent):
    value = dict(parent['short_state_digest_profile'], observation=ARM)
    return value


def expected_observation_profile(C, parent):
    return C.obj(parent['short_parent_source'])['observation_only_profile']


def check_continuation_payload(value):
    """Check the fixed recorded authority; callers also check both whole Refs."""
    require_frozen_inputs()
    expected = dict(schema='bole.explicit-continuation-authorization/v1',
        authority_kind='explicit_user_continuation', user_statement='可以继续穿刺一直到成功',
        document=AUTHORIZATION_DOCUMENT_REF, old_window_extended=False,
        old_hard_report_deadline_utc='2026-10-22T12:38:41+00:00',
        internal_batch_start_epoch=START_EPOCH, internal_batch_cutoff_epoch=CUTOFF_EPOCH,
        internal_batch_cutoff_utc=CUTOFF_ISO, internal_batch_limit_seconds=21600,
        internal_limit_is_not_user_promised_result_window=True,
        phase_seconds=PHASE_SECONDS, cleanup_seconds=CLEANUP_SECONDS,
        whole_prepare_admission_seconds=3780, batch_id=CHILD_BATCH,
        model_path='/cache/efim/Qwen3.6-27B', physical_npus=[4, 5, 6, 7],
        protected_physical_npus=[0, 1, 2, 3], tensor_parallel_size=4,
        scope=CHILD_AUTHORITY_SCOPE, source_root=CHILD_ROOT, output_root=CHILD_OUTPUT,
        numerical_thresholds_unchanged=True, formal_performance_admitted=False,
        resource_owner_created=False, source_frozen=False)
    need(type(value) is dict and all(type(value.get(k)) is type(v) and value[k] == v
                                   for k, v in expected.items()),
         'exact explicit continuation, independent finite batch, unchanged limits and protected devices')
    return value


def continuation_authority(old_authority, old_authority_ref):
    """New ticket only; the exact original ticket remains an immutable input."""
    need(type(old_authority) is dict and old_authority['schema'] == 'bole.short-state-authority/v1'
         and old_authority['start_epoch'] == 1792586321
         and old_authority['cutoff_epoch'] == OLD_REPORT_CUTOFF
         and old_authority['cutoff_iso'] == '2026-10-22T12:38:41+00:00'
         and old_authority['phase_seconds'] == PHASE_SECONDS
         and old_authority['cleanup_seconds'] == CLEANUP_SECONDS,
         'fixed original completed short authority and unchanged owner budgets')
    return dict(old_authority, batch_id=CHILD_BATCH, scope=CHILD_AUTHORITY_SCOPE,
        user_authorization_ref=AUTHORIZATION_REF, historical_authority_ref=old_authority_ref,
        start_epoch=START_EPOCH, cutoff_epoch=CUTOFF_EPOCH, cutoff_iso=CUTOFF_ISO)


def render_current_software_coordinator(old_text):
    """Only three literal cutoffs change in the whole pinned current coordinator."""
    text = pinned_text(old_text, OLD_SOFTWARE_COORDINATOR_REF)
    need(text.count('1792672721') == 3 and str(CUTOFF_EPOCH) not in text,
         'exact three original software cutoff operands')
    text = text.replace('1792672721', str(CUTOFF_EPOCH))
    need(text.replace(str(CUTOFF_EPOCH), '1792672721') == old_text,
         'exact inverse coordinator authority rebind; every other byte unchanged')
    ast.parse(text)
    return text


def normalize_reviewed_helpers(reviewed_helpers):
    need(type(reviewed_helpers) is dict and set(reviewed_helpers) == set(REVIEWED_HELPERS),
         'exact five independently reviewed diagnostic helper pins')
    result = {}
    for name in sorted(reviewed_helpers):
        pin = reviewed_helpers[name]
        need(type(pin) is dict and set(pin) == {'bytes', 'sha256'}
             and type(pin['bytes']) is int and 0 < pin['bytes'] <= 2**22
             and type(pin['sha256']) is str and len(pin['sha256']) == 64
             and all(char in '0123456789abcdef' for char in pin['sha256']),
             'typed complete reviewed helper pin: ' + name)
        result[name] = dict(bytes=pin['bytes'], sha256=pin['sha256'])
    return result


def render_short_delta(old_text):
    """Retain old runtime logic and compose exactly one reviewed boundary delta."""
    text = pinned_text(old_text, OLD_SHORT_DELTA_REF)
    text = once(text, 'import prepare_short_gate as P\n',
                'import prepare_short_gate as P\nimport boundary_delta\n')
    nodes = [node for node in ast.parse(text).body if isinstance(node, ast.Assign)
             and any(isinstance(target, ast.Name) and target.id == 'RUNTIME' for target in node.targets)]
    need(len(nodes) == 1 and ast.literal_eval(nodes[0].value) == OLD_RUNTIME,
         'exact original seven-file runtime declaration')
    text = once(text, ast.get_source_segment(text, nodes[0]), 'RUNTIME = ' + repr(RUNTIME))
    text = once(text, 'def runtime(old):\n',
                "def runtime(old):\n P.need(type(old) is dict and set(old)==set(RUNTIME),'complete boundary runtime input set')\n")
    text = once(text, ' return out\n',
                " out=boundary_delta.runtime(old,out)\n"
                " P.need(type(out) is dict and set(out)==set(RUNTIME),'complete boundary runtime output set')\n"
                ' return out\n')
    ast.parse(text)
    return text


def render_validator(old_text, reviewed_helpers):
    """Add exact helper pins/lineage and rebind one explicit authority predicate."""
    text = pinned_text(old_text, OLD_VALIDATOR_REF)
    reviewed = normalize_reviewed_helpers(reviewed_helpers)
    line = "SCHEMA='bole.performance-successor-source-validation/v1'\n"
    text = once(text, line, line + 'BOUNDARY_REVIEWED_FILES = ' + repr(reviewed) + '\n')
    line = " m=C.obj(sr);parent=C.obj(P.PIN);audit=C.obj(AUDIT);root=Path(m['root'])\n"
    text = once(text, line, line + ' import boundary_validation as BV\n'
                + ' BV.validate(C,sr,m,reviewed=BOUNDARY_REVIEWED_FILES)\n')
    text = once(text, ORIGINAL_VALIDATOR_AUTHORITY_GATE, CONTINUATION_VALIDATOR_AUTHORITY_GATE)
    line = " expected['contract090.py']=B.bind_outputs(C.checked(parent['files']['contract090.py']).read_text(),m['output_root'])\n"
    text = once(text, line, line + TEXT_ONLY_VALIDATOR_RENDER_LINE)
    ast.parse(text)
    return text


TEXT_ONLY_VALIDATOR_RENDER_LINE = " expected['contract090.py']=BV.I.render_text_only_contract(expected['contract090.py'])\n"


def complete_ref(reference, *, expected_path=None):
    need(type(reference) is dict and set(reference) == {'path', 'bytes', 'sha256'}
         and type(reference['path']) is str and reference['path'].startswith('/')
         and '/..' not in reference['path'] and '\\' not in reference['path']
         and type(reference['bytes']) is int and 0 < reference['bytes'] <= 32 * 2**20
         and type(reference['sha256']) is str and len(reference['sha256']) == 64
         and all(char in '0123456789abcdef' for char in reference['sha256'])
         and (expected_path is None or reference['path'] == expected_path),
         'frozen actual complete Ref, never an unbound placeholder')
    return reference


def text_only_input_refs():
    evidence = TEXT_ONLY_PREPARATION_EVIDENCE
    return [evidence['failed_startup_result'], evidence['actual_cpu_parser_caller'],
            *evidence['native_source_receipts'], *evidence['native_source_snapshots'].values()]


def require_frozen_inputs():
    complete_ref(AUTHORIZATION_REF, expected_path=PREPARATION_ROOT+'/AUTHORIZATION_CONTINUATION.json')
    complete_ref(AUTHORIZATION_DOCUMENT_REF, expected_path=PREPARATION_ROOT+'/AUTHORIZATION_CONTINUATION.md')
    need(type(TEXT_ONLY_PREPARATION_EVIDENCE) is dict and
         set(TEXT_ONLY_PREPARATION_EVIDENCE) == {'failed_startup_result', 'actual_cpu_parser_caller',
             'native_source_receipts', 'native_source_snapshots'} and
         type(TEXT_ONLY_PREPARATION_EVIDENCE['native_source_receipts']) is list and
         len(TEXT_ONLY_PREPARATION_EVIDENCE['native_source_receipts']) == 2 and
         type(TEXT_ONLY_PREPARATION_EVIDENCE['native_source_snapshots']) is dict and
         len(TEXT_ONLY_PREPARATION_EVIDENCE['native_source_snapshots']) == 12,
         'fixed failed-startup/native twelve-source preparation evidence')
    refs = text_only_input_refs()
    for reference in refs:
        complete_ref(reference)
    need(len({reference['path'] for reference in refs}) == len(refs),
         'unique complete text-only preparation evidence paths')
    return True


TEXT_ONLY_CONTRACT_FUNCTION = """


def text_only_config(argv,m,*,args=None,engine=None):
 expected=dict(language_model_only=True,skip_mm_profiling=False,enable_mm_embeds=False,limit_mm_per_prompt={})
 value=m.get('text_only_config')
 need(type(value)is dict and set(value)==set(expected) and all(type(value[key])is type(wanted) and value[key]==wanted for key,wanted in expected.items()),'one explicit common text-only configuration')
 if argv is not None:
  need(type(argv)is list and all(type(token)is str for token in argv) and argv.count('--language-model-only')==1,'one actual bare native language-model-only option')
  forbidden=('--no-language-model-only','--skip-mm-profiling','--no-skip-mm-profiling','--enable-mm-embeds','--no-enable-mm-embeds','--limit-mm-per-prompt')
  need(not any(token==flag or token.startswith(flag+'=') or token.startswith(flag+'.') for token in argv for flag in forbidden) and not any(token.startswith('--language-model-only=') or token.startswith('--language-model-only.') for token in argv),'no skip-profiling, embedding, or modality-limit override')
 for actual in(args,engine):
  if actual is not None:
   need(all(hasattr(actual,key) for key in expected),'actual parser and EngineArgs expose every native text-only field')
   need(all(type(getattr(actual,key))is type(wanted) and getattr(actual,key)==wanted for key,wanted in expected.items()),'actual parser and EngineArgs match source text-only fields')
 return expected
"""

TEXT_ONLY_CONTRACT_DELTAS = (
    (" need(m['cache_memory_config']==dict(gpu_memory_utilization=0.8,kv_cache_memory_bytes=None,num_gpu_blocks_override=None),'one common utilization-only memory profile')\n",
     " need(m['cache_memory_config']==dict(gpu_memory_utilization=0.8,kv_cache_memory_bytes=None,num_gpu_blocks_override=None),'one common utilization-only memory profile')\n text_only_config(None,m)\n"),
    (' return explicit_lazy_argv(args)\n',
     " forbidden=('--language-model-only','--no-language-model-only','--skip-mm-profiling','--no-skip-mm-profiling','--enable-mm-embeds','--no-enable-mm-embeds','--limit-mm-per-prompt')\n"
     " need(not any(token==flag or token.startswith(flag+'=') or token.startswith(flag+'.') for token in args for flag in forbidden),'no pre-existing native text-only or MM override')\n"
     " args+=['--language-model-only']\n"
     ' return explicit_lazy_argv(args)\n'),
    (' return expected\n', ' text_only_config(argv,m,args=args,engine=engine)\n return expected\n'),
)


def reverse_text_only_contract(text):
    text = once(text, TEXT_ONLY_CONTRACT_FUNCTION, '')
    for before, after in reversed(TEXT_ONLY_CONTRACT_DELTAS):
        text = once(text, after, before)
    ast.parse(text)
    return text


def render_text_only_contract(old_text):
    """Only one native argv flag plus manifest/actual parser joins; no model imports."""
    need(type(old_text) is str and 'def text_only_config(' not in old_text,
         'one original unmodified command contract, never an already rendered source')
    text = old_text
    for before, after in TEXT_ONLY_CONTRACT_DELTAS:
        text = once(text, before, after)
    text += TEXT_ONLY_CONTRACT_FUNCTION
    ast.parse(text)
    need(reverse_text_only_contract(text) == old_text,
         'whole original command and memory profile restored by exact inverse')
    return text

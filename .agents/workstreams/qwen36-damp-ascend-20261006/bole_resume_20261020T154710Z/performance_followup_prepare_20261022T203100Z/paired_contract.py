"""Pure paired source checks. Never runtime admission or a replacement numerical gate."""
from pathlib import PurePosixPath
import copy
import json

COMMON_FIELDS=('checkpoint_config_ref','checkpoint_index_ref','installed_sources','runtime_sources',
 'cache_memory_config','common','performance_profile','performance_client_contract',
 'native_speculative_config','stream_resource_profile','component_refs','actual118c','authority_ref',
 'followup_authority_ref','followup_source_schema','followup_preparation_root')
COMMON_ENV={'HCCL_DETERMINISTIC':'true'}


def need(v,s):
    if not v:raise ValueError(s)


def refshape(r):
    return type(r)is dict and set(r)=={'path','bytes','sha256'} and type(r['path'])is str and PurePosixPath(r['path']).is_absolute() and type(r['bytes'])is int and r['bytes']>=0 and type(r['sha256'])is str and len(r['sha256'])==64


def pair(bole,ar):
    need(bole['performance_arm']=='bole' and ar['performance_arm']=='native_ar','genuine two distinct arms')
    for m in(bole,ar):
        need(m['prepared_only']is True and m['default_enabled']is False and
             m['performance_ready']is False and m['numerical_qualified']is False,
             'preparation remains defaultOFF/unqualified, never fake source freeze')
        need(m['paired_common_environment']==COMMON_ENV,'preregistered identical deterministic HCCL, not model qualification')
        need(m['common']==dict(HF32=False,async_scheduling=False,eager=True,
             mamba_cache_mode='none',prefix_cache=False,profiling=False),'common eager/HF32/prefix/profiler route')
        scope=m['performance_profile']['scope']
        need(scope['input_tokens']==131 and scope['output_tokens']==1024 and scope['concurrency']==1 and
             scope['warmup_requests']==scope['measured_requests']==1 and
             scope['diagnostic_tensor_export']is False and scope['independent_cpu_ack']is False,
             'same fixed1024 complete warmup/measured workload')
        need('prepared_template'not in m and 'SOURCE_BOUND.json'not in m['files'],
             'no manufactured bound receipt/template')
        need(all(refshape(r) and PurePosixPath(r['path'])==PurePosixPath(m['root'])/n
             for n,r in m['files'].items()),'all virtual source identities actually bound to that arm root')
    for k in COMMON_FIELDS:need(bole.get(k)==ar.get(k),'identical common field '+k)
    need(bole['root']!=ar['root'] and bole['output_root']!=ar['output_root'],'distinct nonoverwriting arms')
    need(bole['validated_performance_profile']['enabled']is True and
         'validated_performance_profile'not in ar and 'observation_only_profile'not in ar and
         bole['observation_only_profile']['enabled']is True,'candidate only BOLE policy; AR no observer-policy impostor')
    need(bole['effective_speculative_config']==dict(method='mtp',num_speculative_tokens=8) and
         ar['effective_speculative_config']is None,'genuine native AR has no speculation')
    return dict(schema='bole.prepared-AR-candidate-pair-check/v1',prepared_only=True,
        source_shape_checked=True,performance_ready=False,numerical_qualified=False,
        common_environment=COMMON_ENV,gate_required='real model correctness with this same policy')

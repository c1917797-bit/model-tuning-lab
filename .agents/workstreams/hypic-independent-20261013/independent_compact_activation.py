"""Atomic opt-in assembly of independent compact HYPIC hooks."""
from contextlib import ExitStack
from pathlib import Path
import hashlib,inspect


def install_owned_chain(installers):
    resources=ExitStack()
    try:
        for install in installers:resources.callback(install())
    except BaseException:
        resources.close();raise
    return resources.close


def verify_model_source(cls):
    from vllm.model_executor.models.qwen3_5 import Qwen3_5Model
    from vllm.model_executor.models import qwen3_next
    if cls is not Qwen3_5Model:
        raise ValueError('selected official Qwen3_5Model identity required')
    paths=((Path(inspect.getfile(cls)),'04f3de5372973770d71c5c05f2e8a5e221ec52b62cca7a1e302d9201b61b8adc'),
           (Path(qwen3_next.__file__),'8d614ce262ab9340585f9a2ad4ab117228f076e3672fcb5f04930ff0a38223ae'))
    for path,expected in paths:
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise ValueError('official hybrid model source drift')


def c2_install_route(config):
    config=dict(config)
    layer_barrier=config.pop("c2_layer_completion_barrier",False)
    finite_gate=config.pop("c2_layer_finite_gate",False)
    block_snapshot=config.pop("c2_block_table_snapshot",False)
    if type(block_snapshot)is not bool or block_snapshot and not layer_barrier:
        raise ValueError("C2 block-table snapshot requires explicit layer barrier")
    if type(finite_gate)is not bool or finite_gate and not layer_barrier:
        raise ValueError("C2 finite gate requires explicit layer barrier")
    if type(layer_barrier) is not bool:
        raise ValueError("explicit C2 layer barrier boolean required")
    if layer_barrier:
        from experimental_c2_layer_barrier import install_compact_c2
    else:
        from independent_compact_c2_hook import install_compact_c2
    if finite_gate or block_snapshot:
        original_install=install_compact_c2
        def install_compact_c2(stage,*,enabled=False,emit=None):
            options={}
            if finite_gate:options["finite_gate"]=True
            if block_snapshot:options["block_table_snapshot"]=True
            return original_install(stage,enabled=enabled,emit=emit,**options)
    install_compact_c2.c2_layer_finite_gate=finite_gate
    install_compact_c2.c2_block_table_snapshot=block_snapshot
    return config,install_compact_c2,layer_barrier

def c1_install_route(config):
    config=dict(config)
    native_batch=config.pop('native_decode_batch',False)
    if type(native_batch) is not bool:raise ValueError('explicit native decode batch boolean required')
    completion=config.pop('c1_layer_completion_barrier',False)
    shadow=config.pop('c1_layer_shadow_validation',False)
    packed=config.pop('c1_packed_wave',False)
    partitioned=config.pop('c1_partitioned_render',False)
    lazy_initial=config.pop('c1_lazy_initial_snapshot',False)
    if type(lazy_initial)is not bool or lazy_initial and not packed:
        raise ValueError('lazy initial snapshot requires explicit packed C1')
    if type(partitioned)is not bool or partitioned and not packed:
        raise ValueError('partitioned render requires explicit packed C1')
    performance=config.pop('c1_performance_mode',False)
    prefix_policy=config.pop('c1_short_prefix_terminal_policy','chunk64')
    short_suffix=config.pop('c1_short_suffix_recurrent',False)
    if type(short_suffix)is not bool or short_suffix and (not packed or prefix_policy!='canonical_recurrent_le64'):
        raise ValueError('short suffix recurrence requires packed C1 and canonical prefix policy')
    if prefix_policy not in ('chunk64','canonical_recurrent_le64') or prefix_policy!='chunk64' and not packed:
        raise ValueError('canonical short prefix requires explicit packed C1')
    probe=config.pop('c1_first_divergence',False)
    head_policy=config.pop('c1_first_divergence_head_policy','head0')
    if head_policy not in ('head0','max_state_residual') or head_policy!='head0' and not probe:
        raise ValueError('residual head policy requires explicit diagnostic probe')
    if type(probe)is not bool or probe and not packed:
        raise ValueError('explicit diagnostic stage switch requires packed C1')
    if type(packed) is not bool:raise ValueError('explicit packed C1 boolean required')
    from independent_c1_execution_mode import validate_c1_mode
    validate_c1_mode(packed=packed,native=native_batch,completion=completion,
                     shadow=shadow,probe=probe,performance=performance)
    if type(completion) is not bool or type(shadow) is not bool:
        raise ValueError('explicit C1 completion/shadow booleans required')
    if shadow and not completion:raise ValueError('C1 shadow requires completion treatment')
    from independent_compact_gdn_hook import install_compact_gdn
    def install(stage,*,enabled=False,emit=None):
        return install_compact_gdn(stage,enabled=enabled,emit=emit,native_decode_batch=native_batch,
            layer_completion=completion,layer_shadow=shadow,packed_wave=packed,
            first_divergence=probe,first_divergence_head_policy=head_policy,
            short_prefix_policy=prefix_policy,performance_mode=performance,
            partitioned_render=partitioned,lazy_initial_snapshot=lazy_initial,
            short_suffix_recurrent=short_suffix)
    install.c1_layer_completion_barrier=completion
    install.c1_layer_shadow_validation=shadow
    install.c1_packed_wave=packed
    install.c1_partitioned_render=partitioned
    install.c1_lazy_initial_snapshot=lazy_initial
    install.c1_short_suffix_recurrent=short_suffix
    install.c1_performance_mode=performance
    install.c1_short_prefix_terminal_policy=prefix_policy
    install.c1_first_divergence=probe
    install.c1_first_divergence_head_policy=head_policy
    return config,install,native_batch

def snapshot_install_route(config):
    config=dict(config)
    enabled=config.pop("prefill_prompt_snapshot",False)
    if type(enabled)is not bool:
        raise ValueError("explicit prefill prompt snapshot boolean required")
    return config,enabled

def metadata_snapshot_install_route(config):
    config=dict(config)
    enabled=config.pop("forward_metadata_snapshot",False)
    if type(enabled)is not bool:
        raise ValueError("explicit forward metadata snapshot boolean required")
    return config,enabled

def activate_compact_hypic(config,*,enabled=False,emit=None,request_progress_limit=128):
    if not enabled:return lambda:None
    if not callable(emit):raise ValueError('activation evidence sink required')
    config,prefill_prompt_snapshot=snapshot_install_route(config)
    config,forward_metadata_snapshot=metadata_snapshot_install_route(config)
    c2_block_table_diagnostic=config.pop("c2_block_table_diagnostic",False)
    if type(c2_block_table_diagnostic)is not bool:
        raise ValueError("explicit C2 block-table diagnostic boolean required")
    snapshot_probe_batches=config.pop("prompt_snapshot_probe_batches",0)
    if (type(snapshot_probe_batches)is not int or not 0<=snapshot_probe_batches<=2
            or snapshot_probe_batches and not prefill_prompt_snapshot):
        raise ValueError("explicit bounded snapshot probe requires enabled snapshot treatment")
    config,install_compact_c2,layer_barrier=c2_install_route(config)
    c2_block_table_snapshot=install_compact_c2.c2_block_table_snapshot
    if c2_block_table_snapshot:
        from independent_c2_block_table_snapshot import verify_c2_snapshot_runtime_contract
        verify_c2_snapshot_runtime_contract()
    config,install_compact_gdn,native_batch=c1_install_route(config)
    # Official ops registration precedes runtime imports; never patch source files.
    import vllm_ascend.ops
    from vllm.model_executor.models.qwen3_5 import Qwen3_5Model
    from independent_compact_stage import CompactCanonicalStage
    from independent_compact_runtime_snapshot import activate_compact_runner
    from independent_compact_model_hook import install_compact_model
    if "public_segments" in config:
        from independent_catalog_stage import CatalogCompactStage
        stage=CatalogCompactStage(**config)
    else:stage=CompactCanonicalStage(**config)
    from independent_runner_context import CURRENT_REQUEST_SLICES
    from independent_linear_material_pool import identity_key
    def transferred(identity,generation,metrics):
        requests=CURRENT_REQUEST_SLICES.get()
        if (not requests or {r.rank for r in requests}!={identity.rank}
                or len({r.step for r in requests})!=1):
            raise ValueError('material transfer audit request/rank/step context required')
        emit({'event':'c1_private_material_transfer_verified','rank':identity.rank,
            'step':requests[0].step,'request_ids':[r.request_id for r in requests],
            'layer':identity.layer,'generation':generation,
            'tokens_sha256':identity.tokens_sha256,'metrics':metrics,
            'full_transfer_bytes_compared':True,'actual_slot_commit':'not_started'})
    stage.compact_store.on_transfer_verified=transferred
    def evicted(pool,event):
        requests=CURRENT_REQUEST_SLICES.get()
        if not requests or len({r.rank for r in requests})!=1:
            raise ValueError("eviction worker rank context required")
        emit(dict(event,event="compact_public_material_evicted",pool=pool,rank=requests[0].rank))
    stage.compact_store.pool.on_eviction=lambda event:evicted("linear",event)
    stage.compact_kv_store.on_eviction=lambda event:evicted("kv",event)
    def publish(material):
        generation=stage.publish(material)
        emit({'event':'compact_public_state_published','rank':material.identity.rank,
              'key':identity_key(material.identity),'pool':'linear',
              'layer':material.identity.layer,'generation':generation,
              'tokens_sha256':material.identity.tokens_sha256,
              'transition_shape':list(material.affine.transition.shape),
              'zero_state_shape':list(material.affine.zero_state.shape)})
    runner_options={}
    if c2_block_table_snapshot or c2_block_table_diagnostic:
        runner_options["record_attention_groups"]=True
    model_options={"metadata_snapshot":forward_metadata_snapshot}
    if c2_block_table_snapshot:model_options["c2_block_table_snapshot"]=True
    stop=install_owned_chain((
        lambda:activate_compact_runner(enabled=True,allow_mixed=stage.enable_mixed,emit=emit,
                                      request_limit=request_progress_limit,
                                      prefill_prompt_snapshot=prefill_prompt_snapshot,
                                      prompt_snapshot_probe_batches=snapshot_probe_batches,
                                      **runner_options),
        lambda:stage.install_producer(enabled=True,publish=publish),
        lambda:install_compact_gdn(stage,enabled=True,emit=emit),
        lambda:install_compact_c2(stage,enabled=True,emit=emit),
        lambda:install_compact_model(Qwen3_5Model,enabled=True,
            verify_source=verify_model_source,select=stage.select_compact,emit=emit,
            **model_options)))
    try:
        import os
        emit({'event':'compact_hypic_hooks_installed','pid':os.getpid(),
              'default_disabled':True,'c2_layer_completion_barrier':layer_barrier,
              'c2_layer_finite_gate':install_compact_c2.c2_layer_finite_gate,
              'c2_block_table_snapshot':c2_block_table_snapshot,
              'c2_block_table_diagnostic':c2_block_table_diagnostic,
              'native_decode_batch':native_batch,
              'c1_async_material_transfer':stage.compact_store.async_material_transfer,
              'c1_async_material_verify':stage.compact_store.verify_async_transfer,
              'prefill_prompt_snapshot':prefill_prompt_snapshot,
              'forward_metadata_snapshot':forward_metadata_snapshot,
              'prompt_snapshot_probe_batches':snapshot_probe_batches,
              'c1_layer_completion_barrier':install_compact_gdn.c1_layer_completion_barrier,
              'c1_layer_shadow_validation':install_compact_gdn.c1_layer_shadow_validation,
              'c1_packed_wave':install_compact_gdn.c1_packed_wave,
              'c1_partitioned_render':install_compact_gdn.c1_partitioned_render,
              'c1_lazy_initial_snapshot':install_compact_gdn.c1_lazy_initial_snapshot,
              'c1_short_suffix_recurrent':install_compact_gdn.c1_short_suffix_recurrent,
              'c1_performance_mode':install_compact_gdn.c1_performance_mode,
              'c1_first_divergence':install_compact_gdn.c1_first_divergence,
              'c1_short_prefix_terminal_policy':install_compact_gdn.c1_short_prefix_terminal_policy,
              'c1_first_divergence_head_policy':install_compact_gdn.c1_first_divergence_head_policy,
              'scope':'installation; real request proof pending'})
    except BaseException:
        stop();raise
    return stop

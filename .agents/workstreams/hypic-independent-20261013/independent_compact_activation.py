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
    if type(layer_barrier) is not bool:
        raise ValueError("explicit C2 layer barrier boolean required")
    if layer_barrier:
        from experimental_c2_layer_barrier import install_compact_c2
    else:
        from independent_compact_c2_hook import install_compact_c2
    return config,install_compact_c2,layer_barrier

def c1_install_route(config):
    config=dict(config)
    native_batch=config.pop('native_decode_batch',False)
    if type(native_batch) is not bool:raise ValueError('explicit native decode batch boolean required')
    completion=config.pop('c1_layer_completion_barrier',False)
    shadow=config.pop('c1_layer_shadow_validation',False)
    packed=config.pop('c1_packed_wave',False)
    probe=config.pop('c1_first_divergence',False)
    head_policy=config.pop('c1_first_divergence_head_policy','head0')
    if head_policy not in ('head0','max_state_residual') or head_policy!='head0' and not probe:
        raise ValueError('residual head policy requires explicit diagnostic probe')
    if type(probe)is not bool or probe and not packed:
        raise ValueError('explicit diagnostic stage switch requires packed C1')
    if type(packed) is not bool:raise ValueError('explicit packed C1 boolean required')
    if packed and not (native_batch and completion and shadow):
        raise ValueError('packed C1 canary requires native1 batch, completion and shadow')
    if type(completion) is not bool or type(shadow) is not bool:
        raise ValueError('explicit C1 completion/shadow booleans required')
    if shadow and not completion:raise ValueError('C1 shadow requires completion treatment')
    from independent_compact_gdn_hook import install_compact_gdn
    def install(stage,*,enabled=False,emit=None):
        return install_compact_gdn(stage,enabled=enabled,emit=emit,native_decode_batch=native_batch,
            layer_completion=completion,layer_shadow=shadow,packed_wave=packed,
            first_divergence=probe,first_divergence_head_policy=head_policy)
    install.c1_layer_completion_barrier=completion
    install.c1_layer_shadow_validation=shadow
    install.c1_packed_wave=packed
    install.c1_first_divergence=probe
    install.c1_first_divergence_head_policy=head_policy
    return config,install,native_batch

def activate_compact_hypic(config,*,enabled=False,emit=None,request_progress_limit=128):
    if not enabled:return lambda:None
    if not callable(emit):raise ValueError('activation evidence sink required')
    config,install_compact_c2,layer_barrier=c2_install_route(config)
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
    stop=install_owned_chain((
        lambda:activate_compact_runner(enabled=True,allow_mixed=stage.enable_mixed,emit=emit,
                                      request_limit=request_progress_limit),
        lambda:stage.install_producer(enabled=True,publish=publish),
        lambda:install_compact_gdn(stage,enabled=True,emit=emit),
        lambda:install_compact_c2(stage,enabled=True,emit=emit),
        lambda:install_compact_model(Qwen3_5Model,enabled=True,
            verify_source=verify_model_source,select=stage.select_compact,emit=emit)))
    try:
        import os
        emit({'event':'compact_hypic_hooks_installed','pid':os.getpid(),
              'default_disabled':True,'c2_layer_completion_barrier':layer_barrier,
              'native_decode_batch':native_batch,
              'c1_layer_completion_barrier':install_compact_gdn.c1_layer_completion_barrier,
              'c1_layer_shadow_validation':install_compact_gdn.c1_layer_shadow_validation,
              'c1_packed_wave':install_compact_gdn.c1_packed_wave,
              'c1_first_divergence':install_compact_gdn.c1_first_divergence,
              'c1_first_divergence_head_policy':install_compact_gdn.c1_first_divergence_head_policy,
              'scope':'installation; real request proof pending'})
    except BaseException:
        stop();raise
    return stop

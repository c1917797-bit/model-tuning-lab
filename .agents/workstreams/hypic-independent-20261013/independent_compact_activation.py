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


def activate_compact_hypic(config,*,enabled=False,emit=None):
    if not enabled:return lambda:None
    if not callable(emit):raise ValueError('activation evidence sink required')
    # Official ops registration precedes runtime imports; never patch source files.
    import vllm_ascend.ops
    from vllm.model_executor.models.qwen3_5 import Qwen3_5Model
    from independent_compact_stage import CompactCanonicalStage
    from independent_compact_runtime_snapshot import activate_compact_runner
    from independent_compact_gdn_hook import install_compact_gdn
    from independent_compact_c2_hook import install_compact_c2
    from independent_compact_model_hook import install_compact_model
    stage=CompactCanonicalStage(**config)
    def publish(material):
        generation=stage.publish(material)
        emit({'event':'compact_public_state_published','rank':material.identity.rank,
              'layer':material.identity.layer,'generation':generation,
              'tokens_sha256':material.identity.tokens_sha256,
              'transition_shape':list(material.affine.transition.shape),
              'zero_state_shape':list(material.affine.zero_state.shape)})
    stop=install_owned_chain((
        lambda:activate_compact_runner(enabled=True,allow_mixed=stage.enable_mixed,emit=emit),
        lambda:stage.install_producer(enabled=True,publish=publish),
        lambda:install_compact_gdn(stage,enabled=True,emit=emit),
        lambda:install_compact_c2(stage,enabled=True,emit=emit),
        lambda:install_compact_model(Qwen3_5Model,enabled=True,
            verify_source=verify_model_source,select=stage.select_compact,emit=emit)))
    try:
        import os
        emit({'event':'compact_hypic_hooks_installed','pid':os.getpid(),
              'default_disabled':True,'scope':'installation; real request proof pending'})
    except BaseException:
        stop();raise
    return stop

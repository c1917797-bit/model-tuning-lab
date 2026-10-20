"""Canonical vocabulary rows using the ACTUAL native proposer convention.

The installed greedy_sample offsets local indices by rank*V_local when
enable_reduce_sample is true. Never mistake a local shard for a global tree.
"""
import inspect
from model_entry import need


def canonical(torch,C,proposer_module,group,local,*,proposer_ref,vocab_size):
 need(C.ref(inspect.getsourcefile(proposer_module))==proposer_ref,
      'actual installed proposer globals, not guessed sampling convention')
 need(not proposer_module.lmhead_tp_enable(),'separate LM-head TP geometry is outside first smoke scope')
 need(local.ndim==2 and local.dtype==torch.float32 and
      type(vocab_size)is int and vocab_size>0 and bool(torch.isfinite(local).all()),
      'raw finite FP32 native vocabulary logits before sampler')
 reduced=proposer_module.get_ascend_config().enable_reduce_sample
 need(type(reduced)is bool,'actual native reduce-sampling policy')
 if reduced:
  need(group.world_size==4 and local.shape[1]*4>=vocab_size,
       'actual four uniform local-vocabulary shards')
  value=group.all_gather(local,dim=-1)
  need(value.shape==(local.shape[0],local.shape[1]*4),'native rank-major vocabulary assembly')
  value=value[:,:vocab_size]
 else:
  need(local.shape[1]==vocab_size,'native ordinary full vocabulary, not unknown sharded logits')
  value=local
 need(bool(torch.isfinite(value).all()),'finite actual global vocabulary')
 return value

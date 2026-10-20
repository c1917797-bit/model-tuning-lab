"""Observe the genuine native MTP first pass; never synthesize draft logits.

This hook is not a scheduler or a BOLE admission certificate. The original
proposer and original compute_logits execute unmodified. A receiver may use
the captured root and two children only after joining target cache ownership.
"""
import functools, inspect, os, types
from model_entry import need, code_source, patched_source


def install(proposer, torch, C, *, proposer_ref, mtp_ref, receive,
            receiver_ref,canonical_logits=None,patch_ref=None):
    if os.environ.get('BOLE_MTP_TREE_CAPTURE_ENABLE') != '1':
        return None
    need(proposer.method == 'mtp', 'actual native MTP method, not EAGLE alias')
    old = proposer._propose
    model = proposer.model
    if patch_ref is not None:
        patched_source(C,model.model.forward,patch_ref,'mtp')
    logits_old = model.compute_logits
    code_source(C, old, proposer_ref)
    code_source(C, logits_old, mtp_ref)
    code_source(C, receive, receiver_ref)
    if canonical_logits is not None:code_source(C,canonical_logits,receiver_ref)
    signature = inspect.signature(old)
    need('next_token_ids' in signature.parameters and
         'target_hidden_states' in signature.parameters,
         'source-proved genuine proposer input ABI')
    active = None
    had_propose = '_propose' in proposer.__dict__
    prior_propose = proposer.__dict__.get('_propose')
    had_logits = 'compute_logits' in model.__dict__
    prior_logits = model.__dict__.get('compute_logits')

    @functools.wraps(logits_old)
    def logits(this, *args, **kwargs):
        value = logits_old(*args, **kwargs)
        if active is not None and not active['calls']:
            need(value.ndim == 2 and value.shape[0] == 1 and
                 value.shape[1] >= 2, 'actual first MTP C1 vocabulary logits')
            need(bool(torch.isfinite(value).all().item()),
                 'finite actual logits before greedy sampler sanitization')
            # Clone before later draft iterations reuse their buffers.
            active['first_local_logits'] = value.detach().clone()
            active['first_logits'] = (value if canonical_logits is None else canonical_logits(value)).detach().clone()
            active['first_hidden'] = args[0].detach().clone()
        if active is not None:
            active['calls'].append(tuple(value.shape))
        return value

    @functools.wraps(old)
    def propose(this, *args, **kwargs):
        nonlocal active
        need(active is None, 'non-reentrant native draft capture')
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        root = bound.arguments['next_token_ids']
        need(root.ndim == 1 and root.numel() == 1,
             'actual C1 target-selected next root')
        record = dict(calls=[], root=root.detach().clone(),
                      target_positions=bound.arguments['target_positions'].detach().clone(),
                      target_token_ids=bound.arguments['target_token_ids'].detach().clone(),
                      target_hidden_states=bound.arguments['target_hidden_states'].detach().clone(),
                      common_attn_metadata=bound.arguments['common_attn_metadata'],
                      scheduler_output=bound.arguments.get('scheduler_output'),
                      model_ready=False, accepted_path_published=False,
                      proposer_source=proposer_ref, mtp_source=mtp_ref)
        active = record
        try:
            result = old(*args, **kwargs)
            need(record['calls'], 'original actual MTP forward reached logits')
            record['children'] = torch.topk(record['first_logits'], 2, dim=-1).indices.detach().clone()
            record['native_draft_result'] = result.detach().clone()
        finally:
            active = None
        # Opaque metadata is deliberately not serializable evidence. Receiver
        # must join these actual objects to source-bound runner cache bindings.
        receive(proposer=proposer, record=record)
        return result

    model.compute_logits = types.MethodType(logits, model)
    proposer._propose = types.MethodType(propose, proposer)

    def restore():
        need(active is None and proposer._propose.__func__ is propose and
             model.compute_logits.__func__ is logits, 'actual installed hook ownership')
        if had_propose: proposer._propose = prior_propose
        else: delattr(proposer, '_propose')
        if had_logits: model.compute_logits = prior_logits
        else: delattr(model, 'compute_logits')
    return restore

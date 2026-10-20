"""ADVISORY PROPOSAL: two actual sequential C1/131 BOLE requests.

Root must review, source-bind, package and qualify this file before any device
admission.  This file creates no controller, process, device or HTTP client.
It never certifies model/task/performance readiness.
"""
import functools
import inspect
import os
import traceback
import types
from types import SimpleNamespace

import model_entry as E
import worker_entry as W
import cache_registry as R
import prefill_tail as T
import diagnostic_export as X
import service_bridge as SB
import eligibility
import transaction
import core112
import adapter
import treeconv118
import tree_metadata111
import predecessor118t
import component_gate
import registration118
import native_logits
import native_dtype131r13 as ND
import context_identity
from live_owner import LiveOwner
import g1_contract as G1
from model_process_calibration import ProcessCalibration


def _snap(t, bridge, owner):
    bridge._validate_bindings(owner)
    gdn, fa = [], []
    for b in bridge.bindings:
        if b['kind'] == 'gdn':
            slot = bridge._physical_slot(b, owner)
            E.need('conv_arena' in b, 'actual registered wide convolution arena')
            gdn.append(dict(layer=b['index'], group=b['group'], physical_slot=slot,
                slot_binding_identity=b['slot_binding'].identity(),
                native_state=b['state'][slot].detach().clone(),
                full_conv_slot=b['conv_arena'][slot:slot+1].detach().clone()))
        else:
            pages = tuple(b['table'][:(owner.length+2+127)//128])
            ix = t.tensor(pages, dtype=t.long, device=b['key'].device)
            fa.append(dict(layer=b['index'], physical_pages=pages,
                ownership=bridge._bole_live.fa_proof(b),
                key=b['key'].index_select(0, ix).detach().clone(),
                value=b['value'].index_select(0, ix).detach().clone()))
    return gdn, fa


def _verify_published(t, bridge, proposal):
    for row in proposal['writes']:
        arena = row['arena']
        if row['kind'] in ('state', 'conv'):
            actual = arena[row['slot']]
        else:
            ix = row['indices']
            actual = arena[ix//128, ix%128]
        E.need(E.tensor_id(arena) == row['arena_identity'] and
            bridge.N.bits(t, actual, row['after']),
            'native bookkeeping/MTP retained actual selected target cache bytes')


def _ctx(ctx, bridge):
    captures = {}
    for layer, row in ctx.captures.items():
        # The selected actual K.commit output is already in staged state.after.
        # Keeping all three full states would needlessly triple capture bytes.
        cap = {k: v for k, v in row.items() if k != 'actual_node_states'}
        if cap['kind'] == 'gdn':
            binding = bridge.bindings[layer]
            E.need(binding['layer'].linear_attn.conv1d.bias is None,
                'actual native conv bias absent for unchanged literal oracle')
            cap['conv_bias_is_none'] = True
        captures[layer] = cap
    return dict(owner=ctx.owner, tokens=ctx.tokens, positions=ctx.positions,
        mode=ctx.mode, captures=captures, order=ctx.order, phase=ctx.phase,
        first_fault=ctx.first_fault, secondary_faults=ctx.secondary_faults)


def _metadata(cad):
    result = {}
    for key in ('query_start_loc', 'query_start_loc_cpu', 'seq_lens',
                'seq_lens_cpu', '_seq_lens_cpu', 'slot_mapping'):
        value = getattr(cad, key, None)
        result[key] = None if value is None else value.detach().clone()
    return result


def _patch(obj, name, fn, restorers):
    had = name in obj.__dict__
    prior = obj.__dict__.get(name)
    setattr(obj, name, types.MethodType(fn, obj))
    def restore():
        E.need(getattr(obj, name).__func__ is fn,
            'owned actual service method before restore ' + name)
        if had:
            setattr(obj, name, prior)
        else:
            delattr(obj, name)
    restorers.append(restore)


def _native_method(C, obj, name, ref):
    fn = getattr(obj, name)
    body = getattr(fn, '__func__', None)
    E.need(body is not None and name not in obj.__dict__ and
        body is getattr(type(obj), name), 'unchanged actual native class method ' + name)
    E.code_source(C, body, ref)
    return fn


def _native_samples(C, runner, refs):
    """Pin the actual torch.inference_mode wrapper and its original method."""
    import torch
    method = runner.sample_tokens
    body = getattr(method, '__func__', None)
    E.need(body is not None and 'sample_tokens' not in runner.__dict__ and
        body is type(runner).__dict__['sample_tokens'],
        'actual installed native class sample_tokens wrapper')
    E.code_source(C, body, refs['torch_contextlib'])
    original = getattr(body, '__wrapped__', None)
    E.need(original is not None, 'actual inference-mode original method')
    E.code_source(C, original, refs['runner'])
    closure = inspect.getclosurevars(body).nonlocals
    E.need(closure.get('func') is original and callable(closure.get('ctx_factory')),
        'actual native torch wrapper closes over that same original method')
    factory = closure['ctx_factory']
    E.code_source(C, factory, refs['torch_grad_mode'])
    context = getattr(factory, '__self__', None)
    E.need(type(context) is torch.inference_mode and context.mode is True and
        C.ref(inspect.getsourcefile(type(context))) == refs['torch_grad_mode'],
        'actual torch inference_mode context factory')
    return method


def install(worker, torch, torch_npu, C, *, source_ref, component_refs,
            get_forward_context, get_attention_context, enter_context,
            native_get_tp_group, publish):
    m = C.obj(source_ref)
    refs = m['runtime_sources']
    own_ref = C.ref(__file__)
    E.need(own_ref == m['files']['service_runner.py'], 'exact frozen service runner')
    E.need(os.environ.get(G1.FLAG) == '1' and m['service_experiment'] == G1.SCOPE, 'explicit bounded service opt-in')
    for ref in m['files'].values():
        C.checked(ref)
    for ref in refs.values():
        C.checked(ref)
    for module in (SB, eligibility, transaction, X, ND, native_logits, R, T,
                   component_gate, registration118, core112, adapter,
                   treeconv118, tree_metadata111, predecessor118t, context_identity, G1):
        name = os.path.basename(module.__file__)
        E.need(C.ref(module.__file__) == m['files'][name], 'actual private module ' + name)
    context_identity.enter_source(C, enter_context, m['files']['context_adapter.py'], refs['contextlib'])
    E.code_source(C, publish, m['files']['worker_bootstrap.py'])
    group = native_get_tp_group()
    runner = worker.model_runner
    drafter = runner.drafter
    inner = worker._bole_model_objects['inner']
    outer = worker._bole_model_objects['outer']
    E.need(group.world_size == 4 and group.rank_in_group in range(4), 'actual native TP4')
    E.need(drafter is not None and drafter.runner is runner and drafter.method == 'mtp' and
        drafter.num_speculative_tokens == runner.num_spec_tokens == 8,
        'actual owned native eight-draft MTP configuration')
    E.need(not runner.use_async_scheduling and not runner.use_aux_hidden_state_outputs and
        not runner.use_cp and runner.pcp_size == runner.dcp_size == 1 and
        runner.cache_config.mamba_cache_mode == 'none' and
        not runner.speculative_config.disable_padded_drafter_batch and
        runner.model_config.enforce_eager is True and
        runner.parallel_config.pipeline_parallel_size == 1 and
        runner.parallel_config.data_parallel_size == 1,
        'synchronous eager noCP/noaux PP1/DP1 bounded native MTP scope')
    E.need('qwen3_5' in inner.config.model_type,
        'actual source-proved Qwen3.5 direct-position rotary route')
    E.need(not drafter.needs_extra_input_slots and not drafter.parallel_drafting,
        'ordinary native MTP first-pass input preparation')
    state = SimpleNamespace(prefill=None, bridge=None, live=None, completed=False,
        steps=[], active_mtp=None, initial_draft=None, initial_native_output=None,
        sampler_type=None, sampler_dtype=None, restorers=[], published=False,
        failed=False, policy_receipts=[], initial_target_head_hidden=None,
        initial_target_head_local_logits=None, request_restorers=[], completed_requests=[],
        strong_requests=[], request_capture_refs=[], generation=1)
    convabi_ref = C.obj(m['actual118c']['capture'])['actual_device_abi_ref']
    calibration = ProcessCalibration(worker=worker, model=inner, source_ref=source_ref,
        own=m, rank=group.rank_in_group, old_ref=convabi_ref)
    old_prepare = _native_method(C, runner, '_prepare_inputs', refs['runner'])
    old_sample = _native_method(C, runner, '_sample', refs['runner'])
    old_samples = _native_samples(C, runner, refs)
    old_propose = _native_method(C, runner, 'propose_draft_token_ids', refs['runner'])
    old_mtp = _native_method(C, drafter, '_propose', refs['proposer'])
    old_first = _native_method(C, drafter, 'set_inputs_first_pass', refs['proposer'])
    _native_method(C, drafter, 'prepare_inputs_padded', refs['proposer'])
    E.code_source(C, drafter._get_positions, refs['base_proposer'])
    E.patched_source(C, drafter.model.model.forward, refs['qwen_patch'], 'mtp')
    old_logits = drafter.model.compute_logits
    E.code_source(C, old_logits, refs['mtp'])
    native_proposer = inspect.getmodule(old_mtp.__func__)
    E.need(C.ref(inspect.getsourcefile(native_proposer)) == refs['proposer'],
        'actual native proposer module before owned hooks')
    old_update = runner._update_states
    E.code_source(C, old_update, m['files']['identity_capture.py'])
    E.need(getattr(old_update, '_actual_identity_capture', False) is True,
        'existing source-bound worker identity journal remains installed')
    underlying_update = inspect.getclosurevars(old_update.__func__).nonlocals.get('original')
    E.need(underlying_update is not None, 'actual journal preserves original native update')
    E.code_source(C, underlying_update, refs['runner'])
    compute_logits = W.actual_logits_head(C, outer, inner, refs['qwen35'])
    head = compute_logits.__self__
    old_head = head.compute_logits
    E.code_source(C, old_head, refs['qwen35'])
    vocab_size = W.actual_vocabulary(C, outer, inner, drafter,
        qwen35_ref=refs['qwen35'], mtp_ref=refs['mtp'])
    ND.validate_sources(C, m, head)
    ND.validate_sources(C, m, drafter.model)
    mtp_signature = inspect.signature(old_mtp)

    def canonical_logits(value):
        return native_logits.canonical(torch, C, native_proposer, group,
            ND.promote(torch, value), proposer_ref=refs['proposer'], vocab_size=vocab_size)

    def neutral_policy(request):
        from vllm.sampling_params import SamplingParams
        from vllm.v1.sample.metadata import SamplingMetadata
        from vllm.v1.worker.gpu_input_batch import CachedRequestState, InputBatch
        from vllm_ascend.worker.npu_input_batch import NPUInputBatch
        for cls, key in ((SamplingParams, 'sampling_params'), (SamplingMetadata, 'sampling_metadata'),
                         (CachedRequestState, 'gpu_input_batch'), (InputBatch, 'gpu_input_batch'),
                         (NPUInputBatch, 'npu_input_batch')):
            E.need(C.ref(inspect.getsourcefile(cls)) == refs[key], 'actual sampling class ' + key)
        E.need(InputBatch in NPUInputBatch.__mro__ and
            NPUInputBatch.no_thinking_budget is InputBatch.__dict__['no_thinking_budget'],
            'actual NPU batch inherits original source-proved thinking-budget property')
        E.code_source(C, InputBatch.__dict__['no_thinking_budget'].fget, refs['gpu_input_batch'])
        p = request.sampling_params
        s = runner.input_batch.sampling_metadata
        E.need(type(request) is CachedRequestState and type(p) is SamplingParams and
            type(s) is SamplingMetadata and type(runner.input_batch) is NPUInputBatch,
            'exact actual native request, parameter and metadata objects')
        expected = dict(n=1, temperature=0, top_p=1, min_p=0, repetition_penalty=1,
            frequency_penalty=0, presence_penalty=0, max_tokens=2, min_tokens=0, ignore_eos=True)
        E.need(all(getattr(p, k) == v for k, v in expected.items()) and p.top_k in (0, -1),
            'actual neutral greedy two-output G1 request policy')
        E.need(p.stop == [] and p.stop_token_ids == [] and p.bad_words == [] and
            p._bad_words_token_ids in (None, []) and all(getattr(p, k) is None for k in
            ('logprobs', 'prompt_logprobs', 'logprob_token_ids', 'structured_outputs',
             'logit_bias', 'allowed_token_ids', 'extra_args', 'thinking_token_budget',
             'repetition_detection')), 'no active request transform or early stopping path')
        E.need(runner.model_config.logits_processors in (None, [], ()) and
            s.all_greedy is True and s.all_random is False and s.no_penalties is True and
            s.temperature is None and s.top_p is None and s.top_k is None and
            s.max_num_logprobs is None and s.allowed_token_ids_mask is None and
            not s.bad_words_token_ids and s.logprob_token_ids is None and
            runner.input_batch.no_thinking_budget, 'actual neutral native batch metadata')
        state.policy_receipts.append(dict(expected, top_k=p.top_k,
            generated_before=len(request.output_token_ids), all_greedy=s.all_greedy,
            no_penalties=s.no_penalties, no_thinking_budget=runner.input_batch.no_thinking_budget))

    restore_tail = T.install_capture(worker, torch, C,
        get_forward_context=get_forward_context, gdn_ref=refs['gdn'], context_ref=refs['forward_context'])

    def after_prefill(**kw):
        if state.completed:
            return
        E.need(state.prefill is None and state.generation == len(state.completed_requests)+1 and
            state.generation in (1, 2), 'next monotonic actual G1 request registration')
        E.need(all(kw['request'] is not prior and kw['request_id'] != rid
            for rid, prior in state.strong_requests), 'distinct strongly retained native request per generation')
        state.strong_requests.append((kw['request_id'], kw['request']))
        ids, positions = kw['input_ids'], kw['positions']
        axes = positions.ndim
        E.need(ids.dtype == torch.int32 and tuple(ids.shape) == (131,), 'actual native 131-token input')
        expected = list(range(131)) if axes == 1 else [list(range(131))]*3
        E.need((axes == 1 or tuple(positions.shape) == (3, 131)) and
            positions.cpu().tolist() == expected, 'actual source text RoPE coordinates')
        import cache_observation
        import fa_prefill131r10
        import native_seams
        E.need(C.ref(cache_observation.__file__) == m['files']['cache_observation.py'] and
            C.ref(fa_prefill131r10.__file__) == m['files']['fa_prefill131r10.py'],
            'exact native cache observers')
        cache_ref = cache_observation.capture(C, source_ref, worker, inner, request_id=kw['request_id'],
            request=kw['request'], metadata=kw['metadata'], context=kw['forward_context'], rank=group.rank_in_group, request_epoch=state.generation)
        fa_ref = fa_prefill131r10.capture(C, source_ref, worker, inner, request_id=kw['request_id'],
            request=kw['request'], metadata=kw['metadata'], context=kw['forward_context'],
            rank=group.rank_in_group, length=131, request_epoch=state.generation)
        restore_tail()
        bindings, window = R.register(torch, C, worker, inner, request_id=kw['request_id'],
            request=kw['request'], metadata=kw['metadata'], forward_context=kw['forward_context'],
            get_attention_context=get_attention_context, refs=refs, length=131, request_epoch=state.generation)
        root_hidden = kw['hidden']
        E.need(isinstance(root_hidden, torch.Tensor) and tuple(root_hidden.shape) == (131, 5120),
            'actual no-aux target prefill final hidden')
        state.prefill = dict(window=window, bindings=bindings, context=kw['forward_context'],
            input_ids=ids.detach().clone(), positions=positions.detach().clone(),
            hidden=root_hidden.detach().clone(), axes=axes, native_input=kw['native_input'])
        convabi = C.obj(m['actual118c']['capture'])['actual_device_abi_ref']
        prerequisite = component_gate.consume(C, component_refs,
            gdn_math=C.ref(core112.__file__), paged_math=C.ref(adapter.__file__))
        bridge = E.Bridge(torch, C, inner, bindings, qwen_next_ref=refs['qwen_next'],
            gdn_ref=refs['gdn'], actual118c=m['actual118c'], conv_seam=native_seams,
            treeconv=treeconv118, tree_metadata=tree_metadata111, core112=core112,
            paged=adapter, torch_npu=torch_npu,
            actual_fia_abi=prerequisite['components']['paged']['actual_fia_abi'],
            actual_conv_abi=convabi, calibration_reader=predecessor118t,
            arm_verified=True, component_refs=component_refs, component_gate=component_gate,
            native_registration=registration118, own_source_ref=source_ref,
            position_axes=1 if axes == 1 else 3, prefill_window=window,
            actual_rank=group.rank_in_group, request_epoch=state.generation,
            calibration_handle=calibration, actual_worker=worker).install()
        owner = E.Owner(window['request_id'], state.generation, window['slot'], 131, 0)
        state.request_capture_refs = dict(cache_observation=cache_ref, fa_prefill=fa_ref,
            registration_audit=bridge.registration_audit_ref)
        state.calibration_acquire = bridge.calibration_acquire
        state.initial_slot_bindings = bridge._validate_bindings(owner)
        state.initial_prefill_GDN_observation = []
        for binding in bindings:
            if binding['kind'] == 'gdn':
                obj = binding['layer'].linear_attn
                obs = obj._bole_pure_prefill_observation
                E.need(obj.conv1d.bias is None, 'actual convolution bias absent')
                state.initial_prefill_GDN_observation.append(dict(layer=binding['index'],
                    raw_last3=obs['raw_last3'].detach().clone(),
                    extra_before=obs['extra_before'].detach().clone(),
                    native_gdn_source=obs['native_gdn_source'], conv_bias_is_none=True))
        state.bridge = bridge
        state.live = LiveOwner(runner, bindings, owner, max_steps=1)
        SB.install_methods(bridge, state.live, C, m)
        neutral_policy(state.live.request)
        # input_identity.capture must observe the untouched native LM head.
        # This callback runs after that real prefill check and before its head call.
        _patch(head, 'compute_logits', guard(target_head), state.request_restorers)

    restore_native_prefill = W.install_after_native_prefill(worker, C,
        qwen_next_ref=refs['qwen_next'], get_forward_context=get_forward_context,
        context_source_ref=refs['forward_context'], callback=after_prefill,
        callback_source_ref=own_ref, native_input_source_ref=source_ref, request_limit=2)
    old_inner = inner.forward
    E.code_source(C, old_inner, m['files']['worker_entry.py'])

    def prepare(this, scheduler_output, num_scheduled_tokens):
        result = old_prepare(scheduler_output, num_scheduled_tokens)
        if state.prefill is not None and not state.completed:
            f = state.live.make_frame(scheduler_output, num_scheduled_tokens)
            if state.live.acknowledgements:
                proof = state.live.acknowledgements[-1]
                if state.steps and state.steps[-1]['next_ack'] is None:
                    E.need(proof['previous_version'] == state.steps[-1]['owner']['version'],
                        'actual next native counter acknowledges immediately preceding publication')
                    state.steps[-1]['next_ack'] = dict(proof)
            f.request_output_tokens_before = tuple(state.live.request.output_token_ids)
            f.remaining_output = 2-len(f.request_output_tokens_before)
            E.need(f.remaining_output == 1, 'G1 remaining one output includes actual prefill root')
            f.native_schedule = dict(req_ids=runner.input_batch.req_ids.copy(),
                request_id=f.owner.request,
                computed_tokens=int(runner.input_batch.num_computed_tokens_cpu[0]),
                num_tokens_without_spec=int(runner.input_batch.num_tokens_no_spec[0]),
                scheduled_num_tokens=f.scheduled_nodes,
                scheduled_spec_tokens=list(scheduler_output.scheduled_spec_decode_tokens.get(f.owner.request, ())),
                CPU_input_token_ids=list(f.real_input_ids),
                request_output_tokens=list(state.live.request.output_token_ids))
            f.before_GDN, f.before_FA = _snap(torch, state.bridge, f.owner)
        return result

    def inner_forward(this, input_ids, positions, intermediate_tensors=None, inputs_embeds=None):
        if state.prefill is None or state.completed or state.live.frame is None:
            return old_inner(input_ids, positions, intermediate_tensors, inputs_embeds)
        return SB.forward(state.bridge, state.live.frame, old_inner, input_ids=input_ids,
            positions=positions, intermediate_tensors=intermediate_tensors, inputs_embeds=inputs_embeds,
            actual_context=get_forward_context(), enter_context=enter_context, source_ref=source_ref)

    def target_head(this, *args, **kwargs):
        value = old_head(*args, **kwargs)
        if state.prefill is not None and not state.completed:
            E.need(len(args) == 1 and not kwargs, 'actual native target head hidden operand ABI')
            f = state.live.frame
            if f is None:
                E.need(state.initial_target_head_hidden is None, 'single actual initial native target head call')
                state.initial_target_head_hidden = args[0].detach().clone()
                state.initial_target_head_local_logits = value.detach().clone()
            else:
                E.need(not hasattr(f, 'target_head_hidden'), 'single actual native target head call per frame')
                f.target_head_hidden = args[0].detach().clone()
                f.target_head_local_logits = value.detach().clone()
        return value

    def sample(this, logits, spec_decode_metadata):
        if state.prefill is None or state.completed:
            return old_sample(logits, spec_decode_metadata)
        neutral_policy(state.live.request)
        E.need(logits is not None and logits.ndim == 2, 'actual native target logits')
        local = logits.detach().clone()
        f = state.live.frame
        if f is None:
            E.need(state.initial_draft is None and state.sampler_type is None and logits.shape[0] == 1,
                'first actual neutral prefill sampler only')
            E.need(state.bridge.N.bits(torch, local, state.initial_target_head_local_logits) and
                state.bridge.N.bits(torch, state.initial_target_head_hidden, state.prefill['hidden'][-1:]),
                'actual native prefill head operand and sampler logits join')
            state.initial_root_local_logits = local
            state.initial_root_logits = canonical_logits(logits).detach().clone()
            result = old_sample(logits, spec_decode_metadata)
            from vllm.v1.outputs import SamplerOutput
            E.need(C.ref(inspect.getsourcefile(SamplerOutput)) == refs['outputs'] and
                type(result) is SamplerOutput and result.logprobs_tensors is None and
                result.sampled_token_ids.shape == (1, 1) and
                result.sampled_token_ids.dtype in (torch.int32, torch.int64),
                'actual installed native initial SamplerOutput ABI')
            state.sampler_type, state.sampler_dtype = type(result), result.sampled_token_ids.dtype
            return result
        E.need(state.bridge.N.bits(torch, local, f.target_head_local_logits) and
            state.bridge.N.bits(torch, f.target_head_hidden, f.tree_hidden[:f.scheduled_nodes]),
            'actual admitted target hidden-to-head-to-sampler operand chain')
        global_ = canonical_logits(logits).detach().clone()
        E.need(global_.shape[0] == f.scheduled_nodes, 'actual admitted target logits rows only')
        f.target_local_logits, f.target_logits = local, global_
        target_next = tuple(int(x) for x in global_.argmax(-1).cpu().tolist())
        decision = eligibility.decide(f.owner, f.tokens, target_next, f.scheduled_nodes,
            remaining_output_tokens=f.remaining_output)
        proposal = state.bridge.stage_selected_path(f.context, decision.terminal,
            current_owner=state.live.current)
        proposal['decision'] = decision
        publication = transaction.publish(torch, state.bridge, proposal, group=group,
            tokens=f.tokens, current_owner=state.live.current, scheduled_nodes=f.scheduled_nodes,
            target_next=target_next, remaining_output_tokens=f.remaining_output)
        f.proposal, f.publication, f.target_next = proposal, publication, target_next
        state.live.publication(publication)
        f.compaction_order = eligibility.native_compaction_order(f.scheduled_nodes, decision.terminal)
        output = torch.full((1, 9), -1, dtype=state.sampler_dtype, device=logits.device)
        output[0, :len(decision.emitted_tokens)] = torch.tensor(decision.emitted_tokens,
            dtype=state.sampler_dtype, device=logits.device)
        return state.sampler_type(sampled_token_ids=output, logprobs_tensors=None)

    def propose_drafts(this, *args, **kwargs):
        f = None if state.prefill is None or state.completed else state.live.frame
        if f is not None:
            n, order = f.scheduled_nodes, f.compaction_order
            E.need(tuple(runner.input_ids.gpu[:n].cpu().tolist()) == f.real_input_ids and
                state.bridge.N.bits(torch, f.native_hidden, f.tree_hidden[:n]),
                'actual original GPU target IDs and native hidden before compaction')
            f.proposal_gpu_ids_before = runner.input_ids.gpu[:n].detach().clone()
            ix = torch.tensor(order, dtype=torch.long, device=f.native_hidden.device)
            if order != tuple(range(n)):
                runner.input_ids.gpu[:n].copy_(f.proposal_gpu_ids_before.index_select(0, ix))
                f.native_hidden.copy_(f.tree_hidden[:n].index_select(0, ix))
            f.proposal_gpu_ids_after = runner.input_ids.gpu[:n].detach().clone()
        return old_propose(*args, **kwargs)

    def first_inputs(this, *args, **kwargs):
        result = old_first(*args, **kwargs)
        record = state.active_mtp
        if record is not None:
            num_tokens, indices, cad, _ = result
            E.need('first_pass_inputs' not in record, 'one actual native first-pass preparation')
            record['first_pass_inputs'] = dict(
                input_ids=drafter.input_ids[:num_tokens].detach().clone(),
                positions=drafter._get_positions(num_tokens).detach().clone(),
                hidden_states=drafter.hidden_states[:num_tokens].detach().clone(),
                token_indices_to_sample=indices.detach().clone(), metadata=_metadata(cad))
        return result

    def mtp_logits(this, *args, **kwargs):
        value = old_logits(*args, **kwargs)
        record = state.active_mtp
        if record is not None:
            E.need(not record['calls'] and value.ndim == 2 and value.shape[0] == 1 and
                bool(torch.isfinite(value).all()), 'one finite actual native first-MTP logits call')
            record['first_local_logits'] = value.detach().clone()
            record['first_logits'] = canonical_logits(value).detach().clone()
            record['first_hidden'] = args[0].detach().clone()
            record['calls'].append(tuple(value.shape))
        return value

    def mtp(this, *args, **kwargs):
        if state.prefill is None or state.completed:
            return old_mtp(*args, **kwargs)
        E.need(state.active_mtp is None and drafter.num_speculative_tokens == 8 and
            drafter.method == 'mtp' and not drafter.needs_extra_input_slots and not drafter.parallel_drafting,
            'owned ordinary native first-MTP preparation')
        bound = mtp_signature.bind(*args, **kwargs)
        bound.apply_defaults()
        a = bound.arguments
        root, cad = a['next_token_ids'], a['common_attn_metadata']
        E.need(root.ndim == 1 and root.numel() == 1, 'actual C1 native bonus/root into MTP')
        indices = a['token_indices_to_sample']
        if indices is None:
            indices = cad.query_start_loc[1:]-1
        rejected = a['num_rejected_tokens_gpu']
        record = dict(root=root.detach().clone(),
            target_token_ids=a['target_token_ids'].detach().clone(),
            target_positions=a['target_positions'].detach().clone(),
            target_hidden_states=a['target_hidden_states'].detach().clone(),
            token_indices_to_sample=indices.detach().clone(),
            query_start_loc=cad.query_start_loc.detach().clone(),
            num_rejected_tokens=None if rejected is None else rejected.detach().clone(),
            metadata=_metadata(cad), calls=[], proposer_source=refs['proposer'], mtp_source=refs['mtp'])
        state.active_mtp = record
        drafter.num_speculative_tokens = 1
        try:
            result = old_mtp(*args, **kwargs)
            E.need(len(record['calls']) == 1 and tuple(result.shape) == (1, 1),
                'original native MTP executed exactly one real first pass')
            record['native_result'] = result.detach().clone()
            children = torch.topk(record['first_logits'], 2, dim=-1).indices.detach().clone()
            record['children'] = children
            returned = [list(map(int, children[0].cpu().tolist()))]
            record['returned_drafts'] = returned
        finally:
            drafter.num_speculative_tokens = 8
            state.active_mtp = None
        root_id, child_ids = int(root.item()), tuple(returned[0])
        state.live.record_draft(root_id, child_ids)
        f = state.live.frame
        if f is None:
            E.need(state.initial_draft is None and
                root_id == int(state.initial_root_logits.argmax(-1).item()),
                'actual native prefill sampled root and genuine first MTP join')
            state.initial_draft = record
        else:
            E.need(root_id == f.publication['emitted_tokens'][-1],
                'actual native MTP uses selected published bonus')
            record['compaction_order'] = f.compaction_order
            f.next_mtp = record
        return returned

    def output_record(result):
        from vllm.v1.outputs import ModelRunnerOutput
        E.need(C.ref(inspect.getsourcefile(ModelRunnerOutput)) == refs['outputs'] and
            type(result) is ModelRunnerOutput and type(result.req_ids) is list and
            type(result.sampled_token_ids) is list, 'actual synchronous native ModelRunnerOutput')
        return dict(req_ids=list(result.req_ids),
            sampled_token_ids=[list(v) for v in result.sampled_token_ids],
            request_output_tokens_after=list(state.live.request.output_token_ids),
            num_tokens_no_spec_after=int(runner.input_batch.num_tokens_no_spec[0]),
            num_computed_tokens_cpu_after=int(runner.input_batch.num_computed_tokens_cpu[0]))

    def samples(this, grammar_output):
        active = state.prefill is not None and not state.completed
        E.need(not active or grammar_output is None, 'no grammar mutation before actual target sampling')
        f = None if not active else state.live.frame
        # First prefill registration fires inside execute_model before this method.
        result = old_samples(grammar_output)
        if not active:
            return result
        record = output_record(result)
        if f is None:
            E.need(state.initial_draft is not None and record['req_ids'] == [state.live.initial.request] and
                record['sampled_token_ids'] == [[int(state.initial_draft['root'].item())]],
                'actual initial ModelRunnerOutput hands off genuine prefill root')
            state.initial_native_output = record
            return result
        _verify_published(torch, state.bridge, f.proposal)
        f.after_GDN, f.after_FA = _snap(torch, state.bridge, f.owner)
        E.need(record['req_ids'] == [f.owner.request] and len(record['sampled_token_ids']) == 1,
            'actual one native request output')
        state.live.close_frame(record['req_ids'], record['sampled_token_ids'][0])
        step = dict(owner=f.owner, scheduled_nodes=f.scheduled_nodes,
            remaining_output=f.remaining_output, tokens=f.tokens, real_input_ids=f.real_input_ids,
            native_schedule=f.native_schedule, request_output_tokens_before=f.request_output_tokens_before,
            original_positions=f.original_positions, tree_positions=f.padded_positions,
            tree_context=_ctx(f.context, state.bridge), tree_hidden=f.tree_hidden,
            before_GDN=f.before_GDN, before_FA=f.before_FA, after_GDN=f.after_GDN, after_FA=f.after_FA,
            target_head_hidden=f.target_head_hidden, target_head_local_logits=f.target_head_local_logits,
            target_local_logits=f.target_local_logits, target_logits=f.target_logits, target_next=f.target_next,
            staged=X.export_staged(torch, f.proposal, cap_bytes=2**30)['payload'],
            publication=f.publication, native_output=record, next_mtp=f.next_mtp,
            proposal_gpu_ids_before=f.proposal_gpu_ids_before,
            proposal_gpu_ids_after=f.proposal_gpu_ids_after, next_ack=None)
        state.steps.append(X.export(torch, step, cap_bytes=2**30)['payload'])
        return result

    def freeze_request():
        for ref in m['files'].values():
            C.checked(ref)
        for ref in refs.values():
            C.checked(ref)
        p = state.prefill
        raw = dict(schema=G1.REQUEST_SCHEMA, source=source_ref,
            rank=group.rank_in_group, request=state.live.initial,
            request_capture_refs=state.request_capture_refs, calibration_acquire=state.calibration_acquire,
            actual_native_prefill_input=p['native_input'], actual_native_prefill_ids=p['input_ids'],
            actual_native_prefill_positions=p['positions'], actual_native_prefill_hidden=p['hidden'],
            initial_prefill_GDN_observation=state.initial_prefill_GDN_observation,
            same_model_conv_calibration=state.bridge.model_calibration_ref,
            layer_slot_bindings=state.initial_slot_bindings,
            native_logits_policy=dict(reduce_sample=native_proposer.get_ascend_config().enable_reduce_sample,
                lmhead_tp=False, vocab_size=vocab_size, proposer_source=refs['proposer']),
            initial_draft=state.initial_draft, initial_root_local_logits=state.initial_root_local_logits,
            initial_root_logits=state.initial_root_logits, initial_native_output=state.initial_native_output,
            initial_target_head_hidden=state.initial_target_head_hidden,
            initial_target_head_local_logits=state.initial_target_head_local_logits,
            policy_receipts=state.policy_receipts, steps=state.steps, retirement=state.retirement,
            source_after=dict(m['files']), runtime_sources_after=dict(refs), primary=None,
            scheduler_committed_independently=False, model_ready=False, task_ready=False,
            performance_ready=False, final_success=False)
        return X.export(torch, raw, cap_bytes=G1.CAP_BYTES)['payload']

    def freeze():
        E.need(len(state.completed_requests) == 2 and calibration.generations == [1, 2],
            'both distinct actual requests and original-calibration acquisitions')
        first, second = state.completed_requests
        def slots(raw):
            return tuple((b['layer'], b['group'], b['physical_slot'])
                for b in raw['steps'][0]['before_GDN'])
        def pages(raw):
            return tuple((b['layer'], tuple(b['physical_pages']))
                for b in raw['steps'][0]['before_FA'])
        reuse = dict(schema='bole.two-request-actual-slot-reuse/v1',
            generations=(first['request']['generation'], second['request']['generation']),
            requests=(first['request']['request'], second['request']['request']),
            GDN_before=(slots(first), slots(second)), FA_before=(pages(first), pages(second)),
            GDN_reused=slots(first) == slots(second), FA_reused=pages(first) == pages(second))
        raw = dict(schema=G1.RAW_SCHEMA, source=source_ref, rank=group.rank_in_group,
            requests=state.completed_requests, process_calibration=calibration.proofs,
            native_slot_reuse=reuse, source_after=dict(m['files']), runtime_sources_after=dict(refs),
            primary=None, scheduler_committed_independently=False, model_ready=False,
            task_ready=False, performance_ready=False, final_success=False)
        for ref in (*m['files'].values(), *refs.values()):
            C.checked(ref)
        payload = X.export(torch, raw, cap_bytes=G1.CAP_BYTES)
        E.need(payload['logical_tensor_bytes']+G1.RESERVE_BYTES <= G1.CAP_BYTES,
            'aggregate both actual requests plus calibration/all metadata within original1GiB')
        state.published = True  # Exclusive output must never be retried.
        return publish(source_ref=source_ref, rank=group.rank_in_group, payload=payload, primary=None)

    def update_states(this, scheduler_output):
        nonlocal restore_tail
        result = old_update(scheduler_output)
        if state.prefill is not None and not state.completed and state.live.initial.request in scheduler_output.finished_req_ids:
            state.retirement = state.live.retire(set(scheduler_output.finished_req_ids))
            E.need(len(state.steps) == 1 and len(state.live.request.output_token_ids) == 2,
                'actual owned G1 request completed exact two-token budget in one tree step')
            state.completed_requests.append(freeze_request())
            # These belong to one actual request. Process native runner/MTP and
            # after-prefill observers stay installed until the second retirement.
            for restore in reversed(state.request_restorers):
                restore()
            state.request_restorers = []
            state.bridge.restore()
            if len(state.completed_requests) == 2:
                for restore in reversed(state.restorers):
                    restore()
                restore_native_prefill()
                state.completed = True
                freeze()
            else:
                E.need(len(state.completed_requests) == 1 and state.generation == 1,
                    'only one G1 lifecycle transition before final restoration')
                restore_tail = T.install_capture(worker, torch, C,
                    get_forward_context=get_forward_context, gdn_ref=refs['gdn'],
                    context_ref=refs['forward_context'])
                state.generation = 2
                state.prefill = state.bridge = state.live = None
                state.steps = []
                state.active_mtp = state.initial_draft = state.initial_native_output = None
                state.sampler_type = state.sampler_dtype = None
                state.policy_receipts = []
                state.initial_target_head_hidden = state.initial_target_head_local_logits = None
                state.request_capture_refs = []
        return result

    def guard(fn):
        @functools.wraps(fn)
        def guarded(this, *args, **kwargs):
            try:
                return fn(this, *args, **kwargs)
            except BaseException as primary:
                if not state.failed:
                    state.failed = True
                    if not state.published:
                        failed = dict(schema='bole.actual-c1-two-request-service-first-fault/v1',
                            source=source_ref, rank=group.rank_in_group, primary=repr(primary),
                            traceback=traceback.format_exc(), generation=state.generation,
                            completed_requests=state.completed_requests, steps=state.steps,
                            initial_draft=state.initial_draft, scheduler_committed_independently=False,
                            model_ready=False, task_ready=False, performance_ready=False, final_success=False)
                        try:
                            frame = None if state.live is None else state.live.frame
                            failed['active_frame'] = None if frame is None else dict(
                                owner=frame.owner, tokens=frame.tokens,
                                real_input_ids=frame.real_input_ids,
                                scheduled_nodes=frame.scheduled_nodes,
                                context=None if not hasattr(frame, 'context') else
                                    _ctx(frame.context, state.bridge))
                            failed['active_mtp'] = state.active_mtp
                            payload = X.export(torch, failed, cap_bytes=2**30)
                            E.need(payload['logical_tensor_bytes']+G1.RESERVE_BYTES <= G1.CAP_BYTES,
                                'bounded first-fault evidence')
                            state.published = True
                            publish(source_ref=source_ref, rank=group.rank_in_group,
                                payload=payload, primary=repr(primary))
                        except BaseException as evidence_error:
                            # Preserve the original fault as the causal exception.
                            try:
                                primary.add_note('first-fault evidence export: '+repr(evidence_error))
                            except BaseException:
                                pass
                raise
        return guarded

    # Source checks and original bindings above all precede any patch.
    # Native update journal remains in the original chain and records removal
    # before our retirement callback publishes the separate bounded payload.
    for obj, name, fn in ((runner, '_prepare_inputs', prepare),
            (inner, 'forward', inner_forward),
            (runner, '_sample', sample), (runner, 'propose_draft_token_ids', propose_drafts),
            (drafter, 'set_inputs_first_pass', first_inputs),
            (drafter.model, 'compute_logits', mtp_logits), (drafter, '_propose', mtp),
            (runner, 'sample_tokens', samples), (runner, '_update_states', update_states)):
        _patch(obj, name, guard(fn), state.restorers)
    return state

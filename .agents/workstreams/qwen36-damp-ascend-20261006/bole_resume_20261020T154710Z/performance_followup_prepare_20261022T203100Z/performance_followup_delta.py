"""Pure exact renderers over the immutable fixed1024 prototype. No numerical admission."""
import hashlib
import json
from pathlib import Path

PARENT=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_performance_profile_prepare_20261021/successor_layer/bound-bole-v2-r1/SOURCE_BOUND.json')
RUNTIME=('service_runner.py','transaction.py','tp_consensus.py','bole_performance_lifecycle.py','host_service.py','model_entry.py','service_bridge.py')


def once(text,before,after):
    if text.count(before)!=1:raise ValueError('exact single source delta: '+before[:100])
    return text.replace(before,after,1)


def render(old):
    if set(old)!=set(RUNTIME):raise ValueError('complete exact runtime input')
    out=dict(old)
    s=out['service_runner.py']
    s=once(s,'import bole_performance_profile as PERF','import bole_performance_profile as PERF\nimport validated_performance_policy as FAST')
    s=once(s,"    performance = PERF.select(os.environ, m.get('performance_profile'))",
        "    performance = PERF.select(os.environ, m.get('performance_profile'))\n"
        "    fast_performance = FAST.select(C,m,os.environ)\n"
        "    E.need(not fast_performance or performance is not None,'performance policy needs original profile; not numerical admission')")
    s=once(s,'    def after_prefill(**kw):','    state.validated_performance = fast_performance\n\n    def after_prefill(**kw):')
    before="""        cache_ref = cache_observation.capture(C, source_ref, worker, inner, request_id=kw['request_id'],
            request=kw['request'], metadata=kw['metadata'], context=kw['forward_context'], rank=group.rank_in_group, request_epoch=state.generation)
        fa_ref = fa_prefill131r10.capture(C, source_ref, worker, inner, request_id=kw['request_id'],
            request=kw['request'], metadata=kw['metadata'], context=kw['forward_context'],
            rank=group.rank_in_group, length=131, request_epoch=state.generation)"""
    s=once(s,before,'        cache_ref = fa_ref = None\n        if not fast_performance:\n'+'\n'.join('    '+line for line in before.splitlines()))
    s=once(s,"        for binding in bindings:\n            if binding['kind'] == 'gdn':","        for binding in (() if fast_performance else bindings):\n            if binding['kind'] == 'gdn':")
    # Keep real LM-head call; skip copies only used by independent diagnostic joins.
    s=once(s,"            E.need(len(args) == 1 and not kwargs, 'actual native target head hidden operand ABI')",
        "            E.need(len(args) == 1 and not kwargs, 'actual native target head hidden operand ABI')\n"
        "            if fast_performance:\n                return value")
    s=once(s,'        local = logits.detach().clone()','        local = logits if fast_performance else logits.detach().clone()')
    before="""            E.need(state.bridge.N.bits(torch, local, state.initial_target_head_local_logits) and
                state.bridge.N.bits(torch, state.initial_target_head_hidden, state.prefill['hidden'][-1:]),
                'actual native prefill head operand and sampler logits join')"""
    s=once(s,before,'            if not fast_performance:\n'+'\n'.join('    '+line for line in before.splitlines()))
    before="""        E.need(state.bridge.N.bits(torch, local, f.target_head_local_logits) and
            state.bridge.N.bits(torch, f.target_head_hidden, f.tree_hidden[:f.scheduled_nodes]),
            'actual admitted target hidden-to-head-to-sampler operand chain')"""
    s=once(s,before,'        if not fast_performance:\n'+'\n'.join('    '+line for line in before.splitlines()))
    s=once(s,'            target_next=target_next, remaining_output_tokens=f.remaining_output)',
        '            target_next=target_next, remaining_output_tokens=f.remaining_output,\n            collect_diagnostic=not fast_performance)')
    s=once(s,'            f.proposal_gpu_ids_after = runner.input_ids.gpu[:n].detach().clone()',
        '            if not fast_performance:\n                f.proposal_gpu_ids_after = runner.input_ids.gpu[:n].detach().clone()')
    # The before-image remains: nonidentity compaction actually consumes it.
    s=once(s,"        if record is not None:\n            num_tokens, indices, cad, _ = result",
        "        if record is not None and not fast_performance:\n            num_tokens, indices, cad, _ = result")
    s=once(s,"            record['first_local_logits'] = value.detach().clone()",
        "            if not fast_performance:\n                record['first_local_logits'] = value.detach().clone()")
    s=once(s,"            record['first_hidden'] = args[0].detach().clone()",
        "            if not fast_performance:\n                record['first_hidden'] = args[0].detach().clone()")
    for name in ('target_token_ids','target_positions','target_hidden_states'):
        s=once(s,"            "+name+"=a['"+name+"'].detach().clone(),",
            "            "+name+"=None if fast_performance else a['"+name+"'].detach().clone(),")
    # Narrow whole record operands so the earlier first_inputs block stays exact.
    before="""            token_indices_to_sample=indices.detach().clone(),
            query_start_loc=cad.query_start_loc.detach().clone(),
            num_rejected_tokens=None if rejected is None else rejected.detach().clone(),"""
    after="""            token_indices_to_sample=None if fast_performance else indices.detach().clone(),
            query_start_loc=None if fast_performance else cad.query_start_loc.detach().clone(),
            num_rejected_tokens=None if fast_performance or rejected is None else rejected.detach().clone(),"""
    s=once(s,before,after)
    s=once(s,"            record['native_result'] = result.detach().clone()",
        "            if not fast_performance:\n                record['native_result'] = result.detach().clone()")
    # The topk(first_logits), root ownership check and native MTP call are untouched.
    s=once(s,'        _verify_published(torch, state.bridge, f.proposal)',
        '        if not fast_performance:\n            _verify_published(torch, state.bridge, f.proposal)\n'
        '        else:\n            f.commit_metadata = FAST.commit_metadata(f.proposal,f.publication)')
    s=once(s,"                    emitted_tokens=list(f.publication['emitted_tokens'])), next_ack=None))",
        "                    emitted_tokens=list(f.publication['emitted_tokens'])), next_ack=None,\n"
        "                commit_metadata=f.commit_metadata if fast_performance else None))")
    s=once(s,'        state.bridge = bridge','        bridge.collect_performance_diagnostics = not fast_performance\n        state.bridge = bridge')
    out['service_runner.py']=s

    s=out['transaction.py']
    s=once(s,'def publish(torch,bridge,proposal,*,group,tokens,scheduled_nodes,target_next,remaining_output_tokens,current_owner):',
        "def publish(torch,bridge,proposal,*,group,tokens,scheduled_nodes,target_next,remaining_output_tokens,current_owner,collect_diagnostic=True):\n"
        " need(type(collect_diagnostic)is bool,'explicit diagnostic collection boolean')")
    s=once(s,'  rows=agreed.detach().cpu(),rank=group.rank_in_group,',
        '  rows=agreed.detach().cpu() if collect_diagnostic else None,rank=group.rank_in_group,')
    s=once(s,'before=TP.agree(torch,group,owner,tokens,terminal,device=device,phase=1)',
        'before=TP.agree(torch,group,owner,tokens,terminal,device=device,phase=1,collect_diagnostic=collect_diagnostic)')
    before="""  for row,dest,index in handles:
   actual=dest if index is None else dest[index//128,index%128]
   need(bridge.N.bits(torch,actual,row['after']),'actual permanent write bitwise')
   applied_values.append(actual.clone())"""
    s=once(s,before,'  if collect_diagnostic:\n'+'\n'.join(' '+line for line in before.splitlines()))
    s=once(s,'applied=TP.agree(torch,group,owner,tokens,terminal,device=device,phase=2)',
        'applied=TP.agree(torch,group,owner,tokens,terminal,device=device,phase=2,collect_diagnostic=collect_diagnostic)')
    s=once(s,'  actual_applied=applied_values,cache_published=True,',
        '  actual_applied=applied_values,diagnostic_readback_performed=collect_diagnostic,cache_published=True,')
    out['transaction.py']=s

    s=out['tp_consensus.py']
    s=once(s,'def agree(torch,group,owner,tokens,terminal,*,device,phase):',
        "def agree(torch,group,owner,tokens,terminal,*,device,phase,collect_diagnostic=True):\n"
        " need(type(collect_diagnostic)is bool,'explicit diagnostic collection boolean')")
    s=once(s,'             rows=gathered.detach().cpu(),rank=group.rank_in_group,',
        '             rows=gathered.detach().cpu() if collect_diagnostic else None,rank=group.rank_in_group,')
    out['tp_consensus.py']=s

    s=out['bole_performance_lifecycle.py']
    s=once(s,'        emit_retirement(record)',
        "        if getattr(state,'validated_performance',False):\n"
        "            commits=[step['commit_metadata'] for step in state.steps]\n"
        "            _require(len(commits)==len(state.steps) and all(c is not None for c in commits),\n"
        "                     'actual successful fast-path commits precede native retirement')\n"
        "            record['commit_metadata']=commits\n"
        "            record['tensor_readback_performed']=False\n"
        "        emit_retirement(record)")
    out['bole_performance_lifecycle.py']=s

    s=out['host_service.py']
    s=once(s,"  if performance:argv[2:2]=['--env',PERF.FLAG+'=1']",
        "  if performance:argv[2:2]=['--env',PERF.FLAG+'=1']\n"
        "  if performance and m.get('validated_performance_profile') is not None:\n"
        "   C.need(m['performance_arm']=='bole','native AR cannot enable BOLE policy')\n"
        "   argv[2:2]=['--env','BOLE_VALIDATED_PERFORMANCE_ENABLE=1']")
    out['host_service.py']=s
    # These fields are consumed only by independent numerical exports. The
    # actual state/keys/factors/trial and rollback before-images remain intact.
    s=out['model_entry.py']
    s=once(s,"  ctx.captures[b['index']]=dict(kind='gdn',phase='BEFORE_NATIVE_TREE_CONV',conv_trial=trial,raw_projected=mixed_qkv.clone(),a=aa.clone(),b=ba.clone(),weight=weight.clone(),activation=bool(obj.activation))",
        "  diagnostics=getattr(self,'collect_performance_diagnostics',True)\n"
        "  ctx.captures[b['index']]=dict(kind='gdn',phase='BEFORE_NATIVE_TREE_CONV',conv_trial=trial,raw_projected=mixed_qkv.clone() if diagnostics else None,a=aa.clone() if diagnostics else None,b=ba.clone() if diagnostics else None,weight=weight.clone() if diagnostics else None,activation=bool(obj.activation))")
    s=once(s,"  ctx.captures[b['index']].update(actual_convolved=convolved.clone(),actual_conv_tail=tail.clone())",
        "  if diagnostics:\n   ctx.captures[b['index']].update(actual_convolved=convolved.clone(),actual_conv_tail=tail.clone())")
    s=once(s,"  ctx.captures[b['index']].update(factors=factors,output=output.clone(),phase='TREE_GDN_COMPLETE')",
        "  ctx.captures[b['index']].update(factors=factors,output=output.clone() if diagnostics else output,phase='TREE_GDN_COMPLETE')")
    out['model_entry.py']=s
    # Service installs this exact FA override. Compact prefix copies are NOT
    # removed: actual A.prepare/native consumes them as algorithm inputs.
    s=out['service_bridge.py']
    s=once(s," ctx=BUS.get();ctx.visit(b['index'],'fa');t=self.t;o=ctx.owner",
        " ctx=BUS.get();ctx.visit(b['index'],'fa');t=self.t;o=ctx.owner\n diagnostics=getattr(self,'collect_performance_diagnostics',True)")
    s=s.replace('query=query.clone(),key=key.clone(),value=value.clone()',
        'query=query.clone() if diagnostics else None,key=key.clone() if diagnostics else None,value=value.clone() if diagnostics else None') if s.count('query=query.clone(),key=key.clone(),value=value.clone()')==2 else (_ for _ in ()).throw(ValueError('exact two FA diagnostic records'))
    s=once(s,'output=out.clone())','output=out.clone() if diagnostics else out)')
    out['service_bridge.py']=s
    for name,text in out.items():compile(text,name,'exec')
    return out


def main():
    import argparse
    import difflib
    parser=argparse.ArgumentParser(description='Pure source review only; never freezes or launches')
    parser.add_argument('--show-diff',action='store_true')
    args=parser.parse_args()
    old=original_sources();new=render(old)
    if args.show_diff:
        for name in RUNTIME:
            print(''.join(difflib.unified_diff(old[name].splitlines(True),new[name].splitlines(True),
                fromfile='immutable-parent/'+name,tofile='prepared-only/'+name)),end='')
    else:
        print(json.dumps(dict(prepared_only=True,performance_ready=False,numerical_qualified=False,
            files={name:dict(bytes=len(text.encode()),sha256=hashlib.sha256(text.encode()).hexdigest())
                   for name,text in new.items()}),sort_keys=True))


def original_sources():
    manifest=json.loads(PARENT.read_bytes())
    out={}
    for name in RUNTIME:
        reference=manifest['files'][name]
        raw=Path(reference['path']).read_bytes()
        if len(raw)!=reference['bytes'] or hashlib.sha256(raw).hexdigest()!=reference['sha256']:
            raise ValueError('original immutable performance source '+name)
        out[name]=raw.decode()
    return out


if __name__=='__main__':main()

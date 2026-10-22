"""Independent actual-frame checks. CPU truth evaluates real captured NPU outputs."""
import copy
import hashlib


def need(v,s):
    if not v:raise ValueError(s)


def selected_conv_write(t,N,write,row,terminal):
    # conv_math already proved ALL candidate tails against an independent
    # convolution history. This additional join proves the accepted one was
    # selected for the permanent write, not another numerically legal tail.
    N.equal(t,write['after'],row['actual_conv_tail'][terminal],
            'selected permanent conv tail follows independently verified accepted terminal')


def cpu_digest_source(original):
    # Saved evidence is CPU, by construction. Keep the original complete byte
    # representation/hash formula; do not spoof the source helper's NPU guard.
    marker="value.device.type == 'npu'"
    need(original.count(marker)==1,'exact original full-state digest device guard')
    return original.replace(marker,"value.device.type == 'cpu'",1)


def actual_cpu_digest(C,m):
    import ast
    import short_state_digest as D
    need(C.ref(D.__file__)==m['files']['short_state_digest.py'],'actual unchanged state witness digest helper')
    text=C.checked(m['files']['short_state_digest.py']).read_text()
    node=next(x for x in ast.parse(text).body if isinstance(x,ast.FunctionDef)and x.name=='tensor_digest')
    ns=dict(need=need,hashlib=hashlib)
    exec(compile(cpu_digest_source(ast.get_source_segment(text,node)),'source-derived-CPU-full-state-digest','exec'),ns)
    return D,ns['tensor_digest']


def generalized_attention(original):
    # Exact mechanical prefix-domain extension of the existing independent
    # FP64/FP32 formula; no tolerance, arithmetic or reference source is changed.
    replacements=[
      ('def attention(t,row,anchor):','def attention(t,row,anchor,length):'),
      ("need(len(table)==2 and len(set(table))==2,'actual131token physical prefix pages')",
       "need(len(table)>=(length+2+127)//128 and len(set(table))==len(table),'actual owned physical prefix pages')"),
      ('for p in range(131)','for p in range(length)')]
    s=original
    for a,b in replacements:
        need(s.count(a)==1 or(a=='for p in range(131)'and s.count(a)==2),'exact independent attention source operand')
        s=s.replace(a,b)
    return s


def actual_readers(C,m):
    import g2_numeric as N
    import independent_model as I
    import oracle112 as O
    import ast
    for name,mod in(('g2_numeric.py',N),('independent_model.py',I),('oracle112.py',O)):
        need(C.ref(mod.__file__)==m['files'][name],'actual unchanged independent reader '+name)
    text=C.checked(m['files']['independent_model.py']).read_text()
    node=next(x for x in ast.parse(text).body if isinstance(x,ast.FunctionDef)and x.name=='attention')
    source=ast.get_source_segment(text,node)
    ns=dict(need=I.need);exec(compile(generalized_attention(source),'source-derived-independent-attention','exec'),ns)
    return N,I,O,ns['attention']


def consume_frame(t,C,m,source,frame,*,previous=None):
    need(C.ref(__file__)==m['files']['fastpath_numeric_consumer.py'],'actual source-owned independent consumer')
    need(frame['schema']=='bole.actual-fastpath-frame-numeric-capture/v1'and frame['source']==source and
         frame['actual_FAST_readback_elided']is True and frame['qualification_observer']is True and
         frame['formal_performance']is False and frame['numerical_qualified']is False,
         'real qualification capture, never a mathematical PASS from producer')
    need(type(frame['rank'])is int and 0<=frame['rank']<4 and
         frame['runtime_execution']['environment']['HCCL_DETERMINISTIC']=='true',
         'actual captured TP4/common deterministic HCCL witness')
    N,I,O,attention=actual_readers(C,m)
    owner=frame['owner'];length=owner['length'];proposal=frame['staged'];pub=frame['publication']
    need(frame['generation']==owner['generation']in(1,2) and frame['ordinal']==owner['version'] and
         proposal['owner']==owner and pub['owner']==owner and frame['order']==list(range(64)),
         'actual frame/generation/owner and all64 traversal')
    path=proposal['processed_nodes'];terminal=path[-1]
    need(path in([0],[0,1],[0,2])and pub['processed_nodes']==path and
         pub['cache_published']is True and pub['diagnostic_readback_performed']is False and
         pub['actual_applied']==[] and pub['scheduler_ack_pending']is True,
         'real successful FAST transaction; original diagnostical arrays remain absent')
    before_g=N.by_layer(frame['before_GDN'],tuple(i for i in range(64)if i%4!=3))
    after_g=N.by_layer(frame['after_GDN'],tuple(i for i in range(64)if i%4!=3))
    before_f=N.by_layer(frame['before_FA'],tuple(i for i in range(64)if i%4==3))
    after_f=N.by_layer(frame['after_FA'],tuple(i for i in range(64)if i%4==3))
    rows=proposal['writes'];writes={(r['layer'],r['kind']):r for r in rows}
    expected={(i,k)for i in range(64)for k in(('key','value')if i%4==3 else('state','conv'))}
    need(len(rows)==len(writes)==len(frame['observed_applied'])==128 and set(writes)==expected,
         'all and only actual128 permanent destinations')
    metrics=[];passed=True
    for i in range(64):
        row=frame['captures'][i];metric=dict(layer=i)
        if i%4!=3:
            before=before_g[i];after=after_g[i]
            identity=before['slot_binding_identity']
            need(identity==after['slot_binding_identity'] and identity['request_id']==owner['request']and
                 identity['generation']==owner['generation']and identity['logical_owner_slot']==owner['slot']==0 and
                 identity['physical_slot']==before['physical_slot']==after['physical_slot']and
                 identity['group']==before['group']==after['group'],'actual GDN slot/group/request binding')
            base=before['native_state'].transpose(-1,-2).unsqueeze(0)
            N.equal(t,row['state'],base,'canonical GDN input joins actual selected native before-image')
            q,k,v,beta,gamma=row['normalized_inputs']
            need(q.shape==k.shape==v.shape==(1,12,3,128) and beta.shape==gamma.shape==(1,12,3)
                 and all(x.dtype==t.float32 for x in(q,k,v,beta,gamma)),'actual normalized GDN ABI')
            truth,states,updates=O.sequential(t,q.double(),k.double(),v.double(),beta.double(),
                  gamma.double(),base.double(),(-1,0,0),return_updates=True)
            metric['FP32_output']=I.old112(t,row['precast_output'],truth)
            metric['U']=I.old112(t,row['factors'][1],updates)
            gd=gamma.double();product=t.stack((gd[...,0],gd[...,0]*gd[...,1],gd[...,0]*gd[...,2]),dim=-1)
            metric['P']=I.old112(t,row['factors'][0],product)
            sw=writes[i,'state'];cw=writes[i,'conv']
            for w in(sw,cw):
                need(w['slot']==w['physical_slot']==before['physical_slot'] and
                     w['group']==before['group']and w['logical_owner_slot']==0 and
                     w['slot_binding_identity']==identity and 'slot_binding'not in w,
                     'actual serialized per-layer state/conv destination identity')
            metric['selected_state']=I.old112(t,sw['after'].transpose(-1,-2).unsqueeze(0),states[terminal])
            metric['conv']=N.conv_math(t,row,before)
            selected_conv_write(t,N,cw,row,terminal)
            N.equal(t,row['output'],row['precast_output'].permute(0,2,1,3).squeeze(0).to(t.bfloat16),
                    'actual BF16 output from actual FP32 return')
            N.equal(t,sw['before'],before['native_state'],'actual recurrent preimage')
            N.equal(t,after['native_state'],sw['after'],'actual recurrent permanent postimage')
            N.equal(t,cw['before'],before['full_conv_slot'][0,:3],'actual conv preimage')
            whole=before['full_conv_slot'].clone();whole[0,:3]=cw['after']
            N.equal(t,after['full_conv_slot'],whole,'selected wide tail and untouched extras')
            passed&=all(metric[k]['passed']for k in('FP32_output','U','P','selected_state'))
            passed&=metric['conv']['output_bound_pass']and metric['conv']['state_bitwise']
        else:
            before=before_f[i];after=after_f[i];N.fa_owner(before,after,row,owner)
            metric['attention']=attention(t,row,before,length)
            passed&=all(v['pointwise_pass']for v in metric['attention'].values())
            table=list(before['physical_pages'])
            indices=[table[(length+j)//128]*128+(length+j)%128 for j in range(len(path))]
            for kind in('key','value'):
                w=writes[i,kind];need(w['indices'].tolist()==indices,'only actual accepted physical KV slots')
                pre=t.stack([before[kind][table.index(index//128),index%128]for index in indices])
                N.equal(t,w['before'],pre,'actual selected FA permanent preimage')
                selected=row[kind].reshape(3,1,256)[list(path)]
                N.equal(t,w['after'],selected,'actual selected normalized/RoPE KV values')
                whole=before[kind].clone()
                for j,index in enumerate(indices):whole[table.index(index//128),index%128]=selected[j]
                N.equal(t,after[kind],whole,'request-owned table pages prefix/padding/unselected FA bytes untouched')
        metrics.append(metric)
    for w,actual in zip(rows,frame['observed_applied']):
        N.equal(t,actual,w['after'],'independently observed actual128 permanent writes')
    if previous is not None:
        need(previous['owner']['request']==owner['request']and previous['owner']['generation']==owner['generation']and
             previous['publication']['next_length']==length and previous['publication']['next_version']==owner['version'],
             'consecutive true actual frame owner/counter')
        for name,current in(('GDN',frame['before_GDN']),('FA',frame['before_FA'])):
            old={r['layer']:r for r in previous['after_'+name]}
            for r in current:
                for key in(('native_state','full_conv_slot')if name=='GDN'else('key','value')):
                    N.equal(t,r[key],old[r['layer']][key],'next actual before-image equals previous actual postimage')
    need(passed,'unchanged independent per-element/norm bounds failed; no tolerance relaxation')
    D,digest=actual_cpu_digest(C,m)
    selected_digests=[dict(layer=w['layer'],kind=w['kind'],after=digest(t,w['after']),
        **({'before':digest(t,w['before'])}if w['kind']in('state','conv')else{}))for w in rows]
    return dict(schema='bole.actual-fastpath-numeric-frame-ack/v1',source=source,rank=frame['rank'],
        generation=frame['generation'],ordinal=frame['ordinal'],frame_checks_passed=True,metrics=metrics,
        independent_reference='original oracle112.sequential / old112 / conv_math / source-derived attention',
        full128_actual_state_writes_verified=True,
        FA_coverage='request-owned table pages only; outside-table arena remains unverified',
        outside_table_FA_arena_pending=True,
        selected_write_digests=selected_digests,
        consumer_sources=[C.ref(mod.__file__)for mod in(N,I,O,D)],
        TP_transaction_code_unchanged=True,TP_raw_collective_receipts_pending=True,
        HTTP_retirement_join_pending=True,domain_complete=False,
        numerical_qualified=False,whole_model_pass=False,formal_performance=False)

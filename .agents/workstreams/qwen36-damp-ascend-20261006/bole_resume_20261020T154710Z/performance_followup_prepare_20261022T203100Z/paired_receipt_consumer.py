"""HTTP/commit/real-native-retirement join; no numerical qualification."""
def need(v,s):
    if not v:raise ValueError(s)


def tokens(v):
    return type(v)is list and all(type(x)is int and x>=0 for x in v)


def candidate_record(record,http):
    need(record['request']==http['id']+'-0' and record['output_token_ids']==http['token_ids'],
         'real request retirement/HTTP token identity')
    generation=record['generation'];ret=record['retirement'];commits=record['commit_metadata']
    need(type(generation)is int and generation in(1,2) and
         ret['schema']=='bole.service-owner-native-retirement/v1' and
         ret['request']==record['request'] and ret['generation']==generation and
         ret['scheduler_committed_independently']is False and ret['final_success']is False and
         ret['steps']==len(commits) and 512<=len(commits)<=1023,
         'actual bounded native retirement, not synthetic commit counter')
    emitted=[];length=131
    for version,c in enumerate(commits):
        need(c['schema']=='bole.performance-commit-metadata/v1' and
             c['request']==record['request'] and c['generation']==generation and c['version']==version and
             c['destination_count']==128 and c['cache_published']is True and
             c['scheduler_ack_pending']is True and c['tensor_readback_performed']is False and
             c['numerical_qualified']is False and c['formal_performance']is False,
             'all actual successful metadata-only cache publications')
        path=c['processed_nodes'];ids=c['emitted_tokens']
        need(path in([0],[0,1],[0,2]) and tokens(ids) and len(ids)==len(path),
             'inclusive-root accepted path and emitted bonus count')
        length+=len(path)
        need(c['next_length']==length and c['next_version']==version+1,
             'strict contiguous physical cache/version advance')
        emitted+=ids
    need(tokens(http['token_ids']) and len(http['token_ids'])==1024 and
         emitted==http['token_ids'][1:] and record['tensor_readback_performed']is False,
         'every accepted token and bonus equals actual HTTP after native prefill token')
    acknowledgements=ret['next_counter_acknowledgements']
    need(len(acknowledgements)==len(commits)-1 and ret['final_ack_by_retirement_pending']is True,
         'each nonfinal cache publication observed by next native counter; final by real retirement')
    for c,a in zip(commits,acknowledgements):
        need(a['schema']=='bole.service-native-scheduler-ack/v1' and
             a['request']==record['request'] and a['previous_version']==c['version'] and
             a['version']==c['next_version'] and a['computed_tokens']==c['next_length'] and
             a['next_root']==c['emitted_tokens'][-1] and a['scheduler_committed']is True and
             a['whole_model_qualification']is False and a['final_success']is False,
             'actual native counter ACK exactly joins preceding commit')
    last=ret['last_publication'];c=commits[-1]
    need(last is not None and last['owner']['request']==record['request'] and
         last['owner']['generation']==generation and last['owner']['length']==c['next_length']-len(c['processed_nodes']) and
         last['owner']['version']==c['version'] and last['next_length']==c['next_length'] and
         last['next_version']==c['next_version'] and last['emitted_tokens']==c['emitted_tokens'],
         'final pending publication belongs to the actually removed native request')
    return dict(generation=generation,request=record['request'],commits=len(commits),
        output_tokens=1024,final_ack='actual-native-removal-plus-HTTP-ID-join',
        numerical_qualified=False,formal_performance=False)


def consume(*,C,source,manifest,client_output,receipt_root):
    need(C.ref(__file__)==manifest['files']['paired_receipt_consumer.py'],
         'actual exact source-bound metadata join helper')
    http=C.obj(C.ref(client_output/'HTTP_RESULT.json'))
    need(manifest['performance_arm']=='bole' and manifest.get('validated_performance_profile') is not None,
         'only explicit BOLE fast-path metadata')
    proofs=[];canonical={}
    for rank in range(4):
        for generation in (1,2):
            ref=C.ref(receipt_root/('PERF-RETIRE-GEN-%d-RANK-%d.json'%(generation,rank)))
            item=C.obj(ref)
            need(item['source']==source and item['rank']==rank and item['generation']==generation and
                 item['kind']=='RETIRE','actual rank/source/generation metadata wrapper')
            record=item['record'];proof=candidate_record(record,http['rows'][generation-1])
            if generation in canonical:need(record==canonical[generation],'all4 identical real commit and retirement paths')
            else:canonical[generation]=record
            proofs.append(dict(rank=rank,retirement=ref,proof=proof))
    return dict(schema='bole.fast-performance-HTTP-publication-retirement-join/v1',
        proofs=proofs,commit_metadata_joined=True,independent_CPU_ACK=False,
        numerical_qualified=False,formal_performance=False)


def wrap_consumer(original):
    before='def consume(*, C, source, manifest, client_output, receipt_root):'
    need(original.count(before)==1,'single original complete HTTP/retirement consumer')
    text=original.replace(before,'def original_consume(*, C, source, manifest, client_output, receipt_root):',1)
    text+='''
def consume(*, C, source, manifest, client_output, receipt_root):
    # Original HTTP usage/timing, sticky failure, all4 retirement and completion
    # checks execute first; this extension never replaces those checks.
    result=original_consume(C=C,source=source,manifest=manifest,
        client_output=client_output,receipt_root=receipt_root)
    if manifest['performance_arm']=='bole':
        import paired_receipt_consumer as JOIN
        C.need(C.ref(JOIN.__file__)==manifest['files']['paired_receipt_consumer.py'],
               'source-bound commit metadata extension')
        result['publication_retirement_join']=JOIN.consume(C=C,source=source,manifest=manifest,
            client_output=client_output,receipt_root=receipt_root)
    result['all_observers_disabled']=False
    result['numerical_qualified']=False
    result['formal_performance']=False
    return result
'''
    compile(text,'performance_client_consumer.py','exec')
    return text

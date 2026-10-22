"""Short8 actual FAST numeric reports + original full HTTP/state/retirement join."""
from pathlib import Path


def need(v,s):
    if not v:raise ValueError(s)


def consume(C,m,source,host_result_ref):
    import performance_client_consumer as ORIGINAL
    import fastpath_numeric_consumer as NUMERIC
    need(C.ref(__file__)==m['files']['qualification_smoke_join.py']and
         C.ref(ORIGINAL.__file__)==m['files']['performance_client_consumer.py']and
         C.ref(NUMERIC.__file__)==m['files']['fastpath_numeric_consumer.py'],
         'actual source-bound original short consumer and independent numeric consumer')
    need(m['fastpath_numeric_qualification']['output_tokens']==8 and
         m['short_state_digest_profile']['output_tokens']==8,'short8 domain only')
    output=Path(m['output_root']);receipt=Path(m['model_receipt_root'])
    host=C.obj(host_result_ref)
    need(host['source']==source and host['primary']is None and host['secondary']==[] and
         host['schema']=='bole.actual-three-node-model-owned/v131'and
         host['source_before']==host['source_after']and host['formal_performance']is False,
         'actual completed cleaned owned host result with unchanged source, not an in-progress summary')
    original=ORIGINAL.consume(C=C,source=source,manifest=m,
        client_output=output/'dense/performance-client',receipt_root=receipt)
    need(original==host['summary']['streaming_validation']and
         original['schema']=='bole.short-state-single-arm-consumption/v1'and
         original['arm_state_receipts_verified']is True,'original HTTP/token/state/retirement stage unweakened')
    reports=[];semantics={};budget=[]
    for rank in range(4):
        root=receipt/('FASTPATH-NUMERIC-R%d'%rank)
        expected=set()
        for generation in(1,2):
            retire=C.obj(C.ref(receipt/('STATE-RETIRE-G%d-O-1-R%d.json'%(generation,rank))))
            steps=retire['record']['retirement']['steps']
            for ordinal in range(steps):
                stem='G%d-O%d'%(generation,ordinal);expected.update((stem+'.json',stem+'-RELEASE.json'))
                r=C.ref(root/(stem+'.json'));report=C.obj(r)
                need(report['schema']=='bole.actual-fastpath-numeric-frame-ack/v1'and
                     report['source']==source and report['rank']==rank and
                     report['generation']==generation and report['ordinal']==ordinal and
                     report['frame_checks_passed']is True and
                     report['full128_actual_state_writes_verified']is True and
                     report['numerical_qualified']is False and report['formal_performance']is False,
                     'each actual independently consumed full64/128 frame, never cached overall PASS')
                for ref in report['consumer_sources']:C.checked(ref)
                metrics=report['metrics']
                need(len(metrics)==64 and [x['layer']for x in metrics]==list(range(64)),
                     'actual complete independent64-layer numeric coverage')
                for metric in metrics:
                    if metric['layer']%4!=3:
                        need(all(metric[k]['passed']is True for k in('FP32_output','U','P','selected_state'))and
                             metric['conv']['output_bound_pass']is True and metric['conv']['state_bitwise']is True,
                             'original independent GDN and conv bounds actually passed')
                    else:need(all(metric['attention'][k]['pointwise_pass']is True for k in('double','float')),
                              'independent original FA pointwise bounds actually passed')
                state=C.obj(C.ref(receipt/('STATE-STEP-G%d-O%d-R%d.json'%(generation,ordinal,rank))))['record']
                observed={(x['layer'],x['kind']):x for x in state['rows']}
                got={(x['layer'],x['kind']):x for x in report['selected_write_digests']}
                need(len(got)==128 and set(got)==set(observed),'all actual short-state and numeric destinations join')
                for key,v in got.items():
                    need(v['after']==observed[key]['after']and
                         ('before'not in v or v['before']==observed[key]['before']),
                         'full actual numeric operands/writes equal original actual state witness')
                release_ref=C.ref(root/(stem+'-RELEASE.json'));release=C.obj(release_ref)
                need(release['source']==source and release['report']==r and
                     release['actual_frame']==report['actual_frame']and
                     release['retained']is(generation==1 and ordinal==0)and
                     release['released_after_independent_consumption']is not release['retained'],
                     'actual durable report precedes bounded own-frame release')
                if release['retained']:C.checked(release['actual_frame'])
                else:need(not Path(release['actual_frame']['path']).exists(),'released raw really absent, not claimed replayable')
                semantic={k:state[k]for k in('request','version','length','tokens','processed_nodes','emitted_tokens')}
                key=(generation,ordinal)
                if key in semantics:need(semantics[key]==semantic,'all4 actual same target/accepted/output semantics')
                else:semantics[key]=semantic
                reports.extend([r,release_ref])
        need({p.name for p in root.glob('*.json')}==expected,'no missing/extra qualification receipts')
        all_files=list(root.iterdir())
        need(all(p.is_file()and not p.is_symlink()for p in all_files)and
             {p.name for p in all_files}==expected|{'G1-O0.pt'},
             'all-and-only actual retained raw/JSON files inside new owned evidence leaf')
        json_bytes=sum(p.stat().st_size for p in all_files if p.suffix=='.json')
        total=sum(p.stat().st_size for p in all_files)
        need(json_bytes<=64*2**20 and total<=2**30 and
             all(p.stat().st_size<=256*2**10 for p in all_files if p.suffix=='.json'),
             'actual complete new qualification evidence directories charged; not omitted from old budget')
        budget.append(dict(rank=rank,actual_total_bytes=total,actual_JSON_bytes=json_bytes,
                           raw_and_metadata_cap=2**30,metadata_cap=64*2**20))
    return dict(schema='bole.actual-fastpath-short8-independent-numeric-scope/v1',source=source,
        original_stage=original,numeric_reports=reports,actual_evidence_budget=budget,short8_numeric_scope_passed=True,
        full64_layers_and128_actual_writes=True,all4_actual_HTTP_state_lifecycle_join=True,
        qualification_observer_active=True,performance_measurement=False,
        numerical_qualified=False,whole_model_pass=False,formal_performance=False,task_accuracy=False,
        pending=['same-config diagnostic-control paired NPU join',
                 'explicit TP all_gather raw-result witness or independently reviewed equivalent evidence',
                 '160/1024 bounded-stream qualification and page/slot transition coverage',
                 'qualification observer disabled same-compute integration proof before formal timing'])


def main():
    import argparse
    import json
    parser=argparse.ArgumentParser(description='Post-host actual short8 numeric/state consumer only')
    parser.add_argument('--consume',action='store_true')
    parser.add_argument('--source')
    parser.add_argument('--host-result')
    parser.add_argument('--output')
    args=parser.parse_args()
    if not args.consume:
        need(not any((args.source,args.host_result,args.output)),'explicit consume required for actual input operands')
        print(json.dumps(dict(enabled=False,NPU=False,numerical_qualified=False)))
        return
    need(all((args.source,args.host_result,args.output)),'explicit real source/terminal RESULT/fresh output')
    import sourceio as C
    source=C.ref(Path(args.source));m=C.obj(source)
    root=Path(m['root']);out=Path(m['output_root'])
    need(root==Path(source['path']).parent and m['prepared_only']is False and
         m['default_enabled']is False and Path(__file__).resolve()==root/'qualification_smoke_join.py',
         'actual bound defaultOFF qualifier source-owned consumer')
    need(Path(args.host_result)==out/'RESULT.json'and Path(args.output)==out/'FASTPATH_NUMERIC_SCOPE_RESULT.json'and
         out.is_dir()and not Path(args.output).exists(),'exact post-host inputs and exclusive new result path')
    result=consume(C,m,source,C.ref(Path(args.host_result)))
    ref=C.write(Path(args.output),result)
    print(json.dumps(dict(result=ref,short8_numeric_scope_passed=result['short8_numeric_scope_passed'],
                         numerical_qualified=False,whole_model_pass=False,formal_performance=False)))


if __name__=='__main__':main()

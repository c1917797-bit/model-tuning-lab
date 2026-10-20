"""Exact actual HTTP ledger origins; never synthesizes a missing receipt field."""
from pathlib import Path


def validate(C,x,m,y,source,bundle,value,schema,header_prefix,frozen):
    C.need(frozen['reference']==x['frozen_inputs']and len(frozen['token_ids'])==131 and
           frozen['source']==m['BOLE_source_ref']and frozen['input_tokens']==131 and
           frozen['tokenizer']=='/models/Qwen3.6-27B'and frozen['data_generated_by_actual_tokenizer']is True,
           'same original actual tokenizer INPUTS receipt, not invented provenance')
    refs=y['actual_prior_cpu_failure_refs']
    if schema=='bole.actual-native-ar-smoke-HTTP/v1':
        C.need(source==x['AR_source']and bundle['http']==refs['AR/HTTP_RESULT.json']and
               value['source']==source and value['pair_source']==source and value['variant']=='native_AR'and
               value['collector']==m['files']['pair_entry.py']and value['inputs_ref']==frozen['reference']and
               header_prefix=='bole-native-ar-131-'and value['untimed']is True and
               value['normal_EOS_qualified']is False,'actual nativeAR source/collector/shared-input receipt join')
    else:
        C.need(schema=='bole.actual-c1-two-request-service-HTTP/v1'and source==m['BOLE_source_ref']and
               bundle['http']==refs['BOLE/HTTP_RESULT.json']and header_prefix=='bole-g1-131-'and
               set(value)=={'schema','source','rows','whole_model_qualified','scheduler_committed'}and
               'inputs_ref'not in value and value['whole_model_qualified']is False and value['scheduler_committed']is False,
               'exact original G1 ledger schema; no fabricated inputs_ref')
        on,owner,original,report=C.g1_pass(source,x['G1_owner'],x['G1_bundle'],x['G1_independent'])
        C.need(original['http']==bundle['http']and value['source']==source and
               Path(bundle['http']['path'])==Path(frozen['reference']['path']).parent/'HTTP_RESULT.json',
               'same actual G1 HTTP and adjacent original INPUTS collection directory')
        terminal=C.obj(owner['summary']['actual_client_terminal']);argv=terminal['actual_argv']
        client=on['files']['service_client.py'];C.checked(client)
        C.need(terminal['exit_code']==0 and argv.count(client['path'])==1 and argv.count('--source-ref')==1 and
               __import__('json').loads(argv[argv.index('--source-ref')+1])==source and argv.count('--output')==1 and
               argv[argv.index('--output')+1]==str(Path(frozen['reference']['path']).parent),
               'actual zero-exit original source-bound G1 collector wrote INPUTS and HTTP in same output')
    # The unchanged http_tokens body checks every prompt, status, sampling,
    # header, usage, finish reason and exact output IDs after this predicate.
    return True

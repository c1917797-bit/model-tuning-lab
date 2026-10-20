"""Collect an already owned endpoint; does not start, authenticate or stop hosts."""
import argparse
import json
from pathlib import Path
import time
import urllib.request
import urllib.parse
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0,str(_Path(__file__).resolve().parent))
import pair_contract as C


def run(pair_sr, variant, variant_sr, inputs_ref, output, base_url, open_url=urllib.request.urlopen):
    m = C.source(pair_sr)
    C.need(C.ref(__file__) == m['files']['pair_entry.py'], 'exact paired collection entry')
    C.need(variant in ('native_AR', 'BOLE') and output.is_absolute() and output.is_dir()
           and not any(p.is_symlink() for p in (output, *output.parents)), 'owned variant output')
    uri = urllib.parse.urlparse(base_url)
    C.need(uri.scheme == 'http' and uri.hostname in ('127.0.0.1', 'localhost')
           and uri.path in ('', '/') and uri.username is None and not uri.query and not uri.fragment,
           'explicit owned loopback endpoint only')
    inputs = C.obj(inputs_ref)
    ids = inputs['token_ids']
    C.need(type(ids) is list and len(ids) == 131 and all(type(x) is int and x >= 0 for x in ids),
           'one frozen actual token-ID input for both variants')
    C.need(inputs['source']==m['BOLE_source_ref'] and inputs['input_tokens']==131
           and inputs['tokenizer']=='/models/Qwen3.6-27B'
           and inputs['data_generated_by_actual_tokenizer']is True,
           'reuse the exact original source-bound G1 tokenizer input receipt')
    C.need(variant_sr == (pair_sr if variant == 'native_AR' else m['BOLE_source_ref']),
           'exact variant source and shared pair authority')
    if variant == 'BOLE':
        on = C.obj(variant_sr)
        C.need(on['service_experiment'] == dict(schema='bole.c1-two-request-service/v1', prefix=131,
            request_count=2, max_steps_per_request=1, max_output_tokens=2),
            'bounded frozen G1-compatible ON profile')
    rows = []
    for label, count in (('tree-1', 2), ('tree-2', 2), ('retirement-barrier', 1)):
        header = ('bole-native-ar-131-' if variant == 'native_AR' else 'bole-g1-131-') + label
        body = dict(model='qwen36-mxr-eager', prompt=ids, max_tokens=count, temperature=0,
                    top_p=1, n=1, stream=False, ignore_eos=True, return_token_ids=True)
        request = urllib.request.Request(base_url.rstrip('/') + '/v1/completions',
            data=json.dumps(body).encode(), headers={'Content-Type':'application/json','X-Request-Id':header})
        start = time.monotonic()
        try:
            with open_url(request, timeout=600) as response:
                wire, status = response.read(8*2**20 + 1), response.status
            C.need(len(wire) <= 8*2**20, 'bounded actual response wire')
            path = output / ('HTTP-' + label + '.json')
            with path.open('xb') as f:
                f.write(wire)
            response_ref = C.ref(path)
            value = C.obj(response_ref)
            C.need(status == 200 and 'error' not in value and value['id'] == 'cmpl-' + header
                   and value['usage']['prompt_tokens'] == 131
                   and value['usage']['completion_tokens'] == count and len(value['choices']) == 1,
                   'actual completed response/header/count join')
            choice = value['choices'][0]
            C.need(choice['finish_reason'] == 'length' and type(choice.get('token_ids')) is list
                   and len(choice['token_ids']) == count
                   and all(type(x) is int and x >= 0 for x in choice['token_ids']),
                   'actual returned IDs and intentional fixed-budget smoke termination')
            rows.append(dict(label=label, header=header, request=body, response=response_ref,
                             http_status=status, elapsed=time.monotonic()-start))
        except BaseException as error:
            C.write(output/'HTTP-FAILURE.json', dict(pair_source=pair_sr, source=variant_sr,
                    variant=variant, rows=rows, primary=repr(error)))
            raise
    schema = C.AR_HTTP if variant == 'native_AR' else 'bole.actual-c1-two-request-service-HTTP/v1'
    result = dict(schema=schema, source=variant_sr, pair_source=pair_sr,
        variant=variant, inputs_ref=inputs_ref, collector=m['files']['pair_entry.py'], rows=rows,
        untimed=True, normal_EOS_qualified=False, model_ready=False, performance_ready=False)
    return C.write(output/'HTTP_RESULT.json', result)


def main():
    p = argparse.ArgumentParser(allow_abbrev=False)
    p.add_argument('--execute', action='store_true')
    p.add_argument('--source-ref'); p.add_argument('--variant', choices=('native_AR','BOLE'))
    p.add_argument('--variant-source-ref'); p.add_argument('--inputs-ref')
    p.add_argument('--output', type=Path); p.add_argument('--base-url')
    a = p.parse_args()
    if not a.execute:
        print('{"enabled":false,"NPU":false}'); return 0
    C.need(all(x is not None for x in (a.source_ref,a.variant,a.variant_source_ref,a.inputs_ref,
                                      a.output,a.base_url)), 'explicit owned pair collection arguments')
    result = run(json.loads(a.source_ref), a.variant, json.loads(a.variant_source_ref),
                 json.loads(a.inputs_ref), a.output, a.base_url)
    print(json.dumps(result)); return 0


if __name__ == '__main__':
    raise SystemExit(main())

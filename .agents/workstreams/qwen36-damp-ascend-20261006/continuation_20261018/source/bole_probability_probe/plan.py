"""Immutable one-rank R6 source and three preregistered FA cases."""
ROOT = '/opt/host/vnf/austinov/run-bole-r6-20261017-001-MAIN'
SOURCE = dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-model-root-repeat-witness-renew24h-v1-20261017-001-repair6-projection-scope/SOURCE_BOUND.json', bytes=81841, sha256='f3303cec9fea4c7445e81373e21cd0da5884be495b72a8847420bf4400bb92f5')
RANK_REPORT = dict(path=ROOT+'/cpu-consumer/RANK-1.json', bytes=110007, sha256='751fad500cd4d530f639bb3d35c8c07ea719c3493c798f17b02072c4f197ce32')
RECEIPT = dict(path=ROOT+'/dense/receipts/BOLE-TREE-RANK-1.json', bytes=2287, sha256='2c667174e1851ab5ca762e612d34960217fff31297039b87601e0624696a64a7')
RAW = dict(path=ROOT+'/dense/receipts/BOLE-TREE-RANK-1.pt', bytes=776474709, sha256='21ab99d4a503f45f750c1926eb383b633b7ced8e9f24b767275c107da89f1c34')
PREVIOUS = dict(path='/opt/host/vnf/austinov/run-bole-fa-rounding-binding-MAIN-RENEW24H_001/fa/consumer/RANK-1.json', bytes=38445, sha256='b70166459442dd5dd4c43f4d3fb044b71bd4b9980a5df0c20061bbf6d35d23b6')
CASES = [
    dict(id='tree-r1-l43-n2', kind='tree', layer=43, node=2, label='tree-node2',
         key_tokens=133, original_failed_elements=1),
    dict(id='native-r1-l43-p2-n2', kind='native', layer=43, path=2, node=2,
         label='native-path2-node2', key_tokens=133, original_failed_elements=1),
    dict(id='tree-r1-l43-n0-pass-control', kind='tree', layer=43, node=0,
         label='tree-node0', key_tokens=132, original_failed_elements=0),
]


def expected():
    return dict(schema='bole.fa-probability-quantization-plan/v1', source=SOURCE,
                rank=1, rank_report=RANK_REPORT, receipt=RECEIPT, raw=RAW,
                previous_diagnostic=PREVIOUS, cases=CASES,
                scale=0.0625, atol=0.001, rtol=0.01, qualified=False,
                original_numeric_failures_unchanged=True)


def consume(C, plan_ref):
    plan = C.obj(plan_ref)
    C.need(plan == expected(), 'exact fixed R6 source, rank1 and preregistered cases')
    source = C.obj(SOURCE)
    C.need(source['prepared_only'] is False and source['whole_numerical_qualification'] is False,
           'original nonqualified R6 diagnostic source')
    rank = C.obj(RANK_REPORT)
    C.need(rank['source'] == SOURCE and rank['receipt'] == RECEIPT and rank['raw'] == RAW and
           rank['report']['component_checks_pass'] is False and
           rank['report']['whole_numerical_qualified'] is False, 'preserve original failed R6 report')
    receipt = C.obj(RECEIPT)
    C.need(receipt['source'] == SOURCE and receipt['rank'] == 1 and
           receipt['primary'] is None and receipt['raw'] == RAW,
           'complete original rank1 producer/raw join')
    C.checked(RAW)
    previous = C.obj(PREVIOUS)
    C.need(previous['schema'] == 'bole.saved-fa-compensated-rounding-diagnostic/v1' and
           previous['rank'] == 1 and previous['original_source'] == SOURCE and
           previous['original_raw'] == RAW and previous['rank_report'] == RANK_REPORT and
           previous['qualified'] is False and previous['NPU'] is False and
           previous['original_failures_preserved'] is True,
           'fixed completed nonqualified rounding diagnostic')
    rows = [row for row in previous['rows'] if row['layer'] == 43]
    C.need(len(rows) == 1, 'exact prior layer43')
    for case in CASES:
        group = 'tree' if case['kind'] == 'tree' else 'native_own_inputs'
        nodes = [row for row in rows[0][group] if row['label'] == case['label']]
        C.need(len(nodes) == 1 and nodes[0]['elements'] == 1536 and
               nodes[0]['failed'] == nodes[0]['compensated_failed'] == case['original_failed_elements'] and
               nodes[0]['failed_set_changed'] is False, 'fixed original 1/1/0 numerical case status')
    return dict(plan=plan, previous=previous,
                readset=[plan_ref, SOURCE, RANK_REPORT, RECEIPT, RAW, PREVIOUS],
                qualified=False)

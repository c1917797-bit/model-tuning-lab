"""Bounded reporting-only join of four completed NPU diagnostic consumers.

No NPU, new numerical oracle, threshold change, source binding or qualification.
Original native/candidate full GDN raw results remain the numerical evidence.
"""
import hashlib,json,os
from pathlib import Path

EXPECTED=[
  [
    {
      "path": "/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-CURRENT24H_MXR48CTX1_NPU_001/RESULT.json",
      "bytes": 590777,
      "sha256": "bf218659bce5202852a1f3546d71360b7d486663cbd9b63d64604ca24f9eec78"
    },
    {
      "path": "/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-CURRENT24H_MXR48CTX1_NPU_001/physical6/numeric/CONSUMED.json",
      "bytes": 69127,
      "sha256": "b494391e6b3b3389d2c17e5099085c2c9be38bdd1e815f95dd51906500233a61"
    },
    {
      "path": "/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-CURRENT24H_MXR48CTX1_NPU_001/physical6/cleanup.json",
      "bytes": 1592,
      "sha256": "c6cbd06ac1423cdc51e91d7b66dfc559b94c316e6cb1cabeac5673574d7aa3f0"
    }
  ],
  [
    {
      "path": "/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-CURRENT24H_MXR48CTX1_S1_NPU_001/RESULT.json",
      "bytes": 594672,
      "sha256": "64e9d7c9e18981fdbae41bb60de11dfcf01069b547dc512f963879694306b80f"
    },
    {
      "path": "/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-CURRENT24H_MXR48CTX1_S1_NPU_001/physical6/numeric/CONSUMED.json",
      "bytes": 69148,
      "sha256": "f0c25804e638f7f557ee9e30a98e80ea706e65afe004d2e3c7854c22cbb709d1"
    },
    {
      "path": "/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-CURRENT24H_MXR48CTX1_S1_NPU_001/physical6/cleanup.json",
      "bytes": 11732,
      "sha256": "5ad05c4807ff22f7a1944013636daa9452ada4347d323d6dd1a360d7536b5838"
    }
  ],
  [
    {
      "path": "/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-CURRENT24H_MXR48CTX1_S2_NPU_001/RESULT.json",
      "bytes": 594670,
      "sha256": "84bf8f6d3d08382b643b44e4f70c898bde3f670c35673027b7b12830077e4064"
    },
    {
      "path": "/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-CURRENT24H_MXR48CTX1_S2_NPU_001/physical6/numeric/CONSUMED.json",
      "bytes": 69157,
      "sha256": "cf21980f24d2cb376a9413c69a44b693790516d2add3e8d1e89ad719e56497da"
    },
    {
      "path": "/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-CURRENT24H_MXR48CTX1_S2_NPU_001/physical6/cleanup.json",
      "bytes": 6667,
      "sha256": "4b35a98212e8e3c3b74266ae0cca22676b3431ba40d8b2994c596059496f0f3c"
    }
  ],
  [
    {
      "path": "/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-CURRENT24H_MXR48CTX1_S3_NPU_001/RESULT.json",
      "bytes": 594671,
      "sha256": "b8ef11e6df9d42a8583350b7bc273c22dc688cb89a51e19572522ec61d43501e"
    },
    {
      "path": "/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-CURRENT24H_MXR48CTX1_S3_NPU_001/physical6/numeric/CONSUMED.json",
      "bytes": 69083,
      "sha256": "1066a36ccae8faabb1d5bd89b1d86b9f946972f72a6942d8b4a925ab727c159a"
    },
    {
      "path": "/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-CURRENT24H_MXR48CTX1_S3_NPU_001/physical6/cleanup.json",
      "bytes": 6668,
      "sha256": "58c748bcf0dd9bc7c5dce9e11f16928a89aafaf1a4666e1f7805f0007b66baf5"
    }
  ]
]
OUTPUT=Path('/opt/host/vnf/austinov/run-mxr-full48-summary-20261023T110200Z-v1')
LIMITS=dict(frob_relative=0.002,r2_min=0.999,rmse_over_mean_ref_abs=0.02)


def need(v,message):
    if not v:raise ValueError(message)


def opened(ref):
    p=Path(ref['path'])
    need(p.is_absolute()and not any(q.is_symlink()for q in(p,*p.parents)),'ordinary original Ref')
    b=p.read_bytes()
    need(len(b)==ref['bytes']and hashlib.sha256(b).hexdigest()==ref['sha256'],'exact original Ref')
    def pairs(items):
        d={}
        for k,v in items:need(k not in d,'duplicate JSON key');d[k]=v
        return d
    return json.loads(b,object_pairs_hook=pairs)


def summary():
    cases=[];sources=[];actual_A=0;pair_output=0;pair_state=0
    canonical={arm:{part:0 for part in('output','state')}for arm in('candidate','native')}
    pair_failures=[];canonical_failures=[]
    for shard,refs in enumerate(EXPECTED):
        terminal,consumer,cleanup=map(opened,refs)
        need(terminal['primary']is None and terminal['secondary']==[],'original successful diagnostic lifecycle')
        need(terminal['cleanup']==refs[2]and cleanup['stopped']is True and cleanup['retained']is True
             and cleanup['errors']==[],'actual own release/retention')
        need(consumer['diagnostic_complete']is True and consumer['qualification']is False
             and len(consumer['rows'])==12,'complete original diagnostic, never qualification')
        for row in consumer['rows']:
            case=row['case']['case_id'];prefix=row['case']['prefix'];m=row['metrics']
            need(case not in cases,'no duplicate frame')
            cases.append(case)
            for k in('output','state'):
                metric=m['pair'][k];need(metric['limits']==LIMITS,'unchanged original numeric limits')
                if k=='output':pair_output+=int(metric['pass'])
                else:pair_state+=int(metric['pass'])
                if not metric['pass']:pair_failures.append(dict(case=case,prefix=prefix,part=k,metrics=metric))
            for arm in canonical:
                z=m['actual_A_inverse'][arm];need(z['limits']==LIMITS,'unchanged conditional actual-A limits')
                actual_A+=int(z['pass'])
                for part in canonical[arm]:
                    metric=m['canonical'][arm][part];need(metric['limits']==LIMITS,'unchanged full canonical limits')
                    canonical[arm][part]+=int(metric['pass'])
                    if not metric['pass']:canonical_failures.append(dict(case=case,prefix=prefix,arm=arm,part=part,metrics=metric))
        sources.append(dict(shard=shard,refs=refs,pair_pass=consumer['pair_pass'],
                            canonical_all_pass=consumer['canonical_all_pass']))
    need(sorted(cases)==['rank0-frame-%03d'%i for i in range(48)],'exact complete rank0 frames0-47')
    return dict(schema='mxr.actual-full48-diagnostic-reporting-join/v1',
      scope='Saved real rank0 candidate X2 intermediates versus newly executed native full-GDN NPU diagnostic; NOT new candidate whole-model execution.',
      frames=48,sources=sources,conditional_actual_A_inverse_pass=actual_A,
      conditional_actual_A_inverse_total=96,pair_output_pass=pair_output,pair_state_pass=pair_state,
      canonical_pass=canonical,pair_failures=pair_failures,canonical_failures=canonical_failures,
      numerical_limits_unchanged=LIMITS,all_owners_released=True,
      qualification=False,whole_model_performance=False,task_accuracy=False,
      findings=[
        'Diagnostic process exit0 proves completed capture/independent consumption and cleanup, not numeric qualification.',
        'actual_A_solve_residual is the independent CPU64 oracle self-check, not measured candidate/native inverse residual.',
        'Shared native/candidate canonical misses do not waive candidate-only canonical misses or pair-state failures.',
        'Current X2 numerical promotion is refused. This is not a paper-wide no-go.'],
      next_action='Attribute first new layer21 pair-state failure with actual CPU64-cast B/WY/H counterfactual; retain other failed frames as holdouts. No unchanged full48 rerun.')


def main():
    value=summary()
    need(not OUTPUT.exists()and OUTPUT.parent.is_dir(),'exclusive reporting output')
    OUTPUT.mkdir(mode=0o700)
    raw=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    need(len(raw)<=65536,'bounded report')
    path=OUTPUT/'RESULT.json'
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
    print(json.dumps(dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
      frames=48,pair_output=value['pair_output_pass'],pair_state=value['pair_state_pass'],
      actual_A=value['conditional_actual_A_inverse_pass'],canonical=value['canonical_pass'],qualification=False)))


if __name__=='__main__':main()

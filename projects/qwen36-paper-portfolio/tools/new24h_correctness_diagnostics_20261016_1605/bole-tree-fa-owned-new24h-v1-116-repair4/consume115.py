"""Pure Devices[] consumption; path gather reference never reads packed mask."""
import json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import tree_fa115 as F
from probe115 import checked


def consume(t,sr,stage):
    if stage['schema']!='bole.FIA-stage/v115'or stage['source']!=sr or len(stage['rows'])!=6:raise ValueError('complete actual six FIA calls')
    report=[]
    for index,row in enumerate(stage['rows']):
        raw=t.load(checked(row['raw']),map_location='cpu',weights_only=True)
        if raw['source']!=sr or(raw['case'],raw['mode'])!=(index//2,(1,0)[index%2]):raise ValueError('exact source/case/mode join')
        inp=raw['inputs'];expected_mask=F.forbid_mask(t,inp['prefixes'],inp['parents'],inp['key'].shape[2])
        batch,prefixes,witness=((1,[0],True),(1,[7],False),(16,[i%9 for i in range(16)],False))[index//2]
        planned=F.recipe(t,batch,prefixes,witness)
        if any(not t.equal(inp[n],planned[n])for n in('query','key','value'))or inp['parents']!=planned['parents']or inp['prefixes']!=prefixes:raise ValueError('actual QKV/requests match preregistered inputs')
        if not t.equal(inp['mask'],expected_mask):raise ValueError('actual mask exactly tree ancestry including prefix/padding')
        metrics=None if raw['primary']is not None else F.score(t,raw['output'],F.path_reference(t,inp))
        report.append(dict(case=raw['case'],mode=raw['mode'],raw=row['raw'],primary=raw['primary'],metrics=metrics,passed=metrics is not None and metrics['preregistered_allclose']))
    supported=[mode for mode in(0,1)if all(r['passed']for r in report if r['mode']==mode)]
    return dict(schema='bole.FIA-independent/v115',source=sr,rows=report,observed_mask_modes_supported_on_exact_test_matrix=supported,pass_gate=bool(supported),qualified=False,model_ready=False,packed_TND_paged_KV_tested=False)

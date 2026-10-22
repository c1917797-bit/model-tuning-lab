"""Actual frozen-command controls plus optional real MAIN source-only join."""
from pathlib import Path
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

HERE=Path(__file__).resolve().parent
WS=HERE.parent
sys.path.insert(0,str(HERE))
from bind_source_operand import source_ref_from_commands,parse_ref

def checked(r):
    p=Path(r['path']);b=p.read_bytes()
    assert len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256']
    return b

def ref(p):
    b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def data():
    cfg=json.loads((WS/'reduction_admission_prepare_v6_common_20261022T210000Z/CONFIG.ON.actual-v3.json').read_text())
    m=json.loads(checked(cfg['source_ref']));commands=json.loads(checked(cfg['commands_ref']))
    raw=checked(m['files']['command_contract.py'])
    tree=ast.parse(raw);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='expected')
    scope={'Path':Path,'json':json}
    exec(compile(ast.Module(body=[node],type_ignores=[]),'actual_checked_command_contract.expected','exec'),scope)
    return cfg,m,commands,scope['expected']

def one_main(mode):
    cfg,m,commands,expected=data()
    cfg['source_ref']=source_ref_from_commands(commands,cfg['source_ref'],m,commands['source'],expected)
    # Preserve this nested insertion order on the config's actual JSON roundtrip.
    cfg=json.loads(json.dumps(cfg,sort_keys=(mode=='reordered')))
    path=WS/'reduction_admission_prepare_v6_common_20261022T210000Z/main_admission_ON_v6_common.py'
    s=importlib.util.spec_from_file_location('_independent_actual_MAIN_sourceinputs',path)
    M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
    os.environ['DENSE090_EXTERNAL_OUTPUT_ENABLE']='1'
    rs=M.Readset()
    try:
        result=M.source_inputs(rs,cfg)
    except ValueError as e:
        if mode!='reordered':raise
        assert 'exact current runnable model/CPU/bind commands' in str(e),str(e)
        print(json.dumps(dict(mode=mode,expected_rejection=str(e),readset_count=len(rs.refs),NPU=False)))
        return
    assert mode=='ordered','semantic Ref order incorrectly admitted'
    assert result[0]==m and result[1]==commands
    rs.verify_again()
    print(json.dumps(dict(mode=mode,actual_MAIN_source_inputs=True,readset_count=len(rs.refs),NPU=False)))

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--one-main',choices=['ordered','reordered'])
    p.add_argument('--real-main-controls',action='store_true')
    a=p.parse_args()
    if a.one_main:
        one_main(a.one_main);return
    cfg,m,commands,expected=data();cases=[]
    r=source_ref_from_commands(commands,cfg['source_ref'],m,commands['source'],expected)
    literal=commands['model'][commands['model'].index('--source-ref')+1]
    assert list(r)==['path','bytes','sha256'] and json.dumps(r)==literal
    assert source_ref_from_commands(commands,dict(sorted(cfg['source_ref'].items())),m,commands['source'],expected)==r
    cases.append('actual_MODEL_CPU_operand_preserved_against_semantically_equal_sorted_review')
    def reject(c,why):
        try:source_ref_from_commands(c,cfg['source_ref'],m,commands['source'],expected)
        except ValueError:cases.append(why)
        else:raise AssertionError(why)
    c=copy.deepcopy(commands);i=c['CPU'].index('--source-ref')+1;c['CPU'][i]=json.dumps(dict(sorted(r.items())))
    reject(c,'MODEL_CPU_literal_divergence_rejected')
    b=commands['bind'];template=parse_ref(b[b.index('--reviewed-template-ref')+1])
    wrong=expected(m['root'],m['output_root'],dict(sorted(r.items())),template,m['component_refs'])
    assert commands['model']!=wrong['model'] and commands['CPU']!=wrong['CPU']
    cases.append('actual_expected_reordered_semantic_equal_Ref_breaks_frozen_MODEL_CPU')
    c=copy.deepcopy(commands);c['model'][1]='unreviewed=1';reject(c,'unrelated_actual_argv_mutation_rejected')
    c=copy.deepcopy(commands);c['bind'][-1]='{}';reject(c,'actual_bind_command_change_rejected')
    c=copy.deepcopy(commands)
    for key in ['model','CPU']:
        i=c[key].index('--source-ref')+1;c[key][i]='{"path":"/a","path":"/b","bytes":1,"sha256":"'+'0'*64+'"}'
    reject(c,'duplicate_operand_key_rejected')
    default=subprocess.run([sys.executable,'-I','-B',str(HERE/'bind_source_operand.py')],capture_output=True,text=True,timeout=10)
    assert default.returncode==0 and json.loads(default.stdout)['enabled']is False
    cases.append('default_OFF_no_read_dispatch_or_approval')
    outputs=[]
    if a.real_main_controls:
        for mode in ['reordered','ordered']:
            q=subprocess.run([sys.executable,'-I','-B',__file__,'--one-main',mode],capture_output=True,text=True,timeout=60)
            assert q.returncode==0,(mode,q.stdout,q.stderr)
            outputs.append(json.loads(q.stdout))
        cases.append('actual_original_MAIN_source_inputs_reordered_reject_ordered_PASS')
    print(json.dumps(dict(schema='bole.source-command-operand-controls/v1',status='PASS',
        cases=cases,case_count=len(cases),actual_MAIN_controls=outputs,
        input_refs=[ref(WS/'reduction_admission_prepare_v6_common_20261022T210000Z/CONFIG.ON.actual-v3.json'),cfg['source_ref'],cfg['commands_ref'],m['files']['command_contract.py']],
        NPU=False,commands_executed=False,approvals_written=False),sort_keys=True))

if __name__=='__main__':main()

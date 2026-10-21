"""CPU tensor guard counterexamples; import-safe and never invokes FIA."""
import ast


def run(t,C,reference):
    tree=ast.parse(C.checked(reference).read_bytes())
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='actual_native_fa')
    checks=[n for n in ast.walk(fn)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and
        n.func.attr=='need'and len(n.args)==2 and isinstance(n.args[1],ast.Constant)and
        n.args[1].value=='exact actual full int8 upper2048 template; q1 right-down sees all132 keys']
    C.need(len(checks)==1,'exact production guard AST for counterexamples')
    code=compile(ast.Expression(checks[0].args[0]),reference['path'],'eval')
    def accepts(mask):return bool(eval(code,dict(t=t,mask=mask)))
    good=t.triu(t.ones((2048,2048),dtype=t.int8,device='cpu'),diagonal=1)
    C.need(accepts(good),'exact complete source template positive control')
    rows=[]
    def reject(name,mask):
        C.need(not accepts(mask),'actual full guard must reject '+name);rows.append(dict(name=name,rejected=True))
    reject('bool-dtype',good.bool());reject('uint8-dtype',good.to(t.uint8))
    reject('132-crop',good[:132,:132].contiguous())
    reject('full-lower-triangle',good.T.contiguous())
    reject('noncontiguous-layout',good.T)
    offset=t.zeros(4194305,dtype=t.int8,device='cpu');offset[1:]=good.reshape(-1)
    reject('nonzero-storage-offset',offset[1:].reshape(2048,2048))
    for name,row,col,value in [('far-interior-corruption',1733,1000,1),('far-diagonal-corruption',1733,1733,1),
        ('far-upper-corruption',1,2047,0),('nonbinary-int8',2000,1000,2),('negative-int8',2000,1000,-1)]:
        bad=good.clone();bad[row,col]=value;reject(name,bad)
    return dict(schema='bole.actual-CPU-native-mask-guard-controls/v1',consumer=reference,
        positive_control_pass=True,negative_controls=rows,negative_count=len(rows),
        tested_full2048_mask=True,FIA_operator_executed=False,NPU=False,
        actual_captured_mask_numerics_qualified=False,formal_success=False)

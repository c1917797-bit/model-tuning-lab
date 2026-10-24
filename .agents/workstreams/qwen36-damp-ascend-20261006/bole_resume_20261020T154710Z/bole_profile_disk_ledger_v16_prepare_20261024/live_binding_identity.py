"""Exact original LiveOwner argument repair; all admission predicates stay immutable."""
import ast
def need(v,msg):
 if not v:raise ValueError(msg)
def adapt(files):
 out=dict(files);body=out['service_runner.py'].decode();t=ast.parse(body)
 calls=[n for n in ast.walk(t)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='LiveOwner']
 need(len(calls)==1,'one real LiveOwner construction')
 call=calls[0]
 need(len(call.args)==3 and [ast.unparse(x)for x in call.args]==['runner','bindings','owner'],'exact original three construction operands')
 source=ast.get_source_segment(body,call);changed=source.replace('LiveOwner(runner, bindings, owner,','LiveOwner(runner, bridge.bindings, owner,',1)
 need(changed!=source and body.count(source)==1,'exact one service construction seam')
 bridge=ast.parse(out['model_entry.py'])
 assigns=[n for n in ast.walk(bridge)if isinstance(n,ast.Assign)and any(ast.unparse(k)=='self.bindings'for k in n.targets)]
 need(len(assigns)==1 and ast.unparse(assigns[0].value)=='tuple(bindings)','actual Bridge canonical binding container')
 live=ast.parse(out['live_owner.py'])
 stores=[n for n in ast.walk(live)if isinstance(n,ast.Assign)and any(ast.unparse(k)=='self.bindings'for k in n.targets)]
 need(len(stores)==1 and ast.unparse(stores[0].value)=='bindings','actual LiveOwner retains exact passed container')
 out['service_runner.py']=body.replace(source,changed,1).encode()
 need(all(out[n]==b for n,b in files.items()if n!='service_runner.py'),'only real construction argument changes')
 return out,dict(before=files['service_runner.py'],after=out['service_runner.py'])
def inverse(files,delta):
 out=dict(files);need(out['service_runner.py']==delta['after'],'exact live-binding inverse')
 out['service_runner.py']=delta['before'];return out

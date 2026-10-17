"""Exact typed payload/ancillary command join, before any subprocess."""
import ast,copy,json
from pathlib import PurePosixPath

def need(v,s):
 if not v:raise ValueError(s)

def literal_source(code):
 tree=ast.parse(code);rows=[n for n in ast.walk(tree)if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='sr']
 need(len(rows)==1,'one literal exact cold source assignment')
 sr=ast.literal_eval(rows[0].value)
 need(type(sr)is dict and set(sr)=={'path','bytes','sha256'},'cold Ref3, not Ref2 or dynamic source')
 return tree,rows[0],sr

def path_insert(tree):
 rows=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and ast.unparse(n.func)=='sys.path.insert']
 need(len(rows)==1 and len(rows[0].args)==2 and ast.literal_eval(rows[0].args[0])==0,'one actual cold source bootstrap')
 return rows[0]

def validate(snapshot,sr):
 root=PurePosixPath(sr['path']).parent.as_posix()
 need(PurePosixPath(sr['path']).name=='SOURCE_MANIFEST.json'and PurePosixPath(root).is_absolute(),'exact POSIX payload source')
 p=snapshot['plan'];argv=p['cold_source_tiny_loader_preflight']
 need(snapshot['schema']=='deltalog.firstdecode-owned-cold-plan/v1'and snapshot['payload_source']==p['source']==sr,'top/plan exact new payload Ref')
 need(len(argv)==5 and argv[1:4]==['-I','-B','-c']and p['software']==[argv[0],'-I','-B',root+'/software.py'],'one complete isolated Python command pair')
 tree,assignment,actual=literal_source(argv[-1]);need(actual==sr,'cold executable AST Ref must equal payload/top/plan, not an ancestor')
 need(ast.literal_eval(path_insert(tree).args[1])==root,'cold actual import root equals exact source root')
 need(p['RO_roots'].count(root)==1 and p['environment']=={'TORCH_DEVICE_BACKEND_AUTOLOAD':'0'},'source RO root and exact no-autoload CPU environment')
 need("assert R.STATE_LIMIT == 7.92e-07 and R.OUTPUT_LIMIT == 0.00303"in ast.unparse(tree),'old independent numerical limits retained')
 return dict(source=sr,root=root,cold_argv=argv,software_argv=p['software'],qualified=False,NPU=False)

def rebind(snapshot,old,new):
 out=copy.deepcopy(snapshot);p=out['plan'];need(out['payload_source']==p['source']==old,'actual reviewed old top/plan source')
 oldroot=PurePosixPath(old['path']).parent.as_posix();newroot=PurePosixPath(new['path']).parent.as_posix()
 oldcode=p['cold_source_tiny_loader_preflight'][-1];before,assignment,stale=literal_source(oldcode)
 need(stale['path']==old['path'],'only the proven stale identity at the actual old path is repaired')
 insert=path_insert(before);need(ast.literal_eval(insert.args[1])==oldroot,'actual original source bootstrap')
 after=copy.deepcopy(before);_,row,_=literal_source(ast.unparse(after));newnode=ast.parse(repr(new),mode='eval').body
 row=next(n for n in ast.walk(after)if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='sr');row.value=newnode
 path_insert(after).args[1]=ast.Constant(newroot)
 inverse=copy.deepcopy(after);row=next(n for n in ast.walk(inverse)if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='sr');row.value=copy.deepcopy(assignment.value);path_insert(inverse).args[1]=copy.deepcopy(insert.args[1])
 need(ast.dump(inverse,include_attributes=False)==ast.dump(before,include_attributes=False),'entire cold-program AST inverse; only sr/import-root changes')
 p['cold_source_tiny_loader_preflight'][-1]=ast.unparse(ast.fix_missing_locations(after))+'\n'
 p['source']=out['payload_source']=new;p['software'][-1]=newroot+'/software.py';p['RO_roots']=[newroot if x==oldroot else x for x in p['RO_roots']]
 p['note']=p['note'].replace('Mandatory22','Mandatory26')
 validate(out,new)
 return out,dict(original_embedded_source=stale,top_original_source=old,new_source=new,entire_cold_AST_inverse=True,math_limits_unchanged=True)

"""Private original Joint/controller/contract reuse. Never a new scheduler."""
import ast,copy,hashlib,types
from pathlib import Path
CUT=1792002456
CONTRACT_SHA='7789d63886da0ebe9420b0f56b584c81eae9e50ab561dbf64940df37eb31aa6a'
HOST_SHA='6414c912b216f3896a21e7b321717b604c4be7db21220ed034a798da460a0be8'
FLAGS=('QWEN36_KIVI_WRITER_CHANNEL32','QWEN36_KIVI_DIRECT_FP32_FULL_GRAPH','QWEN36_KIVI_PACKED_QKAV_SOURCE_CANDIDATE','QWEN36_KIVI_DIRECT_D8_FP32_MODEL_WIRE')
def need(v,m):
 if not v:raise ValueError(m)
def private_contract(B,raw,root,refs,devices):
 need(hashlib.sha256(raw).hexdigest()==CONTRACT_SHA,'whole original contract pin')
 chosen={'labels','create_argv','inspect_owned'}
 ns=dict(vars(B),ROOT=Path(root),OWNER='ascend-disjoint-diagnostic-r156',CUTOFF=CUT,devices=devices)
 def environment(service,leaf):
  value=B.environment(service,leaf)
  if leaf.name in('physical-single','physical-active'):value.update({f:'1'for f in FLAGS})
  return value
 ns['environment']=environment
 parsed=ast.parse(raw);body=[n for n in parsed.body if isinstance(n,ast.FunctionDef)and n.name in chosen]
 need({n.name for n in body}==chosen,'original complete create/inspect/labels bodies')
 exec(compile(ast.Module(body=body,type_ignores=[]),str(B.__file__),'exec',dont_inherit=True),ns)
 C=types.SimpleNamespace(**vars(B));C.ROOT=Path(root);C.CUTOFF=CUT;C.OWNER=ns['OWNER'];C.environment=environment;C.devices=devices
 for name in chosen:setattr(C,name,ns[name])
 C.input_refs=lambda unused:refs
 return C
def owner_name(source,output,leaf,card):
 need(card is None or type(card)is int and card in(4,5,6,7),'only Devices[]/one physical4..7')
 seed='\0'.join((source['sha256'],str(output),str(leaf),str(card)))
 return 'kivi-fp32graph-r156-'+hashlib.sha256(seed.encode()).hexdigest()[:40]+('-cpu'if card is None else'-'+str(card))
def controller_tree(raw):
 need(hashlib.sha256(raw).hexdigest()==HOST_SHA,'whole original Joint/controller source')
 original=ast.parse(raw);tree=copy.deepcopy(original);changes=[]
 class Adapt(ast.NodeTransformer):
  def visit_Assign(self,n):
   target=ast.unparse(n.targets[0])if len(n.targets)==1 else''
   if target=='self.name'and 'kivi-packed3-'in ast.unparse(n.value):
    changes.append((copy.deepcopy(n),ast.parse('self.name=owner_name(co.own,co.out,leaf,card)').body[0]));return copy.deepcopy(changes[-1][1])
   return self.generic_visit(n)
 tree=Adapt().visit(tree);need(len(changes)==1,'only per-stage source-aware name seam; original Joint explicit started argument retained')
 inverse=copy.deepcopy(tree)
 class Undo(ast.NodeTransformer):
  def visit_Assign(self,n):
   for old,new in changes:
    if ast.dump(n,include_attributes=False)==ast.dump(new,include_attributes=False):return copy.deepcopy(old)
   return self.generic_visit(n)
 need(ast.dump(Undo().visit(inverse),include_attributes=False)==ast.dump(original,include_attributes=False),'complete inverse AST; every resource/inspect/proc/stop-retain guard unchanged')
 keep={'utc','helper','closure_mounts','Joint','controller'}
 body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))and not(isinstance(n,ast.Import)and any(x.name in('once_contract','safety_lifecycle')for x in n.names))]
 body +=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name in keep]
 return cohort_tree(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])))
def bind(B,L,host_ref,raw,C,started):
 ns=dict(__name__='_direct_fp32graph_actual_controller',__file__=host_ref['path'],C=C,L=L,phase_started=started,owner_name=owner_name)
 exec(compile(controller_tree(raw),host_ref['path'],'exec',dont_inherit=True),ns)
 return ns

def cohort_tree(tree):
 """Bounded actual donor method seams. Original current-card logic retained."""
 joint=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Joint')
 methods={n.name:n for n in joint.body if isinstance(n,ast.FunctionDef)}
 methods['__init__'].body.insert(0,ast.parse('COHORT_SHARED.attach(self)').body[0])
 obs=methods['observe']
 loops=[n for n in obs.body if isinstance(n,ast.For)and ast.unparse(n.target)=='card']
 need(len(loops)==1 and ast.unparse(loops[0].iter)=='(4, 5, 6, 7)','exact full4 observation loop')
 loops[0].body.insert(1,ast.parse("if card != ctl.card:\n self.cohort.observe_other(ctl,card,live,record)\n continue").body[0])
 protected=[i for i,n in enumerate(obs.body)if isinstance(n,ast.Assign)and ast.unparse(n.targets[0])=="record['protected_boundary']"]
 need(len(protected)==1,'original protected0..3 boundary')
 obs.body.insert(protected[0]+1,ast.parse("record['cohort_protected']=self.cohort.protected(record['protected0_3'])").body[0])
 fd=[n for n in obs.body if isinstance(n,ast.For)and ast.unparse(n.target)=='fd']
 need(len(fd)==1 and len(fd[0].body)==1 and 'real foreign device FD/UDA'in ast.unparse(fd[0]),'original FD seam')
 fd[0].body=[ast.parse('self.cohort.fd(ctl,fd,record)').body[0]]
 returns=[n for n in methods['resources'].body if isinstance(n,ast.Return)]
 need(len(returns)==1 and isinstance(returns[0].value,ast.Call),'one resource report')
 returns[0].value.keywords.append(ast.keyword(arg='cohort_resources',value=ast.parse('self.cohort.resource_check(self)',mode='eval').body))
 factory=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='controller')
 owned=next(n for n in factory.body if isinstance(n,ast.ClassDef)and n.name=='Owned')
 methods={n.name:n for n in owned.body if isinstance(n,ast.FunctionDef)}
 methods['begin'].body.insert(1,ast.parse('self.co.cohort.before_begin(self,label,args)').body[0])
 tried=next(n for n in methods['cleanup'].body if isinstance(n,ast.Try))
 loops=[n for n in tried.body if isinstance(n,ast.For)and ast.unparse(n.target)=='card']
 need(len(loops)==1 and ast.unparse(loops[0].iter)=='(4, 5, 6, 7)','only final whole4 idle loop')
 loops[0].iter=ast.parse('((self.card,) if self.card is not None else ())',mode='eval').body
 tried.body.append(ast.parse("self.co.cohort.released(self,raw['stdout'],result)").body[0])
 return ast.fix_missing_locations(tree)

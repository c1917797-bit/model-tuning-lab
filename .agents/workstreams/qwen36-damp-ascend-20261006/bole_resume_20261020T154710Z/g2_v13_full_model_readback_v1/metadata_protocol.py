"""Explicit stdlib-only final metadata decoder and original protocol tail."""
import ast,copy,hashlib,io,math,pickle,pickletools,stat,sys,zipfile
from pathlib import Path
from types import SimpleNamespace as NS
_DANGEROUS=frozenset(('GLOBAL','STACK_GLOBAL','REDUCE','NEWOBJ','NEWOBJ_EX','BUILD','PERSID','BINPERSID','INST','OBJ','EXT1','EXT2','EXT4','NEXT_BUFFER','READONLY_BUFFER'))
_MEMBERS=frozenset(('archive/data.pkl','archive/.format_version','archive/.storage_alignment','archive/byteorder','archive/version','archive/.data/serialization_id'))
class _MetadataOnlyUnpickler(pickle.Unpickler):
 def find_class(self,module,name):raise ValueError('metadata-only final PT rejects every global: '+module+'.'+name)
 def persistent_load(self,identifier):raise ValueError('metadata-only final PT rejects persistent/storage IDs')
def final_metadata_export(R,raw_ref):
 path=R.checked(raw_ref);before=R.ref(path)
 R.need(before==raw_ref and 0<raw_ref['bytes']<=4*2**20,'exact bounded final metadata PT Ref')
 with zipfile.ZipFile(path,'r')as archive:
  rows=archive.infolist()
  R.need(len(rows)==len({v.filename for v in rows})==6 and {v.filename for v in rows}==_MEMBERS and not archive.comment,'exact six-member final metadata archive; no extra/storage entries')
  R.need(sum(v.file_size for v in rows)<=4*2**20,'bounded complete metadata archive expansion')
  for item in rows:
   R.need(not item.is_dir()and not stat.S_ISLNK(item.external_attr>>16)and not(item.flag_bits&1)and item.compress_type==zipfile.ZIP_STORED and item.compress_size==item.file_size and 0<=item.file_size<=4*2**20,'plain unencrypted uncompressed regular metadata member')
  data={item.filename:archive.read(item)for item in rows}
 R.need(data['archive/byteorder']in(b'little',b'big')and len(data['archive/.data/serialization_id'])==40 and data['archive/.data/serialization_id'].isdigit(),'bounded native archive scalar markers')
 for key in('archive/.format_version','archive/.storage_alignment','archive/version'):
  marker=data[key].strip();R.need(0<len(marker)<=16 and marker.isdigit()and int(marker)>0,'positive bounded archive version/alignment marker')
 wire=data['archive/data.pkl'];ops=list(pickletools.genops(wire))
 R.need(ops and ops[-1][0].name=='STOP'and ops[-1][2]+1==len(wire)and all(op.name not in _DANGEROUS for op,arg,pos in ops),'complete literal-only pickle; every global/reduce/object/storage operation refused')
 for op,arg,pos in ops:
  if op.name=='PROTO':R.need(type(arg)is int and 0<=arg<=5,'supported literal pickle protocol')
 stream=io.BytesIO(wire);value=_MetadataOnlyUnpickler(stream).load();R.need(stream.tell()==len(wire),'no trailing metadata pickle bytes')
 seen=set();active=set();nodes=[0]
 def visit(v,depth):
  nodes[0]+=1;R.need(depth<=128 and nodes[0]<=1000000,'bounded final metadata tree depth/nodes');typ=type(v)
  if typ in(str,int,bool,type(None)):return
  if typ is float:R.need(math.isfinite(v),'finite final metadata scalar');return
  R.need(typ in(dict,list,tuple),'final metadata has only original primitive/container types');identity=id(v);R.need(identity not in active,'no cyclic metadata object graph')
  if identity in seen:return
  seen.add(identity);active.add(identity)
  if typ is dict:
   for k,x in v.items():R.need(type(k)in(str,int),'only exact str/int metadata mapping keys; no bool-as-int key');visit(k,depth+1);visit(x,depth+1)
  else:
   for x in v:visit(x,depth+1)
  active.remove(identity)
 visit(value,0)
 R.need(type(value)is dict and type(value.get('logical_tensor_bytes'))is int and value['logical_tensor_bytes']==0 and type(value.get('payload'))is dict,'actual final export is bounded zero-tensor metadata payload')
 R.need(R.ref(path)==before,'complete final metadata PT unchanged during decoding')
 return value,dict(raw_ref=raw_ref,metadata_pickle_bytes=len(wire),metadata_pickle_sha256=hashlib.sha256(wire).hexdigest(),archive_members=sorted(_MEMBERS),dangerous_pickle_operations=[],logical_tensor_bytes=0,tensor_storage_members=0,decoded_nodes=nodes[0],Torch_imported=False,raw_numerical_replayed=False)
def observed_original_reads(R,modules,action):
 R.need(sys.getprofile()is None,'fresh independent metadata profiler');checks=set();refs=set()
 for module in modules:
  for name,target in(('checked',checks),('ref',refs)):
   fn=getattr(module,name,None);R.need(callable(fn)and hasattr(fn,'__code__'),'actual original metadata Ref function '+name);target.add(fn.__code__)
 def observe(frame,event,returned):
  if event!='return'or returned is None:return
  if frame.f_code in checks:
   operand=frame.f_locals[frame.f_code.co_varnames[0]];R.need(Path(returned)==R.checked(operand),'original checked return exactly joins recorded fullRef')
  elif frame.f_code in refs:R.checked(returned)
 sys.setprofile(observe)
 try:return action()
 finally:sys.setprofile(None)
def original_protocol(R,m,C,G1,G2,CH,O,coverage):
 for module,name in((C,'contract090.py'),(G1,'g1_contract.py'),(G2,'g2_contract.py'),(CH,'g2_channel.py'),(O,'identity_oracle.py'),(coverage,'g2_coverage.py')):
  R.need(R.ref(module.__file__)==m['files'][name],'actual complete original protocol module '+name)
 reference=m['files']['g2_finalize.py'];text=R.checked(reference).read_text();tree=ast.parse(text)
 def function(name):
  rows=[v for v in tree.body if isinstance(v,ast.FunctionDef)and v.name==name];R.need(len(rows)==1 and not rows[0].decorator_list,'one undecorated original function '+name);return rows[0]
 identity=function('identity_join');finalize=function('finalize')
 R.need([x.arg for x in identity.args.args]==['sr','bundle']and [x.arg for x in finalize.args.args]==['t','sr','bundle'],'actual original pure-function signatures')
 starts=[i for i,n in enumerate(finalize.body)if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='exit_ref'];R.need(len(starts)==1,'one exact original metadata tail boundary');start=starts[0];original_tail=copy.deepcopy(finalize.body[start:])
 original_load=ast.parse("exported=t.load(C.checked(entry['raw']),map_location='cpu',weights_only=False)").body[0];replacement=ast.parse("exported=metadata_exports[rank]").body[0];before_dump=ast.dump(original_load,include_attributes=False)
 class ReplaceLoad(ast.NodeTransformer):
  count=0
  def visit_Assign(self,node):
   if ast.dump(node,include_attributes=False)==before_dump:self.count+=1;return ast.copy_location(copy.deepcopy(replacement),node)
   return self.generic_visit(node)
 transform=ReplaceLoad();tail_module=transform.visit(ast.Module(body=copy.deepcopy(original_tail),type_ignores=[]));R.need(transform.count==1,'only the unique original final metadata PT-load assignment replaced')
 R.need(not any(isinstance(n,ast.Name)and n.id=='t'for n in ast.walk(tail_module)),'no Torch facade or other unresolved tensor operation in selected metadata tail')
 replacement_dump=ast.dump(replacement,include_attributes=False)
 class RestoreLoad(ast.NodeTransformer):
  count=0
  def visit_Assign(self,node):
   if ast.dump(node,include_attributes=False)==replacement_dump:self.count+=1;return ast.copy_location(copy.deepcopy(original_load),node)
   return self.generic_visit(node)
 inverse=RestoreLoad();restored=inverse.visit(copy.deepcopy(tail_module))
 R.need(inverse.count==1 and ast.dump(restored,include_attributes=False)==ast.dump(ast.Module(body=original_tail,type_ignores=[]),include_attributes=False),'complete original finalize metadata tail AST inverse')
 prefix=ast.parse("m=C.obj(sr)\ncr=bundle['channel']\nroot=Path(channel['root'])").body
 adapted=ast.FunctionDef(name='metadata_finalize_protocol',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=x)for x in('sr','bundle','channel','metadata_exports','commands')],vararg=None,kwonlyargs=[],kw_defaults=[],kwarg=None,defaults=[]),body=prefix+tail_module.body,decorator_list=[],returns=None,type_comment=None)
 module_tree=ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(identity),adapted],type_ignores=[]))
 scope=dict(C=C,G1=G1,G2=G2,CH=CH,Path=Path,CM=NS(O=O,PROFILE=dict(endpoint='/v1/completions',prompt_count=1,n=1,beam_search=False,streaming_input=False)))
 exec(compile(module_tree,reference['path']+'#explicit-stdlib-metadata-tail','exec'),scope)
 dump=lambda nodes:ast.dump(ast.Module(body=nodes,type_ignores=[]),include_attributes=False)
 proof=dict(schema='bole.exact-original-finalizer-metadata-tail-adapter/v1',original_finalizer_ref=reference,identity_join_original_AST=ast.dump(identity,include_attributes=False),excluded_original_preamble_AST=dump(finalize.body[:start]),original_metadata_tail_AST=dump(original_tail),adapted_metadata_tail_AST=dump(tail_module.body),adapter_prefix_AST=dump(prefix),original_PT_load_AST=before_dump,replacement_PT_load_AST=replacement_dump,original_tail_start_line=finalize.body[start].lineno,identity_join_original=True,tail_whole_AST_inverse=True,PT_load_replacements=1,owned_channel_reexecuted=False,image_only_runtime_paths_reopened=False,numerical_raw_replayed=False,live_identity_reobserved=False)
 return scope['metadata_finalize_protocol'],proof

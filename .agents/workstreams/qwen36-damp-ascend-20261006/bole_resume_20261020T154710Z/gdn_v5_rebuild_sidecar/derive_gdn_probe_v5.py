#!/usr/bin/env python3
"""Default-OFF pure source derivation: GDN v5 literal qualified IO and assembled checks."""
import argparse,ast,hashlib,json,os,shutil,textwrap
from pathlib import Path
BUILDER_SHA='e38dcf3bd1b638fc63d200eb68bb06d28b1597b348e51099cbeae2a5e028583b'
BAD_IO_SHA='0bd97743aa2ac06ea55488a54f5045fd08cff2fdfa4869acc9b1414d2965a0cd'
EXPECTED={
 'core112.py':(1443,'b7e3f3a91889e98c54195a0c5f5eb2a4c6cdf8fc9c667ece26d7250b3e6eebe7'),
 'oracle112.py':(774,'6ba6709289ee37cf54c13faf0bff43f361f06276049774bc3b1cd58456aa3a70'),
 'independent_model.py':(14336,'cdffc7dcb59b744788c2b736a5607e7218a9e13595b0f6a7d10f450a4fb6ad72'),
 'sourceio.py':(1037,'332c4bec18d5e82a19bf807b96397b76a7d95f4dae168b881379cabfc3a8d78d')}
def need(ok,message):
 if not ok:raise ValueError(message)
def ref(path):
 p=Path(path).absolute();s=p.stat();h=hashlib.sha256();n=0
 need(p.is_file()and not p.is_symlink(),'ordinary exact source')
 with p.open('rb')as f:
  a=os.fstat(f.fileno());need((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns),'opened source identity')
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b);n+=len(b)
  z=os.fstat(f.fileno())
 q=p.stat();need((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)==(q.st_dev,q.st_ino,q.st_size,q.st_mtime_ns),'stable whole source')
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def checked_arg(value):
 r=json.loads(value);need(type(r)is dict and set(r)=={'path','bytes','sha256'}and ref(r['path'])==r,'actual complete Ref3');return r
def obj(r):
 need(r['bytes']<=4*2**20,'bounded metadata');b=Path(r['path']).read_bytes();need(len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'exact metadata reopen');return json.loads(b)
def write(path,value):
 with Path(path).open('xb')as f:f.write((json.dumps(value,sort_keys=True,indent=2)+'\n').encode())
 return ref(path)
def subscript(node,name,key):
 return isinstance(node,ast.Subscript)and isinstance(node.value,ast.Name)and node.value.id==name and isinstance(node.slice,ast.Constant)and node.slice.value==key
def main():
 p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
 p.add_argument('--derive',action='store_true');p.add_argument('--v4-packet',type=Path);p.add_argument('--new-packet',type=Path)
 for name in('v4-source-ref-json','v4-sidecar-ref-json','v4-result-ref-json'):p.add_argument('--'+name)
 a=p.parse_args()
 if not a.derive:print('{"enabled":false,"resources_admitted":false,"formal_success":false}');return 0
 need(all(v is not None for v in(a.v4_packet,a.new_packet,a.v4_source_ref_json,a.v4_sidecar_ref_json,a.v4_result_ref_json)),'all exact source inputs required')
 old=a.v4_packet.absolute();new=a.new_packet.absolute()
 need(old.is_dir()and not old.is_symlink()and not new.exists()and new.parent.is_dir(),'new packet leaf only')
 oldbuilder=ref(old/'prepare_gdn_probe.py');need(oldbuilder['bytes']==15140 and oldbuilder['sha256']==BUILDER_SHA,'exact actual v4 builder15140')
 authority=checked_arg(a.v4_source_ref_json);sidecar=checked_arg(a.v4_sidecar_ref_json);failed=checked_arg(a.v4_result_ref_json)
 need(authority['bytes']==112215 and authority['sha256']=='9f4e1a0535aa5279a07135ebd33ceadf0fa321ace6ee869bccc71caf98a57e1f','actual v4 source authority')
 need(sidecar['bytes']==7448 and sidecar['sha256']=='a1b9f6417712d3bad8e78f45e9d9651c3bd45984f6374ac163053c620411ab36','actual v4 derivation authority')
 need(failed['bytes']==234588 and failed['sha256']=='cc4dfb43df0a6c303906b306c9bfd9412fef134cb985c6330dad0bb31f340c85','preserved failed v4 producer')
 source=obj(authority);parent_io=source['files']['sourceio.py']
 need(ref(parent_io['path'])==parent_io and(parent_io['bytes'],parent_io['sha256'])==(1038,BAD_IO_SHA),'actual v4 IO1038 unchanged')
 executed_sidecar=ref(__file__);raw=(old/'prepare_gdn_probe.py').read_bytes();tree=ast.parse(raw)
 mains=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main'];need(len(mains)==1,'unique original main')
 body=mains[0].body;lines=raw.splitlines(keepends=True);starts=[0]
 for line in lines:starts.append(starts[-1]+len(line))
 def one(items,label):need(len(items)==1,'unique AST anchor '+label);return items[0]
 replay_call=one([n for n in body if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Attribute)and isinstance(n.value.func.value,ast.Name)and n.value.func.value.id=='G'and n.value.func.attr=='replay_contract'],'original replay_contract')
 added_loop=one([n for n in body if isinstance(n,ast.For)and isinstance(n.iter,ast.Name)and n.iter.id=='ADDED'],'ADDED source-copy loop')
 files_update=one([n for n in body if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Attribute)and n.value.func.attr=='update'and subscript(n.value.func.value,'m','files')],'m.files.update')
 dependencies=one([n for n in body if isinstance(n,ast.AugAssign)and subscript(n.target,'m','dependencies')and isinstance(n.op,ast.Add)],'original dependency extension')
 bound=one([n for n in body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='bound'for t in n.targets)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Name)and n.value.func.id=='obj'],'actual bound=obj(sr)')
 operations=[];main_indent=body[0].col_offset;need(main_indent==4,'actual original main top-level indentation4')
 def after(node,tag,text):
  need(any(node is item for item in body),'after target is direct main statement')
  block='\n# BEGIN '+tag+'\n'+textwrap.dedent(text).strip('\n')+'\n# END '+tag+'\n'
  block=textwrap.indent(block,' '*main_indent).encode();operations.append((starts[node.end_lineno],block,tag))
 operations.append((starts[replay_call.lineno-1]+replay_call.col_offset,b'_bgv5_helper,_bgv5_replay=','GDN_V5_CAPTURE_VERIFIED_REPLAY'))
 copy_block=r'''
 _bgv5_expected=__EXPECTED__
 def _bgv5_refs(value):
     if type(value)is dict:
         if set(value)=={'path','bytes','sha256'}:yield value
         else:
             for child in value.values():yield from _bgv5_refs(child)
     elif type(value)is list:
         for child in value:yield from _bgv5_refs(child)
 _bgv5_qualified={}
 for _bgv5_name,_bgv5_content in _bgv5_expected.items():
     _bgv5_candidates={r['path']:r for r in _bgv5_refs(_bgv5_replay['references'])
         if Path(r['path']).name==_bgv5_name and(r['bytes'],r['sha256'])==tuple(_bgv5_content)}
     need(len(_bgv5_candidates)==1,'unique original qualified full Ref3 '+_bgv5_name)
     _bgv5_qualified[_bgv5_name]=next(iter(_bgv5_candidates.values()))
     checked(_bgv5_qualified[_bgv5_name])
 _bgv5_parent_io=on['files']['sourceio.py']
 need((_bgv5_parent_io['bytes'],_bgv5_parent_io['sha256'])==(1038,'__BAD_IO_SHA__'),'original parent IO1038 whole source')
 _bgv5_parent_bytes=checked(_bgv5_parent_io).read_bytes()
 _bgv5_qualified_bytes=checked(_bgv5_qualified['sourceio.py']).read_bytes()
 need((new/'sourceio.py').read_bytes()==_bgv5_parent_bytes,'unsealed new IO is exact parent copy')
 need(_bgv5_parent_bytes==_bgv5_qualified_bytes+b'\n','exact one-LF inverse, no semantic replacement')
 need(not(new/'SOURCE_BOUND.json').exists(),'literal IO copy before source sealing')
 shutil.copyfile(checked(_bgv5_qualified['sourceio.py']),new/'sourceio.py')
 need((new/'sourceio.py').read_bytes()==_bgv5_qualified_bytes,'whole qualified IO copy; no newline normalization')
 checked(_bgv5_qualified['sourceio.py']);checked(_bgv5_parent_io)
 def _bgv5_check_files(files):
     rows={};bad=[]
     for name,expected in _bgv5_qualified.items():
         actual=ref(new/name);declared=files[name]
         equal=declared==actual and(actual['bytes'],actual['sha256'])==(expected['bytes'],expected['sha256'])
         rows[name]=dict(qualified=expected,assembled=actual,manifest_ref=declared,equal=equal)
         if not equal:bad.append(name)
     need(not bad,'all assembled qualified mathematical bytes unchanged: '+repr(rows))
     return rows
 '''.replace('__EXPECTED__',repr(EXPECTED)).replace('__BAD_IO_SHA__',BAD_IO_SHA)
 after(added_loop,'GDN_V5_LITERAL_QUALIFIED_IO',copy_block)
 preseal_block=r'''
 need(m['service_required_sameimage_software_cases']==240,'unchanged CPU240; source checks counted separately')
 _bgv5_pre_rows=_bgv5_check_files(m['files'])
 _bgv5_pre_ref=write(new/'GDN_ASSEMBLED_MATH_V5.json',dict(schema='bole.gdn-assembled-qualified-math-source/v1',
     mode=a.mode,qualified_replay=replay,files=_bgv5_pre_rows,all_four_equal=True,
     source_only=True,software_cases_unchanged=240,model_qualified=False,formal_success=False))
 '''
 cases_assign=one([n for n in body if isinstance(n,ast.Assign)and any(subscript(t,'m','service_required_sameimage_software_cases')for t in n.targets)],'original software total assignment')
 need(files_update.end_lineno<=cases_assign.lineno,'files updated before original software total')
 after(cases_assign,'GDN_V5_ASSEMBLED_PRESEAL_CHECK',preseal_block)
 authorities=dict(parent_v4_source=authority,parent_v4_sidecar=sidecar,failed_v4_result=failed,original_builder=oldbuilder,deriver_execution=executed_sidecar)
 descriptor_block=r'''
 _bgv5_authorities=__AUTHORITIES__
 m['gdn_literal_qualified_io_v5']=dict(schema='bole.gdn-literal-qualified-IO-copy/v1',
     qualified_sources=_bgv5_qualified,parent_service_io=_bgv5_parent_io,actual_sourceio=m['files']['sourceio.py'],
     exact_single_LF_inverse_verified=True,source_wholecopy=True,assembled_four_source_proof=_bgv5_pre_ref,
     derivation_authorities=_bgv5_authorities,old_failed_v4_promoted=False,
     gate_seam_kernel_host_observer_unchanged=True,required_sameimage_software_cases=240,
     additional_source_checks_are_not_software_case_count=True,model_qualified=False,formal_success=False)
 m['dependencies'] += [*_bgv5_qualified.values(),_bgv5_parent_io,_bgv5_pre_ref,*_bgv5_authorities.values()]
 '''.replace('__AUTHORITIES__',repr(authorities))
 after(dependencies,'GDN_V5_LITERAL_IO_DESCRIPTOR',descriptor_block)
 postbound_block=r'''
 _bgv5_post_rows=_bgv5_check_files(bound['files'])
 need(bound['service_required_sameimage_software_cases']==240,'bound source retains CPU240')
 write(new/'GDN_POSTBOUND_MATH_V5.json',dict(schema='bole.gdn-postbound-qualified-math-source/v1',
     bound_source=sr,template=tr,preseal_proof=_bgv5_pre_ref,files=_bgv5_post_rows,all_four_equal=True,
     source_only=True,required_sameimage_software_cases=240,model_qualified=False,formal_success=False))
 '''
 after(bound,'GDN_V5_POSTBOUND_CHECK',postbound_block)
 operations.sort(key=lambda item:item[0]);need(len(operations)==5,'five declared insertions only')
 need(len({item[0]for item in operations})==5,'distinct exact source positions')
 parts=[];cursor=0;size=0;ledger=[]
 for offset,inserted,tag in operations:
  need(cursor<=offset<=len(raw),'ordered original byte offset');prefix=raw[cursor:offset];parts.append(prefix);size+=len(prefix)
  ledger.append(dict(tag=tag,original_byte_offset=offset,new_byte_offset=size,inserted_utf8=inserted.decode('utf-8')))
  parts.append(inserted);size+=len(inserted);cursor=offset
 parts.append(raw[cursor:]);derived=b''.join(parts);compile(derived,str(new/'prepare_gdn_probe.py'),'exec');restored=derived
 for item in reversed(ledger):
  offset=item['new_byte_offset'];inserted=item['inserted_utf8'].encode('utf-8')
  need(restored[offset:offset+len(inserted)]==inserted,'exact declared inverse span');restored=restored[:offset]+restored[offset+len(inserted):]
 need(restored==raw and len(restored)==15140 and hashlib.sha256(restored).hexdigest()==BUILDER_SHA,'whole original builder byte inverse')
 for item in old.rglob('*'):need(not item.is_symlink(),'ordinary source packet, no symlink copy')
 shutil.copytree(old,new,ignore=shutil.ignore_patterns('__pycache__','*.pyc'));(new/'prepare_gdn_probe.py').write_bytes(derived);copied={}
 for src in old.rglob('*'):
  if not src.is_file()or '__pycache__'in src.parts or src.suffix=='.pyc':continue
  rel=src.relative_to(old)
  if str(rel)=='prepare_gdn_probe.py':continue
  before=ref(src);actual=ref(new/rel);need((before['bytes'],before['sha256'])==(actual['bytes'],actual['sha256']),'all other packet bytes unchanged: '+str(rel));copied[str(rel)]=dict(before=before,after=actual)
 for path in new.rglob('*.py'):compile(path.read_bytes(),str(path),'exec')
 inherited_manifest=None
 if(new/'MANIFEST.json').exists():
  target=new/'INHERITED_V4_MANIFEST_DO_NOT_USE.json';need(not target.exists(),'unique inherited metadata name')
  (new/'MANIFEST.json').rename(target);inherited_manifest=ref(target)
  if 'MANIFEST.json'in copied:copied['MANIFEST.json']['after']=inherited_manifest
 proof=write(new/'V5_DERIVATION.json',dict(schema='bole.gdn-probe-literal-IO-builder-derivation/v1',authorities=authorities,original_builder=oldbuilder,derived_builder=ref(new/'prepare_gdn_probe.py'),insertions=ledger,whole_builder_inverse_pass=True,unchanged_packet_files=copied,qualified_expected_content={k:dict(bytes=v[0],sha256=v[1])for k,v in EXPECTED.items()},runtime_IO_copy_is_prospective_until_preparation=True,unchanged_software_cases=240,no_other_runtime_source_change_requested=True,resources_admitted=False,model_qualified=False,formal_success=False))
 files={str(path.relative_to(new)):ref(path)for path in new.rglob('*')if path.is_file()and '__pycache__'not in path.parts and path.suffix!='.pyc'}
 manifest=write(new/'MANIFEST.json',dict(schema='bole.gdn-probe-literal-IO-v5-packet/v1',files=files,derivation=proof,inherited_v4_manifest=inherited_manifest,actual_deriver_execution=executed_sidecar,prepared_only=True,resources_admitted=False,actual_source_prepare_pass=False,actual_CPU240_pass=False,actual_model_pass=False,formal_success=False))
 print(json.dumps(dict(packet=str(new),manifest=manifest,derivation=proof,builder=ref(new/'prepare_gdn_probe.py'),whole_builder_inverse_pass=True,resources_admitted=False,actual_source_prepare_pass=False,formal_success=False),sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())

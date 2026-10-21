"""Source-bound relocation of the unchanged HTTP producer into its shared channel."""
import ast,copy,hashlib
from pathlib import Path
SOURCE12=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v12/SOURCE_BOUND.json',bytes=908497,sha256='6c925c8e827b4761926645b89c5897ef25d7e81a80664cb4b4def75076c05d15')
HOST_REF=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v12/host_service.py',bytes=16149,sha256='f056b4e7a579aa48d755c0466bbfb318d496703fa700dc9f64dcd506cbe328df')
FINALIZER_BYTES=17504
FINALIZER_SHA='8d8b3a9af2c069792a3d923af0a43ff6ba7b8e4effba5681a17cdfb2bbcccfda'
OLD_CLIENT="ctl.client,ctl.client_argv=spawn(ctl,[str(P/'service_client.py'),'--execute','--source-ref',json.dumps(sr),'--output',str(ctl.out)],'model-smoke')"
NEW_CLIENT="ctl.client,ctl.client_argv=spawn(ctl,[str(P/'service_client.py'),'--execute','--source-ref',json.dumps(sr),'--output',str(channelroot)],'model-smoke')"
OLD_HTTP="http_ref=C.ref(ctl.out/'HTTP_RESULT.json');http=C.obj(http_ref);response=C.obj(http['rows'][0]['response'])"
NEW_HTTP="http_ref=C.ref(channelroot/'HTTP_RESULT.json');http=C.obj(http_ref);response=C.obj(http['rows'][0]['response'])"
def need(ok,why):
 if not ok:raise ValueError(why)
def _hash(text):
 raw=text.encode('utf-8');return len(raw),hashlib.sha256(raw).hexdigest()
def _replace_once(text,a,b):
 need(text.count(a)==1,'one exact source-owned HTTP route anchor');return text.replace(a,b)
def _base(text):
 need(type(text)is str and _hash(text)==(HOST_REF['bytes'],HOST_REF['sha256']),'exact actual v12 host whole source')
def patch_host(text):
 _base(text)
 new=_replace_once(text,OLD_CLIENT,NEW_CLIENT);new=_replace_once(new,OLD_HTTP,NEW_HTTP)
 audit_host(text,new);return new
def audit_host(before,after):
 _base(before);need(type(after)is str,'actual new host source text')
 expected=_replace_once(_replace_once(before,OLD_CLIENT,NEW_CLIENT),OLD_HTTP,NEW_HTTP)
 need(after==expected,'only the two declared producer/readback path changes')
 restored=_replace_once(_replace_once(after,NEW_CLIENT,OLD_CLIENT),NEW_HTTP,OLD_HTTP)
 need(restored==before,'whole-file exact HTTP relocation inverse')
 need(ast.dump(ast.parse(restored),include_attributes=False)==ast.dump(ast.parse(before),include_attributes=False),'whole executable AST inverse')
 need(OLD_CLIENT not in after and OLD_HTTP not in after and after.count(NEW_CLIENT)==1 and after.count(NEW_HTTP)==1,'single actual channel output and matching ledger readback')
 return dict(schema='bole.exact-HTTP-channel-visibility-source-proof/v13',base_source=SOURCE12,original_host_ref=HOST_REF,current_host_bytes=_hash(after)[0],current_host_sha256=_hash(after)[1],changes=[dict(before=OLD_CLIENT,after=NEW_CLIENT),dict(before=OLD_HTTP,after=NEW_HTTP)],whole_file_inverse=True,whole_AST_inverse=True,all_other_host_text_unchanged=True,HTTP_client_and_identity_and_finalizer_changed=False,new_mounts_or_RW_aliases=False,original3072_ACK_cap_unchanged=True,original128_math_unchanged=True,firstclock_requires_original_source_owned_validator=True,actual_HTTP_or_NPU_executed=False,numerical_model_qualification=False)
def metadata_selector(finalizer_text,root,C):
 """Execute original JSON selection only; no full budget or math qualification."""
 need(_hash(finalizer_text)==(FINALIZER_BYTES,FINALIZER_SHA),'unchanged exact v12 finalizer source for selection-only control')
 expected_iter=ast.dump(ast.parse("root.glob('*.json')",mode='eval').body,include_attributes=False)
 expected_key=ast.dump(ast.parse('str(p)',mode='eval').body,include_attributes=False)
 expected_value=ast.dump(ast.parse('C.ref(p)',mode='eval').body,include_attributes=False)
 expected_if=ast.dump(ast.parse("'RANK-'not in p.name",mode='eval').body,include_attributes=False)
 matches=[]
 for n in ast.walk(ast.parse(finalizer_text)):
  if not isinstance(n,ast.DictComp)or len(n.generators)!=1:continue
  g=n.generators[0]
  if isinstance(g.target,ast.Name)and g.target.id=='p'and not g.is_async and len(g.ifs)==1 and ast.dump(g.iter,include_attributes=False)==expected_iter and ast.dump(n.key,include_attributes=False)==expected_key and ast.dump(n.value,include_attributes=False)==expected_value and ast.dump(g.ifs[0],include_attributes=False)==expected_if:matches.append(n)
 need(len(matches)==1,'one exact original finalizer metadata selector')
 expression=ast.fix_missing_locations(ast.Expression(body=copy.deepcopy(matches[0])))
 code=compile(expression,'g2_finalize.py:original-metadata-selector','eval',dont_inherit=True)
 return eval(code,{'__builtins__':{'str':str},'C':C,'root':Path(root)})
if __name__=='__main__':print('{"enabled":false,"NPU":false}')

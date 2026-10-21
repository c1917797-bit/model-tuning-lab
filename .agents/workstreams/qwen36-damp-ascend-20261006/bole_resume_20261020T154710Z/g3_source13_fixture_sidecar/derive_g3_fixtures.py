
"""Rebase the original32 fixture methods onto actual13 parent metadata gates."""
import argparse,ast,copy,hashlib,json,re,textwrap
from pathlib import Path
T=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
OLD=T/'g3_long_output_v2'
OLD_MANIFEST=dict(path=str(OLD/'MANIFEST.json'),bytes=17849,sha256='f02c246647df27615be5f39c48f485bad9af819ef273bebc6fa9dc123e110095')
SR13=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v13/SOURCE_BOUND.json',bytes=994678,sha256='545e09b8bd8e598830cd81ab2ba3be6c5a6b775d1d35f263ed6d3519a4145345')
TESTS=tuple('test_g3_'+n+'.py'for n in('budget','client','coverage','domain','lifecycle','parent','prepare','tensor_operands'))
PINS={
 'test_g3_parent.py':(3473,'87e1feb7418c90a4b0fa080c142075fd7ff25bf46e2dd647cc48b9bc7a8713ab'),
 'test_g3_prepare.py':(4809,'b4c2ea45586106abe0c3cc1ebff66a1e43b24711c5c5f567692b8227167b7bd1'),
 'test_g3_budget.py':(3060,'240647249cbc2dc0f69f15942e73bca312fc12fcc03789b763474436402f5a26'),
 'test_g3_domain.py':(3569,'dcdc61769fe13033db50e66fe40db65858757d5ee5a0bb8de0acc17704023432'),
 'test_g3_client.py':(2480,'67b52a40a994e9476bd6f761cd5ae2cb1e5e356b17a8732e69bee7778c4a2b3c')}
def need(v,s):
 if not v:raise ValueError(s)
def ref(path):
 p=Path(path);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary exact source')
 a=p.stat();b=p.read_bytes();z=p.stat()
 need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)and len(b)==z.st_size,'stable full read')
 return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def obj(r):need(ref(r['path'])==r,'complete exact supplied Ref3');return json.loads(Path(r['path']).read_bytes())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
PARENT_FIXTURE=r'''
def fixture(self,source_changes=None):
    import json
    td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);p=Path(td.name)
    consumer=C.write(p/'CONSUMER.json',dict(synthetic=True))
    channel=C.write(p/'CHANNEL.json',dict(synthetic=True))
    helper=C.write(p/'READER.json',dict(synthetic=True))
    final_inputs=C.write(p/'FINAL-INPUTS.json',dict(synthetic=True))
    m=dict(service_experiment=copy.deepcopy(G.SCOPE),prepared_only=False,default_enabled=False,
        files={'g2_consumer.py':consumer},service_required_sameimage_software_cases=349)
    m.update(source_changes or {})
    sr=C.write(p/'SOURCE.json',m)
    report=dict(schema='bole.actual-G2-stream-attribution/v2',source=sr,scope=m['service_experiment'],
        channel=channel,service_complete=True,completed_request_count=2,component_checks_pass=True,
        scheduler_committed_independently=True,all4_worker_retirement_verified=True,
        every_frame_independently_consumed=True,model_ready=False,successful_raw_replay_available=False,
        ranks=[dict(rank=rank,all_frames_consumed=True,
            coverage_proof=dict(all_coverage=True,complete_output_tokens=8,request_count=2,
                final_pending_by_retirement=True,target_step_count=4),
            final_metadata_bytes=0,slot_reuse_observed=dict(FA=False,GDN=False),
            requests=[dict(generation=generation,request='fixture-%d-%d'%(rank,generation),
                prefix_token_ids=list(range(131)),observation={},steps=2,processed_tokens=3,
                output_token_ids=[7,11,13,17],next_counter_ACKs=1,component_checks_pass=True)
                for generation in(1,2)])for rank in range(4)])
    report.update({key:False for key in G.QFALSE})
    attribution=C.write(p/'ATTRIBUTION.json',report)
    own=C.write(p/'OWNER.json',dict(source=sr,primary=None,secondary=[],source_before={'fixture':'unchanged'},
        source_after={'fixture':'unchanged'},cpu_only=False,summary=dict(independent=attribution)))
    terminal=C.write(p/'UNIT.json',dict(schema='bole.actual-finite-unit-terminal/v1',observed_epoch=0.,
        properties=dict(ActiveState='active',ControlPID='0',ExecMainStatus='0',
            Id='bole-g2-v13-model-20261020t154710z.service',MainPID='0',Restart='no',
            Result='success',SubState='exited',Type='exec')))
    exit_value=dict(schema='bole.actual-stream-consumer-exit/v2',source=sr,channel_ref=channel,
        completed=True,source_unchanged=True,primary=None,traceback=None,actual_frame_batches=9,
        ACKs=[helper for _ in range(36)],requests=[{} for _ in range(4)],consumer_source=consumer)
    exit_value.update({key:False for key in G.QFALSE})
    consumer_exit=C.write(p/'CONSUMER-EXIT.json',exit_value)
    refs=dict(unit_terminal_ref=terminal,original_attribution_ref=attribution,
        finalizer_inputs_ref=final_inputs,consumer_exit_ref=consumer_exit,reader_ref=helper,
        stage_qualification_ref=helper,stage_reader_ref=helper)
    self.assertEqual(set(refs),set(G.QTYPED))
    q=dict(schema='bole.actual-G2-v13-full-MODEL-metadata-independent-qualification/v1',
        source=sr,result_ref=own,source_readset_count=4088,derived_frame_count=36,
        helper_refs=dict(protocol=helper,roles=helper),independent_readback_refs=[consumer,channel,helper],**refs)
    q.update({key:True for key in G.QTRUE});q.update({key:False for key in G.QFALSE})
    rr=C.write(p/'QUALIFICATION.json',q)
    audit=copy.deepcopy(C.obj(G.ACTUAL['source_audit']))
    inner=json.loads(audit['stdout']);inner['source']=sr
    audit['stdout']=json.dumps(inner,sort_keys=True,allow_nan=False)
    ar=C.write(p/'AUDIT.json',audit)
    return p,sr,m,own,rr,ar
'''
PARENT_PENDING=r'''
def test_pending_source_only_CPU_only_or_first_frame_parent_never_admits(self):
    p,sr,m,own,rr,ar=self.fixture()
    with self.assertRaises((ValueError,TypeError)):
        G.qualified(sr,m,None,None,source_audit_ref=ar)
    for field,value in(('prepared_only',True),('service_experiment',dict(m['service_experiment'],max_output_tokens=1024))):
        p,sr,m,own,rr,ar=self.fixture({field:value})
        with self.subTest(field=field),self.assertRaises(ValueError):
            G.qualified(sr,m,own,rr,source_audit_ref=ar)
    p,sr,m,own,rr,ar=self.fixture()
    o=C.obj(own);o['cpu_only']=True;own2=C.write(p/'CPU.json',o)
    q=C.obj(rr);q['result_ref']=own2;rr2=C.write(p/'CPU-QUALIFICATION.json',q)
    with self.assertRaises(ValueError):
        G.qualified(sr,m,own2,rr2,source_audit_ref=ar)
'''
PARENT_LATE=r'''
def test_missing_late_coverage_retirement_or_source_audit_failure_remains_blocking(self):
    import json
    for field in('coverage','retirement','component','audit'):
        p,sr,m,own,rr,ar=self.fixture();q=C.obj(rr);o=C.obj(own)
        report=C.obj(q['original_attribution_ref'])
        if field=='coverage':report['ranks'][3]['coverage_proof']['all_coverage']=False
        elif field=='retirement':report['all4_worker_retirement_verified']=False
        elif field=='component':report['ranks'][2]['requests'][1]['component_checks_pass']=False
        else:
            audit=C.obj(ar);inner=json.loads(audit['stdout'])
            inner['original_math_ACK_cap_argv_transport_resources_unchanged']=False
            audit['stdout']=json.dumps(inner,sort_keys=True,allow_nan=False)
            ar=C.write(p/'AUDIT-FAILED.json',audit)
        attrib2=C.write(p/'ATTRIBUTION-ALTERED.json',report)
        o['summary']['independent']=attrib2;own2=C.write(p/'OWNER-ALTERED.json',o)
        q['original_attribution_ref']=attrib2;q['result_ref']=own2
        rr2=C.write(p/'QUALIFICATION-ALTERED.json',q)
        with self.subTest(field=field),self.assertRaises(ValueError):
            G.qualified(sr,m,own2,rr2,source_audit_ref=ar)
'''
def klass(text,name):
 nodes=[n for n in ast.parse(text).body if isinstance(n,ast.ClassDef)and n.name==name]
 need(len(nodes)==1,'one original fixture class '+name);return nodes[0]
def method(text,classname,name):
 nodes=[n for n in klass(text,classname).body if isinstance(n,ast.FunctionDef)and n.name==name]
 need(len(nodes)==1,'one original method '+classname+'.'+name);return nodes[0]
def full_span(text,node):
 lines=text.splitlines(keepends=True)
 return sum(map(len,lines[:node.lineno-1])),sum(map(len,lines[:node.end_lineno]))
def edit_spans(text,edits):
 last=len(text)
 for start,end,value in sorted(edits,reverse=True):
  need(0<=start<end<=last,'nonoverlapping exact source edits');text=text[:start]+value+text[end:];last=start
 return text

def replace_methods(text,classname,replacements):
 edits=[]
 for name,value in replacements.items():
  node=method(text,classname,name);start,end=full_span(text,node)
  replacement=textwrap.indent(textwrap.dedent(value).strip('\n')+'\n',' '*node.col_offset)
  edits.append((start,end,replacement))
 return edit_spans(text,edits)
def masked(text,classname,names):
 edits=[]
 for name in names:
  node=method(text,classname,name);start,end=full_span(text,node)
  edits.append((start,end,' '*node.col_offset+'# audited replacement '+name+'\n'))
 return edit_spans(text,edits)
def test_methods(text):
 return sorted((n.name,fn.name)for n in ast.parse(text).body if isinstance(n,ast.ClassDef)
  for fn in n.body if isinstance(fn,ast.FunctionDef)and fn.name.startswith('test_'))

def rebase_prepare(text):
 node=method(text,'PrepareTests','fixture')
 parents=[n for n in node.body if isinstance(n,ast.If)and isinstance(n.test,ast.Name)and n.test.id=='parent']
 need(len(parents)==1 and not parents[0].orelse,'one original parent-only command helper selection')
 branch=parents[0];start,end=full_span(text,branch);indent=' '*branch.col_offset
 inner=' '*branch.body[0].col_offset
 branch_new=indent+'if parent:\n'+inner+'import g3_parent as G\n'+inner+"cc=C.checked(C.obj(G.ACTUAL['source'])['files']['command_contract.py'])\n"
 counts=[n for n in ast.walk(node)if isinstance(n,ast.IfExp)and isinstance(n.test,ast.Name)and n.test.id=='parent'and
  isinstance(n.body,ast.Constant)and n.body.value==242 and isinstance(n.orelse,ast.Constant)and n.orelse.value==274]
 need(len(counts)==1,'unique original242/274 synthetic case expression')
 count=counts[0];lines=text.splitlines(keepends=True)
 a=sum(map(len,lines[:count.lineno-1]))+count.col_offset
 z=sum(map(len,lines[:count.end_lineno-1]))+count.end_col_offset
 need(text[a:z]==ast.get_source_segment(text,count),'exact original source interval')
 return edit_spans(text,[(start,end,branch_new),(a,z,'349 if parent else 381')])

def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--prepare',action='store_true');p.add_argument('--new-root',type=Path)
 a=p.parse_args()
 if not a.prepare:print('{"enabled":false,"NPU":false}');return 0
 new=a.new_root;need(new is not None and new.is_absolute()and new.parent==T and new.name.startswith('g3_source13_fixture_layer_')and not new.exists(),'one new exclusive fixture leaf')
 donor=obj(OLD_MANIFEST);obj(SR13);before={};texts={}
 for name in TESTS:
  r=ref(OLD/name);expected=donor['inventory'][name]
  need(Path(expected['path']).name==name and all(r[k]==expected[k]for k in('bytes','sha256')),'whole original donor inventory '+name)
  if name in PINS:need((r['bytes'],r['sha256'])==PINS[name],'additional fixed source pin '+name)
  before[name]=r;texts[name]=(OLD/name).read_text();compile(texts[name],str(OLD/name),'exec')
 newtexts=dict(texts)
 changed_parent={'fixture':PARENT_FIXTURE,
  'test_pending_source_only_CPU_only_or_first_frame_parent_never_admits':PARENT_PENDING,
  'test_missing_late_coverage_retirement_or_source_audit_failure_remains_blocking':PARENT_LATE}
 newtexts['test_g3_parent.py']=replace_methods(texts['test_g3_parent.py'],'ParentTests',changed_parent)
 newtexts['test_g3_prepare.py']=rebase_prepare(texts['test_g3_prepare.py'])
 need(masked(texts['test_g3_parent.py'],'ParentTests',changed_parent)==masked(newtexts['test_g3_parent.py'],'ParentTests',changed_parent),'all parent-test bytes outside explicitly replaced methods unchanged')
 need(masked(texts['test_g3_prepare.py'],'PrepareTests',{'fixture'})==masked(newtexts['test_g3_prepare.py'],'PrepareTests',{'fixture'}),'all prepare-test bytes outside fixture unchanged')
 original_methods=[];current_methods=[]
 for name in TESTS:
  compile(newtexts[name],str(new/name),'exec')
  old=test_methods(texts[name]);current=test_methods(newtexts[name]);need(old==current,'every original test class/method preserved '+name)
  original_methods.extend((name,*r)for r in old);current_methods.extend((name,*r)for r in current)
 need(len(original_methods)==len(current_methods)==32,'all original32 methods preserved, none added or skipped')
 changed={n for n in TESTS if newtexts[n]!=texts[n]}
 need(changed=={'test_g3_parent.py','test_g3_prepare.py'},'only two fixture modules change')
 new.mkdir();rows={}
 for name in TESTS:
  with(new/name).open('x')as f:f.write(newtexts[name])
  rows[name]=dict(before=before[name],after=ref(new/name),edits=[dict(before=texts[name],after=newtexts[name])]if name in changed else[])
 ledger=dict(schema='bole.G3-original32-fixture-rebase/v1',baseline_source=SR13,donor_manifest=OLD_MANIFEST,
  files=rows,changed_modules=sorted(changed),unchanged_modules=sorted(set(TESTS)-changed),
  parent_methods_replaced=sorted(changed_parent),prepare_methods_replaced=['fixture'],
  original_methods=original_methods,current_methods=current_methods,
  enumerated_methods=32,actual_sameimage_executed=False,actual_pass_claimed=False,
  production_parent_bypass_added=False,NPU=False)
 write(new/'G3_FIXTURE_EDITS_V1.json',ledger)
 summary=dict(schema='bole.G3-original32-fixture-rebase-preparation/v1',baseline_source=SR13,
  whole_inverse=ref(new/'G3_FIXTURE_EDITS_V1.json'),files={n:ref(new/n)for n in TESTS},
  original_methods_preserved=True,enumerated_methods=32,changed_modules=sorted(changed),
  actual_sameimage_executed=False,actual_pass_claimed=False,NPU=False)
 write(new/'MANIFEST.json',summary)
 print(json.dumps(dict(manifest=ref(new/'MANIFEST.json'),whole_inverse=summary['whole_inverse'],
  enumerated_methods=32,actual_sameimage_executed=False,NPU=False)))
 return 0
if __name__=='__main__':raise SystemExit(main())

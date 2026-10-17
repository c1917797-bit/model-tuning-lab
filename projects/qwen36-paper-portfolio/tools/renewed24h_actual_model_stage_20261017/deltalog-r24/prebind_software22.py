"""Prepared-only same-image full discovery; never creates a model binding."""
import argparse,hashlib,importlib.util,io,json,os,sys,time,unittest,traceback
from pathlib import Path
DEFERRED=('test_actual017_binding.ActualBinding.test_real_template_original017_adapt_and_private_bind','test_overlay.Tests.test_allcold_and_actual_namespace')

def partition(suite):
 def flatten(s):
  for x in s:
   if isinstance(x,unittest.TestSuite):yield from flatten(x)
   else:yield x
 rows=list(flatten(suite));ids=[x.id()for x in rows]
 if len(ids)!=len(set(ids))or any(ids.count(x)!=1 for x in DEFERRED):raise ValueError('exact two bound-only tests must exist once; no generic skip')
 return unittest.TestSuite(x for x in rows if x.id()not in DEFERRED),ids
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--template-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 tr=json.loads(a.template_ref);root=Path(__file__).resolve().parent;sys.path.insert(0,str(root));import owner_overlay as O
 O.need(tr['path']==str(root/'SOURCE_TEMPLATE.json'),'exact deployed prepared template path');m=O.obj(tr)
 O.need(m['prepared_only']is True and m['root']==str(root)and not(root/'SOURCE_MANIFEST.json').exists(),'prebind really precedes model source publication, no fake bound descriptor')
 O.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and not list(Path('/dev').glob('davinci*')),'same-image Devices[] stage only')
 O.need(a.output.parent.is_dir()and not a.output.exists(),'new software report')
 # Exact original ticket/source checker; no direct prepared_only=False mutation.
 r=m['files']['prebind_static.py'];s=importlib.util.spec_from_file_location('_r22_original_prebind',O.obj_file(r));S=importlib.util.module_from_spec(s);s.loader.exec_module(S)
 bound_view,closure=S.prepare(m,tr,root,runtime=True)
 os.environ['DL025_DONOR017_LOCAL']=str(Path(m['host017_ref']['path']).parent);os.environ['DL025_DONOR008_LOCAL']=m['donor008_host_ref']['path'];os.environ['DL025_CAPTURE_CLIENT_LOCAL']=m['capture_client_ref']['path']
 started=time.monotonic();stream=io.StringIO();count=None;result=None;primary=None
 try:
  suite,original_ids=partition(unittest.defaultTestLoader.discover(str(root),pattern='test_*.py'));count=suite.countTestCases();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
  O.need(len(original_ids)==m['software_cases']and count==m['software_cases']-2 and result.testsRun==count and result.wasSuccessful()and not result.skipped,'complete prepared-stage suite/noSkip; two exact bound-only tests retained for original model CPU: '+stream.getvalue())
 except BaseException as e:primary=dict(error=repr(e),traceback=traceback.format_exc())
 for r in[*m['files'].values(),tr,closure['ticket']]:O.obj_file(r)
 value=dict(schema='deltalog.actual-prebind-software/v22',template=tr,command_ticket=closure['ticket'],own_read_closure=closure,discovered=count,original_discovered=m['software_cases'],deferred_to_original_model_cpu=list(DEFERRED),full_model_suite_executed=False,executed=result.testsRun if result else None,skipped=len(result.skipped)if result else None,full_suite_pass=primary is None,primary=primary,log=stream.getvalue(),elapsed=time.monotonic()-started,prepared_only=True,model_source_created=False,Devices=[],NPU=False,qualified=False)
 with a.output.open('x',encoding='utf8',newline='\n')as f:json.dump(value,f,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
 return 0 if primary is None else 3
if __name__=='__main__':raise SystemExit(main())

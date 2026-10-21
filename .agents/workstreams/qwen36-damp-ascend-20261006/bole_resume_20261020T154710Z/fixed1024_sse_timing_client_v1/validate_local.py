"""Local controlled protocol checks only; no actual timing/HTTP/process."""
import ast,hashlib,json,pathlib,subprocess,sys,unittest
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P))
def ref(p):b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
asts=[]
for f in sorted(P.rglob('*.py')):ast.parse(f.read_bytes(),filename=str(f));asts.append(ref(f))
with (P/'UNITTEST_STDERR.txt').open('w')as stream:r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('test_sse_controls'))
assert r.wasSuccessful()and r.testsRun==23 and not r.skipped and not r.expectedFailures
modes=[]
for n in('fixed1024_client.py','independent_reader.py'):
 for args in([],['--help'],['--execute']):
  q=subprocess.run(['/usr/bin/python3','-I','-B',str(P/n),*args],capture_output=True,text=True);assert (q.returncode!=0)==(args==['--execute']);modes.append(dict(file=n,args=args,returncode=q.returncode,stdout=q.stdout,stderr=q.stderr))
assert 'fixed1024_client'not in (P/'independent_reader.py').read_text()
review=json.loads((P/'SOURCE_REVIEW.json').read_bytes())
for v in review['source_anchors'].values():assert ref(pathlib.Path(v['full_source']['path']))==v['full_source']
v=dict(schema='bole.fixed1024-SSE-local-only-validation/v1',status='SOURCE_ONLY_UNQUALIFIED',AST=asts,controlled_unittest_cases=r.testsRun,passed=r.testsRun,skipped=0,expected_failures=0,all_passed=True,controlled_fixtures_only=True,full_unittest_stderr=ref(P/'UNITTEST_STDERR.txt'),CLI_modes=modes,independent_parser_imports_no_client=True,actual_source_review=ref(P/'SOURCE_REVIEW.json'),actual_HTTP=False,actual_NPU=False,actual_process=False,resources_admitted=False,actual_fixed1024_run=False,actual_matched_pairs=False,formal_qualification=False,MODEL_four_refs=dict(source=None,owner_result=None,qualification=None,source_audit=None),capture_OFF_production_qualification=None,paired_owner=None,source_bound_owner_reviewer=None)
(P/'LOCAL_VALIDATION.json').write_text(json.dumps(v,sort_keys=True,indent=2)+'\n');print(json.dumps(dict(local_validation=ref(P/'LOCAL_VALIDATION.json'),controlled_pass=r.testsRun,actual_HTTP=False,NPU=False)))

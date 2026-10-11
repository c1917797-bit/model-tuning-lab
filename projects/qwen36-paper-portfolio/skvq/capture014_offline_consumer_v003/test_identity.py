"""Small actual014 metadata regressions. No tensors/framework/native authority.

Windows review uses explicitly SHA-checked source/evidence mirrors only. The
production consumer has no mirror or source-guard bypass option.
"""
import argparse,ast,copy,hashlib,importlib.util,json,sys,unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import capture_identity as identity
ARGS=None;TP=None;NEW=None;OLD=None;MANIFEST=None;INSTALL=None;LOADERS={};RAWS={};PATHS={};FAILURE=None;MIRROR=None
CAPTURE_SHA="9c7b1118b1cd1f2a20ab7fde0ecb98031bf14289c9c795c18f48de9cdb805acd"
def need(v,m):
    if not v:raise ValueError(m)
def checked(path,row):
    raw=Path(path).read_bytes()
    need(len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256'],"actual entire mirrored bytes/size/SHA")
    return raw
def evidence(relative):
    row=next(r for r in MIRROR['files']if r['relative']==relative)
    return ARGS.mirror_root/relative if ARGS.mirror_root else Path(row['path'])
def module(name,path):
    need(name not in sys.modules,"clean test-only module namespace")
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value;spec.loader.exec_module(value);return value
@contextmanager
def source_transport():
    """Read original bytes via exact mirrors, not an identity-oracle stub."""
    read=Path.read_bytes;stat=Path.stat
    def actual(p):return PATHS.get(p.as_posix(),p)
    def read_mapped(p):return read(actual(p))
    def stat_mapped(p,*a,**kw):return stat(actual(p),*a,**kw)
    with patch.object(Path,'read_bytes',read_mapped),patch.object(Path,'stat',stat_mapped):yield
def prepare(args):
    global ARGS,TP,NEW,OLD,MANIFEST,INSTALL,PATHS,FAILURE,MIRROR
    ARGS=args
    raw=(args.capture_source/'SOURCE_MANIFEST.json').read_bytes()
    need(hashlib.sha256(raw).hexdigest()==CAPTURE_SHA,"immutable original014 source manifest")
    MANIFEST=json.loads(raw);rows={Path(r['path']).name:r for r in MANIFEST['files']}
    for name in ('tp_provider_current.py','order_oracle_current.py','consume_loader_current.py',
      'loader_bridge_current.py','runtime_capture_current.py','tp_provider_current.py'):
        checked(args.capture_source/name,rows[name])
    TP=module('tp_provider_current',args.capture_source/'tp_provider_current.py')
    NEW=module('_skvq014_new_order_regression',HERE/'order_oracle_derived.py')
    OLD=module('_skvq014_original_order_regression',args.capture_source/'order_oracle_current.py')
    FAILURE=module('_skvq014_failure_regression',HERE/'previous_failure.py')
    if args.mirror_root:
        mirror=json.loads((args.mirror_root/'MIRROR_MANIFEST.json').read_bytes())
        extra=json.loads((args.mirror_root/'MIRROR_EXTRA_MANIFEST.json').read_bytes())
        MIRROR=dict(files=mirror['files']+extra['files'])
    else:MIRROR=dict(files=json.loads((HERE/'SOURCE_MANIFEST.json').read_bytes())['actual_metadata_regression_refs'])
    for row in MIRROR['files']:checked(evidence(row['relative']),row)
    INSTALL=json.loads(evidence('INSTALL.json').read_bytes())
    need(len(INSTALL)==4 and {r['rank']for r in INSTALL}==set(range(4)),"actual complete all4 INSTALL")
    for rank in range(4):
        LOADERS[rank]=json.loads(evidence('rank-%d/QKV_LOADER_ORDER.json'%rank).read_bytes())
        RAWS[rank]=json.loads(evidence('QKV_INSTALL-rank-%d-RAW.json'%rank).read_bytes())
    # Only known exact archived sources. Their actual hashes are checked BEFORE
    # the transport is installed; unknown paths remain unknown/fail closed.
    PATHS[TP.PARALLEL_SOURCE]=args.native_source/'public_parallel_state.py'if args.native_source else Path(TP.PARALLEL_SOURCE)
    public=next(r for r in MANIFEST['dependencies']if r['path']==TP.PARALLEL_SOURCE)
    checked(PATHS[TP.PARALLEL_SOURCE],public)
    for pin in TP.NATIVE_PINS:
        row=pin['snapshot'];p=args.native_source/Path(row['path']).name if args.native_source else Path(row['path'])
        checked(p,row);PATHS[row['path']]=p
    for pin in NEW.PINS:
        row=pin['snapshot'];name=Path(row['path']).name
        p=(args.native_source/'utils.py'if name=='utils.py'else args.linear_source/name)if args.linear_source else Path(row['path'])
        checked(p,row);PATHS[row['path']]=p
def item(rank):return next(r for r in INSTALL if r['rank']==rank)
def call_raw(rank,raw=None,after=None,loader=None):
    v=LOADERS[rank]if loader is None else loader
    return NEW.consume_install_raw(RAWS[rank]if raw is None else raw,rank,
      item(rank)['identity']if after is None else after,v['records'],v['current_source_ref'],loader_identity=v['identity'])
class ActualIdentity(unittest.TestCase):
    def test01_all12_actual_mirror_originals_hashchecked(self):
        self.assertEqual(len(MIRROR['files']),16)
        for r in MIRROR['files']:checked(evidence(r['relative']),r)
    def test02_original_all4_counterexample_is_only_ordered_timestamp(self):
        for rank in range(4):
            before=LOADERS[rank]['identity'];after=item(rank)['identity']
            self.assertNotEqual(before,after)
            self.assertEqual({k for k in before if before[k]!=after[k]},{'observed_utc_ns'})
            self.assertIs(type(before['observed_utc_ns']),int)
            self.assertLess(before['observed_utc_ns'],after['observed_utc_ns'])
            self.assertTrue(identity.exact(before,RAWS[rank]['identity']))
    def test03_original_order_consumer_reproduces_actual_refusal(self):
        for rank in range(4):
            with self.assertRaisesRegex(ValueError,'complete original all16 same-worker'):
                OLD.consume_install_raw(RAWS[rank],rank,item(rank)['identity'],LOADERS[rank]['records'],LOADERS[rank]['current_source_ref'])
    def test04_original_loader_joint_predicate_reproduces_false(self):
        tree=ast.parse((ARGS.capture_source/'consume_loader_current.py').read_bytes())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='consume')
        gates=[n for n in ast.walk(fn)if isinstance(n,ast.Call)and len(n.args)>1 and
          isinstance(n.args[1],ast.Constant)and n.args[1].value=='same real captured rank process']
        self.assertEqual(len(gates),1)
        expression=compile(ast.Expression(gates[0].args[0]),'original014-L22-predicate','eval')
        for rank in range(4):self.assertFalse(eval(expression,{},dict(v=LOADERS[rank],item=item(rank),rank=rank)))
    def test05_actual_pairs_use_original_TP_source_oracle_twice(self):
        with source_transport():
            for rank in range(4):
                result=identity.pair(LOADERS[rank]['identity'],item(rank)['identity'],rank,TP.consume_identity)
                self.assertEqual(result['elapsed_observation_ns'],item(rank)['identity']['observed_utc_ns']-LOADERS[rank]['identity']['observed_utc_ns'])
                self.assertEqual(len(result['stable_keys']),15)
    def test06_actual_all4_all16_raw_and_global_channel_order(self):
        with source_transport():
            for rank in range(4):self.assertIs(call_raw(rank),RAWS[rank])
            for logical in LOADERS[0]['records']:
                self.assertEqual(NEW.consume_four({r:LOADERS[r]['records'][logical]for r in range(4)}),list(range(1024)))
    def test07_PID_start_cmdline_and_cgroup_rebinding_rejected(self):
        mutations=[('pid',1),('pid_start_ticks',1),('proc_cmdline_sha256','0'*64),
          ('torch_source',{'module':'foreign','path':'/foreign','sha256':'0'*64})]
        with source_transport():
            for key,value in mutations:
                after=copy.deepcopy(item(0)['identity']);after[key]=value
                with self.assertRaises(ValueError):call_raw(0,after=after)
            after=copy.deepcopy(item(0)['identity']);after['groups']['tp']['process_groups']['device']['object_id']+=1
            with self.assertRaises(ValueError):call_raw(0,after=after)
    def test08_group_rank_backend_and_source_changes_rejected(self):
        with source_transport():
            for key,value in [('members',[0,2,1,3]),('logical_device',1),('object_id',1)]:
                after=copy.deepcopy(item(0)['identity']);after['groups']['tp'][key]=value
                with self.assertRaises(ValueError):call_raw(0,after=after)
            after=copy.deepcopy(item(0)['identity']);after['groups']['world']['process_groups']['device']['backend']='nccl'
            with self.assertRaises(ValueError):call_raw(0,after=after)
            after=copy.deepcopy(item(0)['identity']);after['native_group_class']['runtime_origins'][TP.PATCH_MODULE]['sha256']='0'*64
            with self.assertRaises(ValueError):call_raw(0,after=after)
    def test09_missing_extra_identity_and_bool_int_rejected(self):
        with source_transport():
            for key in identity.IDENTITY_KEYS:
                after=copy.deepcopy(item(0)['identity']);after.pop(key)
                with self.assertRaises(ValueError):call_raw(0,after=after)
            after=copy.deepcopy(item(0)['identity']);after['unknown']=True
            with self.assertRaises(ValueError):call_raw(0,after=after)
            after=copy.deepcopy(item(0)['identity']);after['groups']['pp']['global_rank']=False
            with self.assertRaises(ValueError):call_raw(0,after=after)
    def test10_zero_bool_float_equal_or_reversed_timestamps_rejected(self):
        with source_transport():
            for timestamp in (0,True,float(item(0)['identity']['observed_utc_ns']),LOADERS[0]['identity']['observed_utc_ns'],LOADERS[0]['identity']['observed_utc_ns']-1):
                after=copy.deepcopy(item(0)['identity']);after['observed_utc_ns']=timestamp
                with self.assertRaises(ValueError):call_raw(0,after=after)
    def test11_raw_loader_first_observation_must_be_exact(self):
        raw=copy.deepcopy(RAWS[0]);raw['identity']['observed_utc_ns']+=1
        with source_transport():
            with self.assertRaisesRegex(ValueError,'raw and loader'):call_raw(0,raw=raw)
    def test12_same_rank_order_and_all16_typed_projection_guards_preserved(self):
        with source_transport():
            raw=copy.deepcopy(RAWS[0]);raw['rank']=1
            with self.assertRaises(ValueError):call_raw(0,raw=raw)
            raw=copy.deepcopy(RAWS[0]);raw['observed'].pop(next(iter(raw['observed'])))
            with self.assertRaises(ValueError):call_raw(0,raw=raw)
            raw=copy.deepcopy(RAWS[0]);raw['observed'][next(iter(raw['observed']))]['fields']['tp_rank']={'type':'builtins.bool','value':False}
            with self.assertRaises(ValueError):call_raw(0,raw=raw)
    def test13_real_producer_observation_order_and_fields_preserved(self):
        raw=(ARGS.capture_source/'loader_bridge_current.py').read_text()
        self.assertLess(raw.index('identity=original.RankProvider()()'),raw.index('original.install_rpc'))
        session=(ARGS.capture_source/'runtime_capture_current.py').read_text()
        self.assertIn('self.identity=self.rank()',session)
        provider=(ARGS.capture_source/'tp_provider_current.py').read_text()
        self.assertIn('"observed_utc_ns":time.time_ns()',provider)
        self.assertEqual(identity.IDENTITY_KEYS,set(LOADERS[0]['identity']))
    def test14_full_consumer_entry_calls_new_pair_and_raw_loader_link(self):
        raw=(HERE/'consume_loader_derived.py').read_text();tree=ast.parse(raw)
        self.assertIn('pair(v["identity"],item["identity"],rank,consume_identity)',raw)
        self.assertIn('loader_identity=v["identity"]',raw)
        self.assertLess(raw.index('result=full_baseline_raw(root)'),raw.index('pair(v["identity"]'))
        self.assertIn('events==16384',raw);self.assertIn('consume_four',raw)
        calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='consume_install_raw']
        self.assertEqual(len(calls),1);self.assertEqual([k.arg for k in calls[0].keywords],['loader_identity'])
    def test15_no_other_order_oracle_math_or_qualification_body_changed(self):
        old=ast.parse((ARGS.capture_source/'order_oracle_current.py').read_bytes());new=ast.parse((HERE/'order_oracle_derived.py').read_bytes())
        for fn in ('consume_record','consume_four','consume_qualification','consume_preweights'):
            a=next(n for n in old.body if isinstance(n,ast.FunctionDef)and n.name==fn)
            b=next(n for n in new.body if isinstance(n,ast.FunctionDef)and n.name==fn)
            self.assertEqual(ast.dump(a),ast.dump(b))
        for n in ast.walk(new):
            if isinstance(n,ast.ImportFrom):self.assertFalse(n.module and n.module.startswith('torch'))
    def test16_all_own_sources_compile_and_no_framework_or_device(self):
        for p in HERE.glob('*.py'):compile(p.read_bytes(),str(p),'exec')
        self.assertNotIn('torch',sys.modules);self.assertNotIn('torch_npu',sys.modules)
    def test17_actual_failed_parent_not_reconstructed_success(self):
        value=json.loads(evidence('MAIN_SKVQ014_05A7_FAILED_ORIGINAL_20261011.json').read_bytes())
        record=FAILURE.original(value);self.assertEqual(record['exitCode'],1)
        for key,replacement in [('succeeded',True),('terminal',False),('status','running')]:
            wrong=copy.deepcopy(value);wrong[key]=replacement
            with self.assertRaises(ValueError):FAILURE.original(wrong)
        wrong=copy.deepcopy(value);wrong['operation']['result']['record']['exitCode']=0
        with self.assertRaises(ValueError):FAILURE.original(wrong)
    def test18_actual_child0_consumer1_and_three_released_owned(self):
        h=json.loads(evidence('HOST_RESULT.json').read_bytes())
        a=json.loads(evidence('capture256-CLI-1791678368942182340.json').read_bytes())
        b=json.loads(evidence('consume-full256-preprojection-CLI-1791679925302880550.json').read_bytes())
        self.assertTrue(FAILURE.children_fields(h,a,b));self.assertIsNone(h['result'])
        for original,key,value in[(a,'exit_code',1),(a,'terminated',False),(b,'exit_code',0)]:
            wrong=copy.deepcopy(original);wrong[key]=value
            with self.assertRaises(ValueError):FAILURE.children_fields(h,wrong if original is a else a,wrong if original is b else b)
        wrong=copy.deepcopy(h);wrong['owned'][1]['released']=False
        with self.assertRaises(ValueError):FAILURE.children_fields(wrong,a,b)
        wrong=copy.deepcopy(a);wrong['argv'][4]='MAIN_OWNED_CID='+'0'*64
        with self.assertRaises(ValueError):FAILURE.children_fields(h,wrong,b)
    def test19_arbitrary_failure_wrong_source_or_old_success_rejected(self):
        h=json.loads(evidence('HOST_RESULT.json').read_bytes())
        for key,value in[('primary',"ValueError('other')"),('secondary',['error']),('status','PASS'),('result',{})]:
            wrong=copy.deepcopy(h);wrong[key]=value
            with self.assertRaises(ValueError):FAILURE.qualify_host(wrong,FAILURE.HOST_REF)
        wrong=copy.deepcopy(h);wrong['source_lock']['sha256']='0'*64
        with self.assertRaises(ValueError):FAILURE.qualify_host(wrong,FAILURE.HOST_REF)
    def test20_original_firstfault_full_byte_identity_is_preserved(self):
        row=FAILURE.FAILED_STDERR_REF
        data=checked(evidence('consume-full256-preprojection.stderr'),row)
        self.assertTrue(data.endswith(b'ValueError: same real captured rank process\n'))
        self.assertIn(b'consume_loader_current.py", line 22',data)
        self.assertIn(b'v["identity"]==item["identity"]',data)
def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--mirror-root',type=Path)
    p.add_argument('--capture-source',type=Path,default=Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-014'))
    p.add_argument('--native-source',type=Path);p.add_argument('--linear-source',type=Path);a=p.parse_args(argv);prepare(a)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ActualIdentity))
    return 0 if result.wasSuccessful()else 1
if __name__=='__main__':sys.exit(main())

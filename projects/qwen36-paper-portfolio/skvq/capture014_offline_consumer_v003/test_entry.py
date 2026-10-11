"""Actual aggregate source/CLI closure; local tests never create a runtime guest."""
import ast,hashlib,json,subprocess,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import test_identity as I
class Entry(unittest.TestCase):
    def test01_unique_new_CPU_argv_and_no_recap(self):
        import cpu_host as H
        source=dict(path='/new/SOURCE_MANIFEST.json',bytes=1,sha256='a'*64)
        args=H.guest_args(source,Path('/new-run'))
        self.assertIn('consume_raw.py',args[0]);self.assertNotIn('capture_current.py',str(args))
        self.assertEqual(args[args.index('--output')+1],str(Path('/new-run/work')))
        self.assertEqual((H.TOTAL,H.CLEANUP,H.OUTCAP),(3600,180,64*2**20))
    def test02_exact_Control_AST_no_native_idle_in_CPU_adapter(self):
        old=ast.parse((I.ARGS.capture_source/'MAIN_HOST.py').read_bytes())
        row=next(n for n in old.body if isinstance(n,ast.ClassDef)and n.name=='Control')
        raw=(HERE/'cpu_host.py').read_text()
        self.assertIn('ast.Module(body=nodes,type_ignores=[])',raw)
        self.assertNotIn('nodes[0].body',raw);self.assertNotIn('ast.NodeTransformer',raw)
        tree=ast.parse(raw);adapter=next(n for n in ast.walk(tree)if isinstance(n,ast.ClassDef)and n.name=='CPUControl')
        observe=next(n for n in adapter.body if isinstance(n,ast.FunctionDef)and n.name=='observe')
        self.assertIsInstance(observe.body[0],ast.Raise)
        create=next(n for n in adapter.body if isinstance(n,ast.FunctionDef)and n.name=='create')
        self.assertIn('npu is False',ast.unparse(create));self.assertIn('mem == 2 * GIB',ast.unparse(create))
        self.assertTrue(hashlib.sha256(ast.dump(row,include_attributes=False).encode()).hexdigest())
    def test03_whole_keeps_strict_true_external_terminal_and_FAILED_parent(self):
        raw=(HERE/'consume_cpu_whole.py').read_text()
        self.assertIn('"actual NEW successful CPU whole',raw)
        self.assertIn('value["succeeded"]is True',raw)
        self.assertIn('original_failed_whole_succeeded=False',raw)
        self.assertIn('original_failed_whole_ref=D.FAILED_ORIGINAL',raw)
        self.assertIn('whole_operation_consumed=True',raw)
        self.assertNotIn('succeeded=False,exitCode=0',raw)
    def test04_raw_whole_preserves_all_event_and_source_oracles(self):
        raw=(HERE/'consume_raw.py').read_text()
        for value in ('loader.consume(root)','projection.consume(root,br[\'path\'])','host_reader.consume(Path(D.RAW_ROOT),ar)',
          'stage.combine(baseline,preprojection,D.CAPTURE,br,kr)','payload_recheck(D.obj(F.HOST_REF),deadline)',
          "D.ref(root/'PRODUCER_RESULT.json')==producer_ref"):
            self.assertIn(value,raw)
        self.assertLess(raw.index('identity=inspect_pairs(source)'),raw.index('baseline=loader.consume(root)'))
    def test05_original_owned_all3_and_actual_cmdline_math_guards_preserved(self):
        a=ast.parse((I.ARGS.capture_source/'consume_host.py').read_bytes())
        b=ast.parse((HERE/'consume_previous_host.py').read_bytes())
        for name in ('read','consume_protected'):
            aa=next(n for n in a.body if isinstance(n,ast.FunctionDef)and n.name==name)
            bb=next(n for n in b.body if isinstance(n,ast.FunctionDef)and n.name==name)
            self.assertEqual(ast.dump(aa),ast.dump(bb))
        raw=(HERE/'consume_previous_host.py').read_text()
        for needle in ('len(v["owned"])==3','PC.consume(read(p["actual_cmdline_raw_ref"]),p,source)',
          'actual_hbm(smi["stdout"],card)','native_tp.consume_preweights','consume_qkv_preweights',
          'consume_text_preweights','D.consume(read(reference(root/"cpu/INPUT_DEPENDENCY.json"))'):
            self.assertIn(needle,raw)
        self.assertNotIn('consumed=read(v["result"]["consumer"])',raw)
        self.assertIn('reference(C.ROOT/"SOFTWARE_TESTS_15.py")',raw)
    def test06_no_mutation_old_root_and_single_RW_payload_after(self):
        raw=(HERE/'cpu_host.py').read_text()
        self.assertIn("mounts[str(D.RAW_ROOT)]=(str(D.RAW_ROOT),False)",raw)
        self.assertIn("mounts[str(out)]=(str(out),True)",raw)
        self.assertIn("if rw]==[str(out)]",raw)
        self.assertIn("mem==2*GIB",raw)
        raw=(HERE/'consume_raw.py').read_text()
        self.assertIn("value==old_host['actual_payload']",raw)
        self.assertIn("old_before_after_success_not_claimed=True",raw)
        self.assertNotIn('fake',ast.unparse(ast.parse(raw)).lower())
        import offline_contract as D
        row=D.ref(HERE/'capture_identity.py')
        loaded=D.load('_skvq014_actual_owned_cache_regression',row)
        self.assertEqual(D.ref(loaded.__file__),row)
        self.assertIs(D.load('_skvq014_actual_owned_cache_regression',row),loaded)
        with self.assertRaisesRegex(ValueError,'cached module'):
            D.load('_skvq014_actual_owned_cache_regression',D.ref(HERE/'identity_preflight.py'))
        self.assertIn('load("identity_preflight",own["identity_preflight.py"])',
          (HERE/'offline_contract.py').read_text())
    def test07_actual_default_OFF_children_no_source_device_launch(self):
        for name in ('cpu_host.py','consume_raw.py','identity_preflight.py','consume_cpu_whole.py'):
            r=subprocess.run([sys.executable,'-I','-B',str(HERE/name)],text=True,capture_output=True,timeout=5)
            self.assertEqual(r.returncode,0,r.stderr)
            value=json.loads(r.stdout);self.assertIs(value['default_enabled'],False)
            self.assertIs(value['model_ready']if 'model_ready'in value else value['whole_capture_consumed'],False)
    def test08_loader_narrow_delta_and_raw_installs_match_actual(self):
        for rank in range(4):
            self.assertTrue(I.identity.exact(I.RAWS[rank]['identity'],I.LOADERS[rank]['identity']))
        old=ast.parse((I.ARGS.capture_source/'consume_loader_current.py').read_bytes())
        new=ast.parse((HERE/'consume_loader_derived.py').read_bytes())
        a=next(n for n in old.body if isinstance(n,ast.FunctionDef)and n.name=='consume')
        b=next(n for n in new.body if isinstance(n,ast.FunctionDef)and n.name=='consume')
        aa=next(n for n in a.body if isinstance(n,ast.For)and ast.unparse(n.target)=='item')
        bb=next(n for n in b.body if isinstance(n,ast.For)and ast.unparse(n.target)=='item')
        self.assertEqual(len(bb.body),len(aa.body)+1) # exactly ordered pair added
        self.assertNotIn('torch',sys.modules);self.assertNotIn('torch_npu',sys.modules)

    def test09_original_Control_left_charges_preflight_and_preserves_earlier_cutoff(self):
        import cpu_host as H
        from types import SimpleNamespace
        from unittest import mock
        tree=ast.parse((I.ARGS.capture_source/'MAIN_HOST.py').read_bytes())
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Control')
        node=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='left')
        def require(v,m):
            if not v:raise ValueError(m)
        now=[3513.]
        namespace=dict(time=SimpleNamespace(monotonic=lambda:now[0]),CLEANUP=180,require=require)
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-original-Control.left>','exec'),namespace)
        def controller(end):
            c=SimpleNamespace(start=900.,end=end,cleanup_started=None,cleanup_spent=0.)
            c.left=lambda **kw:namespace['left'](c,**kw)
            return c
        with mock.patch.object(H.time,'monotonic',side_effect=lambda:now[0]):
            c=controller(4500.)
            H.charge_preflight(c,100.)
            self.assertEqual((c.start,c.end,c.left()),(100.,3700.,7.))
            early=controller(3697.)
            H.charge_preflight(early,100.)
            self.assertEqual((early.end,early.left()),(3697.,4.))
            now[0]=3521.
            with self.assertRaisesRegex(ValueError,'cleanup'):
                H.charge_preflight(controller(9000.),100.)
            with self.assertRaisesRegex(ValueError,'actual entry'):
                H.charge_preflight(controller(9000.),True)
            with self.assertRaisesRegex(ValueError,'actual entry'):
                H.charge_preflight(controller(9000.),4000.)

    def test10_execute_clock_precedes_source_and_does_not_create_on_source_failure(self):
        import cpu_host as H
        from types import SimpleNamespace
        from unittest import mock
        events=[]
        def tick():
            events.append('entry');return 100.
        def fail_source(value):
            events.append('source');raise RuntimeError('deliberate-before-resources')
        with mock.patch.dict(H.os.environ,{'MAIN_SKVQ_OFFLINE_CPU_ENABLE':'1'}), \
             mock.patch.object(H.time,'monotonic',side_effect=tick), \
             mock.patch.object(H.time,'time',return_value=0.), \
             mock.patch.object(H.D,'source',side_effect=fail_source), \
             mock.patch.object(H,'newroot') as create_root:
            with self.assertRaisesRegex(RuntimeError,'deliberate-before-resources'):
                H.execute(SimpleNamespace(source_manifest_sha256='a'*64))
            self.assertEqual(events,['entry','source'])
            create_root.assert_not_called()

    def test11_actual_all3_host_mount_sources_visible_and_driver_RO(self):
        import cpu_host as H
        import previous_failure as F
        from pathlib import PurePosixPath as P
        from unittest import mock
        host=json.loads(I.evidence('HOST_RESULT.json').read_bytes())
        manifest=json.loads((HERE/'SOURCE_MANIFEST.json').read_bytes())
        source=H.D.ref(HERE/'SOURCE_MANIFEST.json')
        def actual_read(r):
            if r==F.HOST_REF:return host
            if r==source:return manifest
            raise AssertionError('unbound fixture input')
        with mock.patch.object(H.D,'obj',side_effect=actual_read), \
             mock.patch.object(H,'Path',P), \
             mock.patch.object(H.D,'ROOT',P(manifest['root'])):
            mounts=H.mount_set(P('/new-run'),source)
        self.assertEqual(mounts['/usr/local/Ascend/driver'],('/usr/local/Ascend/driver',False))
        self.assertEqual([d for d,(_,rw) in mounts.items()if rw],['/new-run'])
        def missing(m):
            return {s for e in host['owned']for s,rw in e['mounts'].values()
              if not any(P(s)==P(d)or P(d)in P(s).parents for d in m)}
        self.assertEqual(missing(mounts),set())
        del mounts['/usr/local/Ascend/driver']
        self.assertEqual(missing(mounts),{'/usr/local/Ascend/driver'})
        self.assertNotIn('/cache',mounts)
        self.assertNotIn('/dev',mounts)

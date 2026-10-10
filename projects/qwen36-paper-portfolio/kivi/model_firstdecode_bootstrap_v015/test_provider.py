"""Real source-body control-flow regression; inert tensors are not NPU/numerics."""
import copy, importlib.util, json, os, sys, time, types, unittest
from pathlib import Path
ROOT=Path(__file__).parent

def load(name):
    spec=importlib.util.spec_from_file_location("_provider_local_"+name,ROOT/(name+".py"))
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
P=load("explicit_provider");I=load("provider_independent");F=load("provider_projection")
class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.events=[];self.t,self.kv,self.u,self.dl,self.native,self.runner_cls=F.actual_modules(self.events)
        self.cfg=F.config();self.specs=F.specs_from_actual(self.kv)
        self.old=os.environ.get(P.FLAG);os.environ[P.FLAG]="1"
    def tearDown(self):
        if self.old is None:os.environ.pop(P.FLAG,None)
        else:os.environ[P.FLAG]=self.old
    def plan(self,bits=2):
        return P.plan(self.cfg,self.specs,self.u,self.kv,bits=bits,allocation_margin_bytes=256*1024**2)
    def config_for(self,plan):
        groups=self.u.get_kv_cache_groups(self.cfg,copy.deepcopy(self.specs))
        return self.u.get_kv_cache_config_from_groups(self.cfg,groups,plan["native_budget_returned_bytes"])
    def allocated(self):
        plan=self.plan();kv=self.config_for(plan)
        runner=F.new_runner(self.runner_cls,self.cfg,self.specs,self.events)
        raw=runner._allocate_kv_cache_tensors(kv)
        native=P.native_raw_check(raw,kv,F.describe)
        names=next(g["names"] for g in plan["native"]["groups"] if g["kind"]=="FA")
        arenas={n:self.dl.CompactArena(self.t,plan["pages"],16,2,"torch.bfloat16","npu:0",
                                      P.field_bytes(plan["pages"],2)) for n in names}
        compact={n:{k:F.describe(t) for k,t in a.pool.items()
                    if k not in ("allocated_bytes","dense_shadow_bytes")} for n,a in arenas.items()}
        return plan,native,compact,arenas
    def test01_actual_off_returns_without_source_or_tensor(self):
        os.environ.pop(P.FLAG)
        self.assertIs(P.make_worker(self.native,None,None,None,None,bits=None,allocation_margin_bytes=None,
                      describe=None,qualify=None,publish=None,consume_allocations=None,install_after_native=None),self.native)
        self.assertEqual(self.events,[])
    def test02_exact_factory_replays_actual_dense422(self):
        p=self.plan();self.assertEqual(p["dense_control"]["num_blocks"],422)
        self.assertEqual(p["dense_control"]["native_bytes"],10723688448)
        self.assertEqual(p["blocks_per_full_request"],25)
    def test03_budget_includes_every_named_item(self):
        p=self.plan();self.assertEqual(p["native"]["num_blocks"],341)
        self.assertEqual(p["pages"],4092);self.assertEqual(p["full_resident_upper_bound"],13)
        self.assertEqual(p["overhead"]["persistent_metadata_bytes"],69754880)
        self.assertEqual(p["overhead"]["full_prefill_gather_peak_bytes"],67108864)
        self.assertLessEqual(p["charged_total_bytes"],10*1024**3)
        self.assertGreater(p["charged_total_bytes"]+16*(1588224+294912),10*1024**3)
    def test04_four_bit_has_smaller_native_not_extra_budget(self):
        p=self.plan(4);self.assertLess(p["native"]["num_blocks"],341)
        self.assertLessEqual(p["charged_total_bytes"],10*1024**3)
    def test05_override_rejected_before_factory(self):
        self.cfg.cache_config.num_gpu_blocks_override=422
        with self.assertRaisesRegex(ValueError,"override"):self.plan()
    def test06_full_graph_rejected(self):
        self.cfg.model_config.enforce_eager=False
        with self.assertRaises(ValueError):self.plan()
    def test07_gdn_mode_not_relaxed(self):
        self.cfg.cache_config.mamba_cache_mode="align"
        with self.assertRaises(ValueError):self.plan()
    def test08_transfer_rejected(self):
        self.cfg.kv_transfer_config=object()
        with self.assertRaises(ValueError):self.plan()
    def test09_c16_scalar_config_preserved_not_ready(self):
        self.cfg.scheduler_config.max_num_seqs=16;p=self.plan()
        self.assertEqual(self.cfg.scheduler_config.max_num_seqs,16)
        self.assertEqual(p["requested_max_num_seqs"],16)
        self.assertFalse(p["scheduler_preemption_supported"]);self.assertFalse(p["performance_ready"])
        self.assertLess(p["full_resident_upper_bound"],16)
    def test10_malformed_actual_member_rejected(self):
        p=self.plan();kv=self.config_for(p);kv.kv_cache_tensors[0].shared_by.pop()
        with self.assertRaises(ValueError):P.native_summary(kv,self.kv)
    def test11_whole_storages_independent_positive_roundtrip(self):
        p,n,c,_=self.allocated()
        proof=I.consume(*json.loads(json.dumps([p,n,c])))
        self.assertEqual(proof["fields"],144);self.assertTrue(proof["native_all64_whole_pools_excluded"])
        self.assertFalse(proof["numerical_checked"])
    def test12_cross_fa_compact_overlap_rejected(self):
        p,n,c,_=self.allocated();names=list(c)
        c[names[1]]["key_codes"]=copy.deepcopy(c[names[0]]["key_codes"])
        with self.assertRaisesRegex(ValueError,"overlap"):I.consume(p,n,c)
    def test13_compact_inside_original_native_rejected(self):
        p,n,c,_=self.allocated();d=c[next(iter(c))]["key_codes"]
        d["storage_base"]=next(iter(n));d["data_ptr"]=d["storage_base"]
        with self.assertRaisesRegex(ValueError,"overlap"):I.consume(p,n,c)
    def test14_field_stride_rejected(self):
        p,n,c,_=self.allocated();c[next(iter(c))]["key_codes"]["stride"][0]-=1
        with self.assertRaises(ValueError):I.consume(p,n,c)
    def test15_missing_field_rejected(self):
        p,n,c,_=self.allocated();c[next(iter(c))].pop("shifts")
        with self.assertRaises(ValueError):I.consume(p,n,c)
    def test16_extra_unreported_field_rejected(self):
        p,n,c,_=self.allocated();fields=c[next(iter(c))];fields["secret"]=fields["shifts"]
        with self.assertRaises(ValueError):I.consume(p,n,c)
    def test17_storage_rounded_past_margin_rejected(self):
        p,n,c,_=self.allocated();d=c[next(iter(c))]["shifts"]
        d["storage_bytes"]+=p["overhead"]["allocation_margin_bytes"]+1
        with self.assertRaises(ValueError):I.consume(p,n,c)
    def test18_native_size_rejected(self):
        p,n,c,_=self.allocated();n[next(iter(n))]["logical_bytes"]-=1
        with self.assertRaises(ValueError):I.consume(p,n,c)
    def test19_foreign_device_rejected(self):
        p,n,c,_=self.allocated();c[next(iter(c))]["key_codes"]["device"]="npu:1"
        with self.assertRaises(ValueError):I.consume(p,n,c)
    def test20_claimed_peak_permission_rejected(self):
        p,n,c,_=self.allocated();p["allocator_peak_checked"]=True
        with self.assertRaises(ValueError):I.consume(p,n,c)
    def worker(self,install=None,consumer=I.consume):
        publications=[]
        def publish(name,value):
            publications.append((name,json.loads(json.dumps(value))))
            return {"path":"/fixture/"+name,"sha256":"fixture-not-authority","bytes":1}
        selected=P.make_worker(self.native,self.u,self.kv,self.dl,self.t,bits=2,
            allocation_margin_bytes=256*1024**2,describe=F.describe,
            qualify=lambda:self.events.append("qualify"),publish=publish,
            consume_allocations=consumer,
            install_after_native=install or (lambda worker,state:self.events.append("installer_after_native")))
        worker=selected();worker.vllm_config=self.cfg;worker.cache_config=self.cfg.cache_config
        worker.init_snapshot=types.SimpleNamespace(free_memory=64*1024**3)
        worker.model_runner=F.new_runner(self.runner_cls,self.cfg,self.specs,self.events)
        return worker,publications
    def test21_actual_native_profile_factory_allocator_arena_publish_chain(self):
        worker,pubs=self.worker();budget=worker.determine_available_memory()
        kv=self.config_for(worker._kivi_explicit_provider["plan"])
        self.assertEqual(kv.num_blocks,341)
        worker.initialize_from_config(kv)
        s=worker._kivi_explicit_provider
        self.assertEqual(s["state"],"consumer_installed");self.assertEqual(len(s["arenas"]),16)
        self.assertEqual(self.events.count("native_profile"),1)
        self.assertEqual([p[0] for p in pubs],["EXPLICIT-CACHE-PLAN","EXPLICIT-CACHE-ALLOCATED"])
        self.assertLess(self.events.index("native_reshape_bind_fixture"),self.events.index("installer_after_native"))
        self.assertNotIn("_allocate_kv_cache_tensors",vars(worker.model_runner))
        self.assertIs(worker.model_runner.raw,s["native_raw"])
        self.assertEqual(budget,s["plan"]["native_budget_returned_bytes"])
        self.assertEqual(worker.cache_config.kv_cache_memory_bytes,10*1024**3)
    def test22_wrong_scheduler_config_fails_before_allocation(self):
        worker,_=self.worker();worker.determine_available_memory()
        kv=self.config_for(worker._kivi_explicit_provider["plan"]);kv.num_blocks+=1
        with self.assertRaises(ValueError):worker.initialize_from_config(kv)
        self.assertNotIn("native_initialize",self.events)
    def test23_second_plan_rejected(self):
        worker,_=self.worker();worker.determine_available_memory()
        with self.assertRaises(ValueError):worker.determine_available_memory()
        self.assertEqual(self.events.count("native_profile"),1)
    def test24_independent_consumer_failure_restores_exact_hook_retains_state(self):
        def fail(*args):raise ValueError("independent failed")
        worker,_=self.worker(consumer=fail);worker.determine_available_memory()
        with self.assertRaisesRegex(ValueError,"independent failed"):
            worker.initialize_from_config(self.config_for(worker._kivi_explicit_provider["plan"]))
        self.assertEqual(worker._kivi_explicit_provider["state"],"failed")
        self.assertEqual(len(worker._kivi_explicit_provider["arenas"]),16)
        self.assertNotIn("_allocate_kv_cache_tensors",vars(worker.model_runner))
        self.assertNotIn("installer_after_native",self.events)
    def test25_original_arena_slot_epoch_and_actual_fence_order(self):
        _,_,_,arenas=self.allocated();a=next(iter(arenas.values()));r=a.acquire(0,"one")
        self.assertEqual(r.epoch,1)
        with self.assertRaises(ValueError):a.acquire(0,"second")
        a.release(r);self.assertEqual(self.events[-1],"sync")
        other=a.acquire(0,"second");self.assertEqual(other.epoch,2)
        with self.assertRaises(ValueError):a.owned(r)
        self.assertIs(a.active[0],other)
    def test26_pending_slot_never_recycled(self):
        _,_,_,arenas=self.allocated();a=next(iter(arenas.values()));r=a.acquire(0,"one")
        r.pending=True
        with self.assertRaises(ValueError):a.release(r)
        self.assertIs(a.active[0],r);a.abort(r);a.release(r)
        self.assertNotIn(0,a.active)
    def test27_original_shared_prefix_refcounts_return_only_after_last_owner(self):
        _,_,_,arenas=self.allocated();a=next(iter(arenas.values()));r=a.acquire(0,"parent")
        ki,vi=a._reserve(1,2);r.kp=ki;r.vp=vi
        a.krefs={ki[0]:1};a.vrefs={x:1 for x in vi}
        child=a.fork(r,1,"child");a.release(r)
        self.assertNotIn(ki[0],a.free_k);self.assertEqual(a.krefs[ki[0]],1)
        a.release(child);self.assertIn(ki[0],a.free_k)
        self.assertEqual(a.krefs,{});self.assertEqual(a.vrefs,{})
    def test28_negative_reservation_and_exhaustion(self):
        _,_,_,arenas=self.allocated();a=next(iter(arenas.values()))
        with self.assertRaises(ValueError):a._reserve(-1,1)
        with self.assertRaises(ValueError):a._reserve(len(a.free_k)+1,1)
    def test29_same_native_pool_alias_rejected_before_compact(self):
        p=self.plan();kv=self.config_for(p);runner=F.new_runner(self.runner_cls,self.cfg,self.specs,self.events)
        raw=runner._allocate_kv_cache_tensors(kv);pool=kv.kv_cache_tensors[0]
        raw[pool.shared_by[1]]=F.Tensor(pool.size,"torch.int8","npu:0",self.events)
        with self.assertRaises(ValueError):P.native_raw_check(raw,kv,F.describe)
    def test30_no_margin_no_claimed_bound(self):
        with self.assertRaises(ValueError):
            P.plan(self.cfg,self.specs,self.u,self.kv,bits=2,allocation_margin_bytes=0)
    def managers(self):
        p=self.plan();config=self.config_for(p)
        pools,managers=F.actual_managers(self.kv,self.u)
        pool=pools.BlockPool(p["native"]["num_blocks"],False,33792)
        result=[]
        for index,g in enumerate(config.kv_cache_groups):
            cls=managers.FullAttentionManager if type(g.kv_cache_spec) is self.kv.FullAttentionSpec else managers.MambaManager
            result.append(cls(g.kv_cache_spec,pool,enable_caching=False,kv_cache_group_id=index,scheduler_block_size=33792))
        return p,pool,result
    def test31_original_blockpool_one_null_and_original_manager25(self):
        p,pool,managers=self.managers()
        self.assertTrue(pool.null_block.is_null);self.assertEqual(pool.get_num_free_blocks(),340)
        needs=[m.get_num_blocks_to_allocate("owner",33792,[],0,33792) for m in managers]
        self.assertEqual(sorted(needs),[1,1,1,22]);self.assertEqual(sum(needs),p["blocks_per_full_request"])
        for m in managers:m.allocate_new_blocks("owner",33792,33792)
        self.assertEqual(pool.get_num_free_blocks(),315)
        for m in managers:m.free("owner")
        self.assertEqual(pool.get_num_free_blocks(),340)
    def test32_original_thirteen_full_requests_and_fourteenth_no_capacity(self):
        p,pool,managers=self.managers()
        for i in range(13):
            for m in managers:m.allocate_new_blocks(str(i),33792,33792)
        self.assertEqual(pool.get_num_free_blocks(),15)
        requested=sum(m.get_num_blocks_to_allocate("fourteenth",33792,[],0,33792) for m in managers)
        self.assertEqual(requested,25);self.assertGreater(requested,pool.get_num_free_blocks())
        for m in managers:m.free("0")
        self.assertEqual(pool.get_num_free_blocks(),40)
        for m in managers:m.allocate_new_blocks("replacement",33792,33792)
        self.assertEqual(pool.get_num_free_blocks(),15)
    def test33_original_gdn_retire_does_not_free_other_owner_or_null(self):
        _,pool,managers=self.managers()
        for rid in ("a","b"):
            for m in managers:m.allocate_new_blocks(rid,33792,33792)
        before={id(b) for m in managers for b in m.req_to_blocks["b"]}
        for m in managers:m.free("a")
        after={id(b) for m in managers for b in m.req_to_blocks["b"]}
        self.assertEqual(before,after);self.assertTrue(pool.null_block.is_null)
        self.assertEqual(pool.get_num_free_blocks(),315)
    def test34_c16_worker_rejects_before_profile_not_silent_smaller_batch(self):
        self.cfg.scheduler_config.max_num_seqs=16
        worker,_=self.worker()
        with self.assertRaisesRegex(ValueError,"B1 diagnostic"):worker.determine_available_memory()
        self.assertNotIn("native_profile",self.events);self.assertEqual(self.cfg.scheduler_config.max_num_seqs,16)
    def native_event_fixture(self,p,n):
        # Explicit synthetic relocation/resizing fixture from original dimensions.
        # Never persisted or represented as an actual new model LAYOUT.
        event=json.loads(F.LAYOUT_PATH.read_bytes())
        before=event["num_blocks"];after=p["native"]["num_blocks"];event["num_blocks"]=after
        by_name={name:d for pool,d in zip(p["native"]["pools"],n.values()) for name in pool["shared_by"]}
        for pool in event["pools"]:
            d=copy.deepcopy(by_name[pool["shared_by"][0]]);d["layout"]="ND_CONTIGUOUS"
            pool["raw"]=d;pool["size"]=d["logical_bytes"]
        for name,row in event["layers"].items():
            raw=by_name[name]
            for d in row["views"]:
                d["shape"][0]=d["shape"][0]//before*after
                d["storage_offset_elements"]=d["storage_offset_elements"]//before*after
                d["logical_bytes"]=d["logical_bytes"]//before*after
                d["storage_base"]=raw["storage_base"];d["storage_bytes"]=raw["storage_bytes"]
                d["data_ptr"]=d["storage_base"]+d["storage_offset_elements"]*d["element_size"]
        zero=dict(schema="kivi.actual-ascend-zeroer-writer/v1",identity=event["identity"],rank=event["rank"],
           num_blocks=after,initialized=False,segments=[],n_segs=0,page_size_el=0,block_size_el=0,
           speculative_config_is_none=True,segment_table_before=None,segment_table_after=None,
           source_sha256="e75651c8742650f1bac7dddb5f39b9a636f289b4785864c984837ec12dcdae75",
           runner_source_sha256=P.RUNNER_SHA,native_initializer_source_sha256=P.NATIVE_SHA,
           absent_guarded_noop_source_sha256="6250ca0670c4593aa2f7c4567c9c71d6cb3d8182624a985d4d4e33d5bf054666")
        path=F.LAYOUT_CONSUMER_PATH;spec=importlib.util.spec_from_file_location("_real_layout_consumer",path)
        layout=importlib.util.module_from_spec(spec);spec.loader.exec_module(layout)
        return event,zero,layout
    def test35_source_qualified_native64_and_absent_zeroer(self):
        p,n,c,_=self.allocated();event,zero,layout=self.native_event_fixture(p,n)
        proof=I.validate_native_event(p,event,n,c,zero,layout_consumer=layout)
        self.assertTrue(proof["zeroer_after_initialize_checked"]);self.assertFalse(proof["model_ready"])
    def test36_native_view_mutation_rejected_by_original_consumer(self):
        p,n,c,_=self.allocated();event,zero,layout=self.native_event_fixture(p,n)
        event["layers"][next(iter(event["layers"]))]["views"][0]["shape"][0]-=1
        with self.assertRaises(ValueError):I.validate_native_event(p,event,n,c,zero,layout_consumer=layout)
    def test37_initialized_zeroer_outside_native_rejected(self):
        p,n,c,_=self.allocated();event,zero,layout=self.native_event_fixture(p,n)
        zero.update(initialized=True,page_size_el=4,segments=[c[next(iter(c))]["key_codes"]["storage_base"]],n_segs=1)
        with self.assertRaises(ValueError):I.validate_native_event(p,event,n,c,zero,layout_consumer=layout)
    def test38_zeroer_whole_stride_and_source_checked(self):
        p,n,c,_=self.allocated();event,zero,layout=self.native_event_fixture(p,n)
        zero.update(initialized=True,page_size_el=4,segments=[next(iter(n))],n_segs=1)
        self.assertTrue(I.validate_native_event(p,event,n,c,zero,layout_consumer=layout)["zeroer_after_initialize_checked"])
        zero["source_sha256"]="0"*64
        with self.assertRaises(ValueError):I.validate_native_event(p,event,n,c,zero,layout_consumer=layout)
    def test39_same_bytes_different_gdn_spec_rejected(self):
        worker,_=self.worker();worker.determine_available_memory()
        kv=self.config_for(worker._kivi_explicit_provider["plan"])
        g=next(g for g in kv.kv_cache_groups if type(g.kv_cache_spec) is self.kv.MambaSpec)
        import dataclasses
        g.kv_cache_spec=dataclasses.replace(g.kv_cache_spec,shapes=((1,7680),(12,128,128)))
        with self.assertRaises(ValueError):worker.initialize_from_config(kv)
        self.assertNotIn("native_initialize",self.events)
    def test40_gdn_small_block_cannot_use_one_block_budget(self):
        import dataclasses
        for name,spec in self.specs.items():
            if type(spec) is self.kv.MambaSpec:self.specs[name]=dataclasses.replace(spec,block_size=1536)
        with self.assertRaises(ValueError):self.plan()
    def test41_primary_and_foreign_restore_failure_both_preserved(self):
        worker,_=self.worker();worker.determine_available_memory()
        foreign=lambda config:None
        def fail(config):
            worker.model_runner._allocate_kv_cache_tensors=foreign
            raise RuntimeError("original native failure")
        worker.model_runner.initialize_kv_cache=fail
        with self.assertRaises(BaseExceptionGroup) as caught:
            worker.initialize_from_config(self.config_for(worker._kivi_explicit_provider["plan"]))
        self.assertIs(worker.model_runner._allocate_kv_cache_tensors,foreign)
        self.assertEqual(str(caught.exception.exceptions[0]),"original native failure")
        self.assertIn("restore only",str(caught.exception.exceptions[1]))

if __name__=="__main__":
    started=time.monotonic()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ProviderTests))
    print(json.dumps({"schema":"kivi.provider-local-source-projection-tests/v1","tests":result.testsRun,
        "failures":len(result.failures),"errors":len(result.errors),"elapsed_seconds":time.monotonic()-started,
        "actual_framework":False,"actual_npu":False,"numerical_checked":False,"model_ready":False},sort_keys=True))
    sys.exit(not result.wasSuccessful())


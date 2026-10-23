"""Narrow independent source/control Ref and original owned_create mount coverage."""
from pathlib import Path


def need(v,s):
    if not v:raise ValueError(s)


def refs(value):
    if type(value)is dict:
        if set(value)=={'path','bytes','sha256'}:return [value]
        return [r for x in value.values()for r in refs(x)]
    if type(value)is list:return [r for x in value for r in refs(x)]
    return []


def _required_original(C,sr,original=()):
    # Original is the actual bind_model readset, not the full-proof return value.
    m=C.obj(sr);out=[sr,*original]
    for key in ('prepared_template','authority_ref','qualification_authority_ref','qualification_historical_short_source',
                'files','dependencies','qualification_parent_preparation_readset','short2k_helper_refs'):
        out.extend(refs(m.get(key)))
    authority=C.obj(m['qualification_authority_ref'])
    review_ref=authority['MAIN_review_ref'];C.obj(review_ref);out.append(review_ref)
    unique={}
    for r in out:
        C.checked(r);need(r['path']not in unique or unique[r['path']]==r,'conflicting independent required Ref')
        unique[r['path']]=r
    return list(unique.values())


def readset_coverage(C,required_refs,readset):
    unique={}
    for r in readset:
        C.checked(r);need(r['path']not in unique or unique[r['path']]==r,'conflicting mounted Ref')
        unique[r['path']]=r
    return index_coverage(required_refs,unique)


def index_coverage(required_refs,unique):
    # Ref bytes must already be checked by readset_coverage before this pure join.
    missing=[r['path']for r in required_refs if unique.get(r['path'])!=r]
    need(not missing,'missing independently required source/control Refs: '+repr(missing))
    return dict(required=len(required_refs),mounted_readset=len(unique))


def mount_coverage(C,required_refs,mounts,source_root):
    # Only the exact original owned SOURCE root can cover package descendants.
    # No workspace/cache parent directory exemption or privileged mount.
    if type(mounts)is list:
        pairs={}
        for row in mounts:
            dst=row['Destination'];need(dst not in pairs,'ambiguous Docker destination')
            pairs[dst]=(row['Source'],row['RW'])
        mounts=pairs
    need(type(mounts)is dict,'actual Docker/owned mount map')
    root=Path(source_root);missing=[]
    for r in required_refs:
        C.checked(r);p=Path(r['path'])
        exact=mounts.get(str(p))in [(str(p),False),[str(p),False]]
        own=root in p.parents and mounts.get(str(root))in [(str(root),False),[str(root),False]]
        if not(exact or own):missing.append(str(p))
    need(not missing,'missing exact RO guest coverage: '+repr(missing))
    return dict(required=len(required_refs),actual_mounts=len(mounts))

# SEMANTIC_CLOSURE_V2: original prefix above is reversible, never edited in place.
import ast
import hashlib
import json

ORIGINAL_REF = {"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_mount_coverage_prepare_v1/coverage.py","bytes":2767,"sha256":"1f0002c86896551c8dc126327f47ae3d56c11e093bc4af86f7500447a9b0ee96"}
Q_SOURCE = {"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/qualification_short_prepare.py","bytes":16410,"sha256":"940f26bd449f6b0577b0d590303bb68aa0f99f73f8051cc165ba4e09a955db0b"}
Q_HELPERS = {"fastpath_numeric_observer.py":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/fastpath_numeric_observer.py","bytes":8846,"sha256":"c5943291ed026402f67bbc0f6c515ba506439943c2baf55b9f12153836f6c6b2"},"fastpath_numeric_consumer.py":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/fastpath_numeric_consumer.py","bytes":11339,"sha256":"ed4499e8b64035d4a4280b895d559087c98548b853d4a28eb08be858ef6f2945"},"fastpath_numeric_sink.py":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/fastpath_numeric_sink.py","bytes":5497,"sha256":"adfd91fd06ca949bdb32dc9617bb60ffc794fd06a7aa50298d02cac1cbd1b62a"},"qualification_tap_delta.py":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/qualification_tap_delta.py","bytes":2577,"sha256":"349bd1da965eca33df950f6817d88d9e9a3759771ce589f9b901c62302fe27da"},"qualification_state_probe.py":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/qualification_state_probe.py","bytes":4413,"sha256":"d08ee36da48a4ee91ee3aa3f42fbdf16b3060ac3a0d9dfdfa7c5834316f6250e"},"qualification_smoke_join.py":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/qualification_smoke_join.py","bytes":8824,"sha256":"aa671bd5ae0686e58139d700f0f3b74a35362ad9578e3afeb5f8f2f8f6a6c7fe"},"qualification_short_prepare.py":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/qualification_short_prepare.py","bytes":16410,"sha256":"940f26bd449f6b0577b0d590303bb68aa0f99f73f8051cc165ba4e09a955db0b"},"qualification_source_validate.py":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/qualification_source_validate.py","bytes":10799,"sha256":"7cab1fbd35f49ba181265364d1b210e3e8089844246beccd6cd5c8896f33fd18"},"qualification_source_producer.py":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/qualification_source_producer.py","bytes":6853,"sha256":"eb02f1d2815a31cdcea1fb1d514a1b6d4ff769276cd8868b7ab3d59252ce6848"},"qualification_parent_renderer.py":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/qualification_parent_renderer.py","bytes":2751,"sha256":"1db3e787bd7b9a3f3b6b532fb59e9410902c70c2f1f31d5216e4e9d965bdadae"},"test_qualification_entry.py":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/test_qualification_entry.py","bytes":5849,"sha256":"3c10d6477dd1f709cb19c695aef0878db4d07c581618bd0251f0e070c2aa3ddd"}}
DONOR_NAMES = ('short_state_digest.py','compare_state_digest.py',
 'performance_client_consumer.py','bole_performance_profile.py','prepare_short_gate.py',
 'test_short_state_digest.py','test_digest_reader.py','test_short_dependency_contract.py',
 'fixtures/service_runner.py','fixtures/live_owner.py','fixtures/bole_performance_profile.py',
 'fixtures/performance_service_client.py','performance_validate.py')
PARENT_SOURCE = {'path':'/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_performance_profile_prepare_20261021/successor_layer/bound-bole-v2-r1/SOURCE_BOUND.json',
 'bytes':1368583,'sha256':'2398014d94f4365ecfb47b11de05edccff085b0efda9e474e8d557a7e5efef0d'}
AUDIT_EVIDENCE_REF = {'path':'/opt/host/vnf/austinov/run-bole-followup-preparation-evidence-20261022T230600Z-v1/BOLE_V3_READONLY_AUDIT_0dda_ORIGINAL_V1.json',
 'bytes':56903,'sha256':'2f756c8566ed990115467740fca45bab2e2212d648bda21bf72285be320147e7'}
AUDIT17 = [{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-reduction-ON-v6-common_20261022T210000Z/bole_performance_profile.py","bytes":4979,"sha256":"f1ffb4485d8963c06eab882f6c2d8b5700de74025b9663cc705e5df5c88c67f8"},{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-reduction-ON-v6-common_20261022T210000Z/compare_state_digest.py","bytes":8418,"sha256":"a7bdff799d6bc214b69e2da69d3bb8d78ee19dd73c30ef48a22317b27064c826"},{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-reduction-ON-v6-common_20261022T210000Z/fixtures/bole_performance_profile.py","bytes":4722,"sha256":"a0c911a00b4e3aa5ece0a520ba9d79c23c05808d0482b8e6a11d0361403145df"},{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-reduction-ON-v6-common_20261022T210000Z/fixtures/live_owner.py","bytes":11779,"sha256":"4aa604d5b4dd79e73382b155c86d2c333c8b21e2d56b9d979e5038d0621f687e"},{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-reduction-ON-v6-common_20261022T210000Z/fixtures/performance_service_client.py","bytes":7482,"sha256":"80e72d3712402405ff60a148de711032b6965a5b212fb3b1de1ddf683155810f"},{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-reduction-ON-v6-common_20261022T210000Z/fixtures/service_runner.py","bytes":49903,"sha256":"0f2f84f73338c6c1ac0b8c046bcaf88ff9ef81ef2c263818e24bc6e68da726ac"},{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-reduction-ON-v6-common_20261022T210000Z/performance_client_consumer.py","bytes":898,"sha256":"4f517b88ae20ac837955c8c5d1d9e8f9d49ee85d80a349899cded41ba4318c5a"},{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-reduction-ON-v6-common_20261022T210000Z/performance_validate.py","bytes":8144,"sha256":"2d5e166a7e24c04db752adb5867dbd78ab29d4cc9b7e5a0888b2ee5fba2de1a4"},{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-reduction-ON-v6-common_20261022T210000Z/prepare_short_gate.py","bytes":6875,"sha256":"475f6abe77b009aceb49af2aec974e919e40b0674da2607be8cbd4941c0a8930"},{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-reduction-ON-v6-common_20261022T210000Z/short_state_digest.py","bytes":11410,"sha256":"21d95e3cec1b90260229a4fa156981e48bbdaa9a7d466a230c63fbf4d9099ec8"},{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-reduction-ON-v6-common_20261022T210000Z/test_digest_reader.py","bytes":5204,"sha256":"93bdf35468590e9443c277591a155afe0be449a971f31d91db79b72b0a2cd821"},{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-reduction-ON-v6-common_20261022T210000Z/test_short_dependency_contract.py","bytes":1755,"sha256":"13de42975d219fd0f45b391965957d923cc4043aeffb84466c52fd2540142f4e"},{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-reduction-ON-v6-common_20261022T210000Z/test_short_state_digest.py","bytes":8178,"sha256":"a117ea35bc3d0546e66a67843798b1745f6f458db8b2d661a63c6e13786e4730"},{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/qualification_smoke_join.py","bytes":8824,"sha256":"aa671bd5ae0686e58139d700f0f3b74a35362ad9578e3afeb5f8f2f8f6a6c7fe"},{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/qualification_source_producer.py","bytes":6853,"sha256":"eb02f1d2815a31cdcea1fb1d514a1b6d4ff769276cd8868b7ab3d59252ce6848"},{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/qualification_source_validate.py","bytes":10799,"sha256":"7cab1fbd35f49ba181265364d1b210e3e8089844246beccd6cd5c8896f33fd18"},{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/test_qualification_entry.py","bytes":5849,"sha256":"3c10d6477dd1f709cb19c695aef0878db4d07c581618bd0251f0e070c2aa3ddd"}]

def _unique(rows):
    unique={}
    for r in rows:
        need(type(r)is dict and set(r)=={'path','bytes','sha256'},
             'complete semantic closure Ref3')
        need(r['path']not in unique or unique[r['path']]==r,
             'conflicting independent required Ref')
        unique[r['path']]=r
    return unique

class _Invocation:
    """Only this call owns the checked/object maps; no persistent PASS cache."""
    def __init__(self,C,initial):
        self.C=C;self.rows=_unique(initial);self.verified={};self.objects={}
    def add(self,rows):
        for path,r in _unique(rows).items():
            need(path not in self.rows or self.rows[path]==r,'conflicting independent required Ref')
            self.rows[path]=r
    def checked(self,r):
        self.add([r]);p=r['path']
        if p not in self.verified:
            self.verified[p]=self.C.checked(r)
        return self.verified[p]
    def obj(self,r):
        self.add([r])
        p=r['path']
        if p not in self.objects:
            # Same actual sourceio Path-returning ABI as C.obj; hash before JSON.
            self.objects[p]=json.loads(self.checked(r).read_bytes())
        return self.objects[p]
    def finish(self):
        for r in self.rows.values():self.checked(r)
        return list(self.rows.values())

def required(C,sr,original=()):
    call=_Invocation(C,[sr,*original]);m=call.obj(sr)
    for key in ('prepared_template','authority_ref','qualification_authority_ref',
                'qualification_historical_short_source','files','dependencies',
                'qualification_parent_preparation_readset','short2k_helper_refs'):
        call.add(refs(m.get(key)))
    authority=call.obj(m['qualification_authority_ref'])
    call.obj(authority['MAIN_review_ref'])
    q=call.checked(Q_SOURCE).read_bytes()
    tree=ast.parse(q);nodes=[n for n in tree.body if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name)and t.id=='HELPERS'for t in n.targets)]
    need(len(nodes)==1 and ast.literal_eval(nodes[0].value)==tuple(Q_HELPERS),
         'exact pinned Q source and complete HELPERS order/list')
    need(Q_HELPERS['qualification_short_prepare.py']==Q_SOURCE,
         'Q self identity inside semantic preparation readset')
    call.add(Q_HELPERS.values())
    historical=call.obj(m['qualification_historical_short_source'])
    call.add([historical['files'][name]for name in DONOR_NAMES])
    # The actual original P.read_parent reads every one of this parent's391 files.
    # They are already present in V3 dependencies, but keep the edge explicit.
    need(m['followup_parent_source']==PARENT_SOURCE,'same pinned P.read_parent source')
    parent=call.obj(PARENT_SOURCE);call.add(parent['files'].values())
    return call.finish()

def readset_coverage(C,required_refs,readset):
    unique=_unique(readset)
    # Detect every conflict before the bulk checks; each unique checked once.
    for r in unique.values():C.checked(r)
    return index_coverage(required_refs,unique)

def inverse(raw=None):
    """Return exact original coverage.py, proving no old mount/math gate changed."""
    raw=Path(__file__).read_bytes()if raw is None else raw
    marker=b'\n# SEMANTIC_CLOSURE_V2:'
    need(raw.count(marker)==1,'one v2 independent semantic extension')
    prefix=raw.split(marker,1)[0]
    need(prefix.count(b'def _required_original(')==1,'exact original renamed seam')
    old=prefix.replace(b'def _required_original(',b'def required(',1)
    need(len(old)==ORIGINAL_REF['bytes']and hashlib.sha256(old).hexdigest()==ORIGINAL_REF['sha256'],
         'entire original coverage bytes/inverse retained')
    return old

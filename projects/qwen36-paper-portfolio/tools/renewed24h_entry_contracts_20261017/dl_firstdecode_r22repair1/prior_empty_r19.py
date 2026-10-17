"""Typed failed empty R19 reservation continuation; never rewrites that journal."""
import os,stat,types
from pathlib import Path
import stream_closed_tree as S
ROOT=Path('/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061')
OWNER=dict(path='/opt/host/vnf/austinov/run-deltalog-FIRSTDECODE101R19-main-NEW24H_FIRSTDECODE101R19_001/RESULT.json',bytes=5486,sha256='90a3ade40d09a3d04f3f65a7f2323fb70422c531480a65bbd9821b8991bfe678')
SOURCE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-first-real-decode-owned-renew24h-v1-101-repair19-20261017-001/SOURCE_MANIFEST.json',bytes=253011,sha256='a5f9678df3c96035891b6bb0b1bf48c4c9bffc484f6d414538008d0593a98c81')
TEMPLATE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-first-real-decode-owned-renew24h-v1-101-repair19-20261017-001/SOURCE_TEMPLATE.json',bytes=234563,sha256='adca9c401d3beaa22fb560c9be9a0f8ec659bacf449f608502877dde32d1ea89')
JOURNAL=dict(path=(ROOT/'MODEL_SNAPSHOTS_LEDGER.R19.json').as_posix(),bytes=2618,sha256='48adca9b216569ef533d812018f93a5302e3d58eafeb6a24a52647464fca5867')
LEAF=ROOT/'first-real-decode-model-snapshots-renew24h-20261017-001'
OPT=Path(OWNER['path']).parent
PRIMARY="ValueError('source-original host plus CLI cumulative512MiB')"
def validate(O,K):
 owner=O.obj(OWNER);source=O.obj(SOURCE);journal=O.obj(JOURNAL)
 O.need(owner['schema']=='deltalog.actual-owned-dispatch-smoke/v025'and owner['source']==SOURCE and owner['status']=='failed'and owner['primary']==PRIMARY and owner['secondary']==[]and owner['all_created_containers_release_verified']is True,'exact failed R19 owner retained; not a numeric/result PASS')
 O.need(source['prepared_template']==TEMPLATE and source['prepared_only']is False and source['output_root']==str(OPT),'exact actual R19 source/template/output')
 O.need(owner['owned_containers']==[dict(stage=str(OPT/'cpu-preflight'),cid=None,exact_owned_release_verified=None)],'R19 never created a container; no borrowed stopped CID')
 p=owner['post_work_verification'];O.need(p['source_after']is True and p['metadata_after_hash']is True and p['registered_cap_seconds']==900 and 0<p['actual_cap_seconds']<=900 and 0<=owner['elapsed']<=2700 and 0<=owner['cleanup_seconds']<=270,'original R19 complete final source/data metadata fence and original timers')
 O.need(journal['schema']=='deltalog.model-snapshots-reservation/v1'and journal['source']==SOURCE and journal['leaf']==str(LEAF)and journal['combined_opt_root']==str(OPT)and journal['legacy_ledger_written']is journal['numeric_qualified']is False and journal['budget_bytes']==32*2**30,'original journal identity/cap/flags unchanged')
 st=LEAF.lstat();O.need(stat.S_ISDIR(st.st_mode)and(st.st_dev,st.st_ino,st.st_mtime_ns,st.st_ctime_ns)==(64770,6029409,1792229108508000000,1792229108508000000)and not any(LEAF.iterdir())and all(not q.is_symlink()for q in(LEAF,*LEAF.parents)),'actual exact R19 empty payload root unchanged')
 # Reuse the exact canonical command/FD/shared-map scan for BOTH old roots.
 # No PID exemption. Binder's separately reviewed exact current-PID Ref-data
 # rule, if installed in K, continues to scan its FD/maps unchanged.
 ns=dict(K.__dict__,SOURCE=SOURCE,PHASES=('payload','control'),leaf=lambda i:(LEAF,OPT)[i])
 check=types.FunctionType(K.no_writers.__code__,ns,'no_writers',K.no_writers.__defaults__,K.no_writers.__closure__)
 proof=check();O.need(not any(LEAF.iterdir())and(st.st_dev,st.st_ino,st.st_mtime_ns,st.st_ctime_ns)==(lambda z:(z.st_dev,z.st_ino,z.st_mtime_ns,z.st_ctime_ns))(LEAF.lstat()),'empty leaf stable across complete writer scan')
 return dict(schema='deltalog.closed-failed-empty-attempt/v1',owner=OWNER,source=SOURCE,journal=JOURNAL,leaf=str(LEAF),original_primary=PRIMARY,actual_payload_bytes=0,original_nominal_budget_bytes=32*2**30,prior_lease_terminal=True,legacy_ledger_written=False,old_journal_not_rewritten=True,current_no_writers=proof,numeric_qualified=False)
def refs():return[OWNER,SOURCE,TEMPLATE,JOURNAL]

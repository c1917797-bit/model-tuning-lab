"""Exact source-owned disk-ledger seams only; original algorithms/outer caps intact."""
def need(v,s):
 if not v:raise ValueError(s)
def once(s,a,b):
 need(s.count(a)==1,'one exact disk-ledger seam '+a[:70]);return s.replace(a,b,1)
PREIMAGES={
 'related160':dict(bytes=11384,sha256='3f48559f18744bd0c52c625fdfb1fc2ae42bfa26cd7a4bbfad63ef830ee18fe8'),
 'formal':dict(bytes=9831,sha256='9755a6053ca0518e43dc592727490a18d836e771c1a167a74716a06725a09bb0')}
def terminal(raw,domain):
 import hashlib
 need(type(domain)is str and domain in PREIMAGES,'explicit reviewed followup domain')
 expected=PREIMAGES[domain]
 need(type(raw)is bytes and len(raw)==expected['bytes']and hashlib.sha256(raw).hexdigest()==expected['sha256'],
      'exact actual domain terminal preimage, never guessed short8 source')
 s=raw.decode()
 s=once(s,'    import fa_stream_capture as FS','    import disk_ledger as D\n    import fa_stream_capture as FS')
 if domain=='related160':
  marker='        budget.append(dict(rank=rank,combined_actual_metadata_bytes=combined_bytes,'
  after="        disk_refs={}\n        def disk_add(target,rr):\n            C.checked(rr)\n            need(rr['path']not in target or target[rr['path']]==rr,'one complete disk Ref per path; never swallow a conflicting identity')\n            target[rr['path']]=rr\n        file_refs=[C.ref(p)for p in all_files]\n        for rr in list(combined.values())+file_refs+archive['references']:disk_add(disk_refs,rr)\n        archive_json=[rr for rr in archive['references']if rr['path'].endswith('.json')]\n        need(sum(rr['bytes']for rr in archive_json)==archive['actual_archive_metadata_bytes'],'same original FS JSON classification and complete archive metadata charge')\n        disk_metadata={}\n        for rr in list(combined.values())+[rr for rr in file_refs if not rr['path'].endswith('.pt')]+archive_json:disk_add(disk_metadata,rr)\n        need(all(path in disk_refs and disk_refs[path]==rr for path,rr in disk_metadata.items()),'metadata is a complete strict subset of the disk union')\n        disk_total=sum(rr['bytes']for rr in disk_refs.values())\n        disk_json=sum(rr['bytes']for rr in disk_metadata.values())\n        need(disk_json<=64*2**20,'ONE complete legacy STATE new and archive metadata union within original64MiB')\n        disk=D.rank_terminal(dict(C=C,m=m,source=source,used=0,metadata_bytes=disk_json),rank=rank,source=source,total=disk_total,json_bytes=disk_json)\n        budget.append(dict(disk,rank=rank,combined_actual_metadata_bytes=combined_bytes,"
 else:
  marker='        budget.append(dict(rank=rank,actual_total_bytes=total,actual_JSON_bytes=json_bytes,'
  after="        disk=D.rank_terminal(dict(C=C,m=m,source=source,used=0,metadata_bytes=json_bytes),rank=rank,source=source,total=total,json_bytes=json_bytes)\n        budget.append(dict(disk,rank=rank,actual_total_bytes=total,actual_JSON_bytes=json_bytes,"
 s=once(s,marker,after)
 if domain=='related160':
  s=once(s,'combined_readset=list(combined.values()),actual_total_bytes=total,actual_JSON_bytes=json_bytes,',
   'combined_readset=list(combined.values()),actual_total_bytes=disk_total,actual_JSON_bytes=disk_json,collector_actual_total_bytes=total,collector_actual_JSON_bytes=json_bytes,')
 s=once(s,'    RAM.complete(ram_identities)','    disk_sum=D.all_terminal(C,m,source,budget,shared=ram_shared)\n    RAM.complete(ram_identities)')
 flag='intermediate160_numeric_scope_passed'if domain=='related160'else'short8_numeric_scope_passed'
 s=once(s,'actual_evidence_budget=budget,'+flag+'=True,',
  'actual_evidence_budget=budget,actual_disk_budget=disk_sum,'+flag+'=True,')
 if domain=='related160':
  s=once(s,"short8_numeric_scope_passed=result['short8_numeric_scope_passed']",
           "intermediate160_numeric_scope_passed=result['intermediate160_numeric_scope_passed']")
 return s.encode()

def adapt(files,*,helper,domain):
 out=dict(files);need('disk_ledger.py'not in out,'no stacked disk adapter')
 s=out['fa_block_store.py'].decode()
 s=once(s,'RAW_CAP=2**30','import disk_ledger as D\nRAW_CAP=D.template_disk_cap()')
 s=once(s,"   need(c['used']+len(raw)+CHECKPOINT+META_CAP<=RAW_CAP,'original1GiB raw/checkpoint/metadata before write')",
        "   D.archive_before(c,len(raw),metadata=metadata)")
 out['fa_block_store.py']=s.encode()
 s=out['runtime_joint_ledger.py'].decode()
 s=once(s,'from pathlib import Path','from pathlib import Path\nimport disk_ledger as D')
 s=once(s,'        return total','        D.wire_total(self.c,self.first,wire)\n        return total')
 s=once(s,'        self.quota = min(FRAME_WIRE_CAP, available)',
        "        available=min(available,D.wire_room(self.c))\n        if available<=0:raise BudgetReject('no positive profile disk wire quota')\n        self.quota = min(FRAME_WIRE_CAP, available)")
 out['runtime_joint_ledger.py']=s.encode()
 s=out['fastpath_numeric_sink.py'].decode()
 s=once(s,'import runtime_joint_ledger as J','import runtime_joint_ledger as J\nimport disk_ledger as D')
 s=once(s,'    ref=durable(c[\'C\'],path,value)',"    D.metadata_before(c,len(raw))\n    ref=durable(c['C'],path,value)")
 s=once(s,"    C.need(c['used']+ref['bytes']<=6375342080,",
        "    D.pt_before(c,ref['bytes'])\n    C.need(c['used']+ref['bytes']<=6375342080,")
 out['fastpath_numeric_sink.py']=s.encode()
 s=out['fa_stream_capture.py'].decode()
 s=once(s,'import fa_block_store as B','import fa_block_store as B\nimport disk_ledger as D')
 s=once(s," need(total<=B.RAW_CAP and metadata<=B.META_CAP,'actual full archive byte accounting')",
        " D.rank_terminal(dict(C=C,m=m,source=source,used=0,metadata_bytes=metadata),rank=rank,source=source,total=total,json_bytes=metadata)\n need(total<=B.RAW_CAP and metadata<=B.META_CAP,'actual full archive byte accounting')")
 out['fa_stream_capture.py']=s.encode()
 out['qualification_smoke_join.py']=terminal(out['qualification_smoke_join.py'],domain)
 out['disk_ledger.py']=helper
 delta={n:dict(before=files.get(n),after=raw)for n,raw in out.items()if files.get(n)!=raw}
 need(set(delta)=={'disk_ledger.py','fa_block_store.py','fa_stream_capture.py','runtime_joint_ledger.py','fastpath_numeric_sink.py','qualification_smoke_join.py'},'only shared disk boundaries, no oracle/math changes')
 return out,delta
def inverse(files,delta):
 out=dict(files)
 for n,v in delta.items():
  need(out[n]==v['after'],'exact disk inverse')
  if v['before']is None:out.pop(n)
  else:out[n]=v['before']
 return out

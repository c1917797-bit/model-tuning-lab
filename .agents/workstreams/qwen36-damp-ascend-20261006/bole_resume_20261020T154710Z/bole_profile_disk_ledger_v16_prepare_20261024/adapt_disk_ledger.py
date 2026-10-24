"""Exact source-owned disk-ledger seams only; original algorithms/outer caps intact."""
def need(v,s):
 if not v:raise ValueError(s)
def once(s,a,b):
 need(s.count(a)==1,'one exact disk-ledger seam '+a[:70]);return s.replace(a,b,1)
def adapt(files,*,helper):
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
 s=out['qualification_smoke_join.py'].decode()
 s=once(s,'    import fa_stream_capture as FS','    import disk_ledger as D\n    import fa_stream_capture as FS')
 s=once(s,'        budget.append(dict(rank=rank,actual_total_bytes=total,actual_JSON_bytes=json_bytes,',
        "        disk=D.rank_terminal(dict(C=C,m=m,source=source,used=0,metadata_bytes=json_bytes),rank=rank,source=source,total=total,json_bytes=json_bytes)\n        budget.append(dict(disk,rank=rank,actual_total_bytes=total,actual_JSON_bytes=json_bytes,")
 s=once(s,'    RAM.complete(ram_identities)','    disk_sum=D.all_terminal(C,m,source,budget,shared=ram_shared)\n    RAM.complete(ram_identities)')
 s=once(s,'actual_evidence_budget=budget,short8_numeric_scope_passed=True,',
        'actual_evidence_budget=budget,actual_disk_budget=disk_sum,short8_numeric_scope_passed=True,')
 out['qualification_smoke_join.py']=s.encode();out['disk_ledger.py']=helper
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

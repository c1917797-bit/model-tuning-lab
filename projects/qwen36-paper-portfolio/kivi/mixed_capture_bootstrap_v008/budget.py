"""Bounded proposal, not measured fit. A source change is needed for any budget change."""
CUTOFF=1791788425
NPU_SECONDS=5400
CPU_SECONDS=43200
CLEANUP_SECONDS=90
WORKSPACE_BYTES=160*1024**3
# 576 whole1536 rows * measured32769-row19.758s =11380.608s (output oracle only).
# CPU cap12h is a conservative scheduling allowance, NOT a proved total upper:
# 3x output projection34141.824s plus9058.176s writer/hash/I/O/cleanup.
# Unmeasured codec/reference can still exhaust it. Fail, retain raw, never sample.
def require_fit(start_epoch,phase):
 seconds=NPU_SECONDS if phase=="capture" else CPU_SECONDS
 if type(start_epoch) not in(int,float) or start_epoch+seconds>CUTOFF:
  raise ValueError("complete bounded phase cannot fit unchanged absolute cutoff")
 return start_epoch+seconds
def preregister(now):
 if now+NPU_SECONDS+CPU_SECONDS>CUTOFF:
  raise ValueError("complete capture+CPU budget cannot fit absolute cutoff")
 return dict(capture_seconds=NPU_SECONDS,cpu_seconds=CPU_SECONDS,
  total_reserved_seconds=NPU_SECONDS+CPU_SECONDS,cutoff_epoch=CUTOFF,
  CPU_output_projection_seconds=11380.608,CPU_budget_is_measured_upper_bound=False,
  unknown_writer_hash_io_cost=True,workspace_bytes=WORKSPACE_BYTES)

"""One entrypoint, default OFF; the frozen v2 register is called exactly once."""
def register():
 import os
 if os.environ.get("DAMP_ADMISSION_TRACE_ENABLE")!="1":return
 from v3_contract import source_contract
 source_contract()
 from v3_before import install
 return install()

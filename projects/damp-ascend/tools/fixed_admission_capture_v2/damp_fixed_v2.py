"""Unique NEW plugin entrypoint. DefaultOFF returns before runtime imports."""
def register():
    import os
    if os.environ.get("DAMP_ADMISSION_TRACE_ENABLE")!="1": return
    from v2_contract import source_contract
    source_contract()
    from v2_observer import register as install
    return install()

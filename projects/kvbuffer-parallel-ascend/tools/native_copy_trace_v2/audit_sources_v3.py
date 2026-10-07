#!/usr/bin/env python3
"""Source-only successor; checks host/kernel namespace isolation, not numeric parity."""
import json
from pathlib import Path
import audit_sources
def audit():
    result=audit_sources.audit()
    op=audit_sources.OP
    host=(op/"op_extension/native_tiling.h").read_text()
    wrapper=(op/"op_extension/qwen36_native_recurrent_copy_trace_v2_torch.cpp").read_text()
    audit_sources.require("namespace NativeTraceHost {" in host and
                          "using NativeRecurrentCopyTraceV2::NativeRecurrentCopyTraceV2TilingData;" in host and
                          "namespace NativeRecurrentCopyTraceV2 {" not in host,
                          "host constexpr cannot collide with device MAX_MTP")
    audit_sources.require("NativeTraceHost::make_tiling(" in wrapper and
                          "NativeRecurrentCopyTraceV2::make_tiling(" not in wrapper,
                          "actual host tiling caller")
    result["checks"]+=["host_kernel_namespace_isolation","actual_host_namespace_caller"]
    result["schema"]="kvbp.native-recurrent-source-audit/v3"
    result["build_only_successor_of"]="v2"
    return result
if __name__=="__main__":print(json.dumps(audit(),indent=2))

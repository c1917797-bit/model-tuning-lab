# SPDX-License-Identifier: Apache-2.0
"""NO-device preparation tests; no Torch/Docker/build/NPU imported."""
import hashlib
import json
from pathlib import Path
from cases import (GUARDS,NAMES,LUT_HASHES,lut_hashes,labeled_fixtures,
                   endpoint_rows,proposal_rows,golden,lifecycle_rows)
BASE=Path(__file__).resolve().parent
def control_contracts():
    import argparse
    import copy
    from unittest.mock import patch
    import run_certificate_gate as runner
    class SimTensor:
        def __init__(self,value,fault=None): self.value=value; self.fault=fault
        def cpu(self):
            if self.fault=="cpu": raise RuntimeError("simulated poisoned D2H")
            return self
        def clone(self):
            if self.fault=="clone": raise RuntimeError("simulated clone failure")
            return self.value
    saves=[]
    save=lambda observation,path: saves.append((observation,path))
    observation=runner.save_observation(save,"memory-only",returns=[
        SimTensor([1,2]),SimTensor(0,"cpu"),SimTensor(0,"clone")],
        roots=[SimTensor([3]),SimTensor(0,"cpu")],
        dispatch_error="ORIGINAL_DISPATCH_ERROR",before=["saved_before"],
        rows=["saved_fixture"],golden_interiors=["saved_golden"])
    assert len(saves)==1 and observation["dispatch_error"]=="ORIGINAL_DISPATCH_ERROR"
    assert observation["outputs_full"]==[[1,2],None,None]
    assert observation["after"]==[[3],None]
    assert len(observation["output_copy_errors"])==2 and len(observation["input_copy_errors"])==1
    assert observation["before"]==["saved_before"] and observation["rows"]==["saved_fixture"]
    assert observation["golden_interiors"]==["saved_golden"]
    observation=runner.save_observation(save,"memory-no-return",returns=None,
        roots=[SimTensor(0,"cpu")],dispatch_error="ORIGINAL_ADMISSION_ERROR",
        before=["safe_cpu_before"])
    assert len(saves)==2 and observation["outputs_full"] is None
    assert observation["after"]==[None] and observation["output_copy_errors"]==[]
    observation=runner.save_observation(save,"memory-ok",returns=[SimTensor([7])],
        roots=[SimTensor([8])],dispatch_error=None)
    assert observation["outputs_full"]==[[7]] and observation["after"]==[[8]]
    assert not observation["output_copy_errors"] and not observation["input_copy_errors"]
    # Synthetic file-reader/hasher only. Not a build or library load proof.
    sha="a"*64
    runtime={n:sha for n in runner.SOURCE_NAMES}
    compiled={n:runtime[n] for n in runner.COMPILED_NAMES}
    receipt={"schema":"damp_integer_certificate_build_v1",
        "status":"compiled_no_device","npu_executed":False,
        "physical_soc_runtime_observed":False,"commands":[
            {"command":["cmake","-S","synthetic"],"exit_code":0,"log_sha256":sha},
            {"command":["cmake","--build","synthetic"],"exit_code":0,"log_sha256":sha}],
        "image_id":runner.EXPECTED_IMAGE_ID,"npu_arch":"dav-2201",
        "library_sha256":sha,"sources":compiled,
        "cann_identity":{"version":"9.1.0","component":"opp",
            "version_info_path":"/usr/local/Ascend/cann-9.1.0/opp/version.info",
            "version_info_sha256":sha}}
    source_doc={"sources":compiled}  # actual compiler manifest has no schema
    runtime_doc={"schema":"damp_integer_certificate_runtime_sources_v1","sources":runtime}
    args=argparse.Namespace(source_manifest="compiled-doc",runtime_manifest="runtime-doc",
                            build_receipt="receipt-doc",library="synthetic.so",library_sha256=sha)
    def invoke(sdoc=source_doc,rdoc=runtime_doc,bdoc=receipt):
        data={"compiled-doc":sdoc,"runtime-doc":rdoc,"receipt-doc":bdoc}
        with patch.object(runner,"read_json",side_effect=lambda p:data[p]), \
             patch.object(runner,"digest",return_value=sha):
            return runner.source_checks(args)
    good=invoke()
    assert len(good["compiled_sources"])==9 and len(good["runtime_sources"])==16
    assert set(good["compiled_sources"]).issubset(good["runtime_sources"])
    bads=[]
    for key,value in (("status","failed"),("npu_executed",True),
                      ("physical_soc_runtime_observed",True),("image_id","wrong-image"),
                      ("npu_arch","dav-3510"),("library_sha256","b"*64)):
        b=copy.deepcopy(receipt); b[key]=value; bads.append((source_doc,runtime_doc,b))
    b=copy.deepcopy(receipt); b["commands"][1]["exit_code"]=2
    bads.append((source_doc,runtime_doc,b))
    b=copy.deepcopy(receipt); del b["cann_identity"]
    bads.append((source_doc,runtime_doc,b))
    b=copy.deepcopy(receipt); b["cann_identity"]["component"]="all-sdk-guessed"
    bads.append((source_doc,runtime_doc,b))
    b=copy.deepcopy(receipt); b["sources"][runner.COMPILED_NAMES[0]]="b"*64
    bads.append((source_doc,runtime_doc,b))
    bads.append(({"sources":runtime},runtime_doc,receipt))  # old16-as-compiled mismatch
    b=copy.deepcopy(runtime_doc); b["sources"]["cases.py"]="b"*64
    bads.append((source_doc,b,receipt))
    b=copy.deepcopy(runtime_doc); b["sources"].pop("cases.py")
    bads.append((source_doc,b,receipt))
    for sdoc,rdoc,bdoc in bads:
        try: invoke(sdoc,rdoc,bdoc)
        except AssertionError: continue
        raise AssertionError("synthetic bad compiled/runtime/build binding accepted")
    asc=(BASE/"op_kernel/certificate_probe_kernel.asc").read_text()
    arch="#if defined(__NPU_ARCH__)"
    assert asc.index("kernel_operator.h")<asc.index(arch)
    assert asc.index("probe_plan.h")<asc.index(arch)
    # Source-only host projection: declaration alone is insufficient to emit
    # the ASC host launcher. Actual symbol resolution remains MAIN's ELF gate.
    depth=0; projected=[]
    for line in asc.splitlines():
        if line==arch: depth+=1; continue
        if line=="#endif": depth-=1; assert depth>=0; continue
        if not depth: projected.append(line)
    assert depth==0
    host="\n".join(projected)
    assert host.count('extern "C" __global__ __vector__ void')==1
    assert "GM_ADDR tilingGm)\n{\n}" in host
    assert '#include "certificate_probe.h"' not in host
    assert "DampIntegerProbe::Kernel" not in host
    assert asc.count(arch)==2 and asc.count('extern "C" __global__ __vector__ void')==1
    # Preserve the exact device algorithm body from the archived actual v2.
    prior=(BASE/"audit/kernel-source-v2.asc.txt").read_text()
    body=prior.split("\n{\n",1)[1].split("\n}",1)[0]
    assert "\n{\n"+arch+"\n"+body+"\n#endif\n}" in asc
    assert "\"soc\"" not in str(receipt)  # compile target is not a runtime observation
    return {"failure_save_simulations":3,"receipt_admission_negatives":len(bads),
            "host_boundary_source_contract":True}

def run():
    controls=control_contracts()
    assert lut_hashes()==LUT_HASHES
    rows=labeled_fixtures()
    assert len(GUARDS)==len(set(GUARDS))==len(NAMES)==7
    endpoints=accepts=domain_false=0
    for row in endpoint_rows():
        g=golden(row)
        assert g[5:]==(0,1) and g[0]==0
        domain_false+=not g[3]; endpoints+=1
    assert endpoints==254*12*127
    certificates=0
    for row in proposal_rows(rows):
        g=golden(row)
        if g[0]: assert g[5]==(-row["proposal"] if row["x_bits"]>>31 else row["proposal"])
        accepts+=g[0]; certificates+=1
    for count in (64,896):
        for repeat in range(20):
            rs=lifecycle_rows(rows,count,repeat)
            assert len(rs)==count
            for r in rs: assert len(golden(r))==7
    # Source-bound control-flow contracts. Not a C++ compiler/device proof.
    wrapper=(BASE/"op_extension/certificate_torch.cpp").read_text()
    kernel=(BASE/"op_kernel/certificate_probe.h").read_text()
    register=(BASE/"op_extension/register.cpp").read_text()
    assert wrapper.index("const auto host=n.to(at::kCPU)")<wrapper.index("qwen36_damp_integer_certify_bits_kernel<<<")
    assert "magnitudes[i]>=0 && magnitudes[i]<=127" in wrapper
    assert 'stream(false)' in wrapper and 'RunOpApi("Qwen36DampIntegerCertifyBits"' in wrapper
    assert "get_npu_format" in wrapper and "storage.nbytes()" in wrapper
    assert "HardEvent::V_S" in kernel and "HardEvent::S_V" in kernel
    assert "scaleDomain && out[3].GetValue(lane)" in kernel
    assert "scaleDomain && out[4].GetValue(lane)" in kernel
    assert "GatherMask(" not in kernel
    assert "Meta,m" in register
    print(json.dumps({"status":"software_contract_pass","endpoint_rows":endpoints,
      "endpoint_lower_outside_domain":domain_false,"proposal_rows":certificates,
      "accepted_certificates":accepts,"fixture_rows":len(rows),
      "unsafe_acceptances":0,"lut_hashes":LUT_HASHES,"cxx_compiled":False,
      "asc_compiled":False,"npu_executed":False,"production_enabled":False,
      "graph_supported":False,"gather_mask_compaction_implemented":False,**controls},sort_keys=True))
if __name__=="__main__": run()

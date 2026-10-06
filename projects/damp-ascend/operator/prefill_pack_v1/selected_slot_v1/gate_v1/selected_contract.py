"""Stdlib-only, source-bound selected prefill correctness contract. Default OFF."""
from pathlib import Path
import hashlib
import json
import time

NAMESPACE = "qwen36_damp_selected_prefill_v1"
SELECTED_MANIFEST_SHA = "5670a88c77fde9fd81abadcb7c88d2b3f6bb684928e24f445a3a1d3a67f0a8bf"
SELECTED_BUILD_SHA = "50f161e606a7faa567b7588300f526f3294c7ecfbf69a88edaa8898b09d1825f"
ALL_BATCH_BUILD_SHA = "a9c8a6824f3f0948d4395eabcc731a0b4e0da6a7f94d6053d3159cf008e23d36"
ALL_BATCH_SO_SHA = "a802d2584f6342acd198406a94c4a4cb3dd0e9cd6cc360569e58f3f117ac0ade"
ALL_BATCH_MANIFEST_SHA = "a115f00eb371476ad96c440fca53db2c383e2f5f11c9b62e80214543754c1958"
SELECTED_SO_SHA = "28684cb4f502ead28fd9974a54f420d0ec027de19ccc6728ba3942209fc910d7"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
OPP_SHA = "841279757459d4eabc1c8cfea69d3e1dc0fc9db3eb0c18100294cd5c1301b9e6"
COMPILED = {
  "projects/damp-ascend/operator/prefill_pack_v1/exact_float_div_bits.h": "bca2ab982ac57ebed71efa4145281b5ee37faa5ec46cc0beccddf9d83eb2ae04",
  "projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/CMakeLists.txt": "269966c5f70b5b1d57ff8c0f7e53b9c98bef6b96765829f9cb5d30617ac877ac",
  "projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/op_extension/ops.h": "8554be1ec4c86b81f472787ae98c6e2a51ec4fad2e422bcdadef3af9dbdf481d",
  "projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/op_extension/register.cpp": "bd94f4c761769bb40636f3b12ed5c6cabc2aae1316d344143bab19fb8c3c5571",
  "projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/op_extension/selected_prefill_torch.cpp": "dd03d2c2b56397566507952fc962b3336ac054ebd85b803eb6cd892c0b0e2236",
  "projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/op_kernel/prefill_plan.h": "449c36746067c784f0f7612e526ea836556247aa0b660a68d2c0b04b75a11aa1",
  "projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/op_kernel/selected_prefill.h": "e2355651657152c8b3bc530f4cab805d4bae6cbcfec329f11e018150196e5c30",
  "projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/op_kernel/selected_prefill_kernel.asc": "87a67006ad535a9101304f329ad496a1dcc291f259e1b87bab4191f3ca5f01d4",
  "projects/damp-ascend/operator/production_integer_compaction_v1/op_kernel/qwen36_gdn_damp_integer_compaction_v1_decode_tiling.h": "ac40d62d8a37f8825ffb085beeb133a8b04f359e0e3a34bf4bca6ebf854224cc",
  "projects/damp-ascend/operator/quantizer/exact_quantizer_bits.h": "f5d380534d34d6e4148d94fcfec35b294ca8ca38d09316d98b11e7f645ff6169",
  "projects/damp-ascend/operator/quantizer/fast_integer_certificate/integer_certificate_ascendc.h": "e96cbd0565cdb879016e1970753342151936e3d45bafd375530d1d27cfd7b9cb"
}
REFERENCE = {
  "CMakeLists.txt": "f921cc3580e5a3ec3f0fb02130108249626ac918b5275ec5b857e6ac11a3deba",
  "LICENSE-APACHE": "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4",
  "LICENSE-CANN": "5ee30bd08e3c47a51591e380d04cfc4cf90692c18a1b439abd85cf2f105dee8d",
  "README.md": "c139d70a3622a0a37329570c2668ee152ecc28740f0b959c9e54c35944874c1e",
  "check_source_contract.py": "5e4a09325b73729c96309cfb13867358d9ce725e8f3b083265556acb6337223a",
  "op_extension/native_sr_reference_torch.cpp": "71c69bae01a6e15e3f4b9f9cac80bcab08916acf83ec08412eb06653b8f4b9ba",
  "op_extension/ops.h": "1b4b34b3588d3d4d6325221ad702e43f082c4940f6575ab927e2cc4d5a6e2282",
  "op_extension/register.cpp": "fa485af95d0a55f009226db77f6af7294d018e1d8b6a5fd08f27aaca2f34845a",
  "op_kernel/native_sr_reference.h": "8816198563deaa460aa50dfd993e94b1e8483173fdfa65ed4af83104f9474896",
  "op_kernel/native_sr_reference_kernel.asc": "296f2cd699ab228d347cba1783b614c990d9affcc2188debe82b606cf78d6c3c"
}
ALL_BATCH_COMPILED = {
  "projects/damp-ascend/operator/all_batch_wrapper_v3/CMakeLists.txt": "febb3e7e7dd955c98c8ca1e054afedeb77cdd6512040cf4d3551a950deb24561",
  "projects/damp-ascend/operator/all_batch_wrapper_v3/op_extension/ops.h": "8f103382816ac8e4206ebd24f996f41186f5d92f6ace9918362936191c7e8b84",
  "projects/damp-ascend/operator/all_batch_wrapper_v3/op_extension/qwen36_gdn_damp_all_batch_v3_decode_torch.cpp": "b8c0304b9efb13c03537894549c9e3028bd7a4e866305b2b86122875f5b45812",
  "projects/damp-ascend/operator/all_batch_wrapper_v3/op_extension/register.cpp": "cdfac8e115b450262d372aa76b464fb1c4948d88b8f906cef4e9c7fe2950ac08",
  "projects/damp-ascend/operator/all_batch_wrapper_v3/op_kernel/qwen36_gdn_damp_all_batch_v3_decode.h": "16505660b4c4714bfb3c7ab5cbc3b5330eec88337f693ecdd4c48a79ab2db60e",
  "projects/damp-ascend/operator/all_batch_wrapper_v3/op_kernel/qwen36_gdn_damp_all_batch_v3_decode_kernel.asc": "5bfc1847a8a117b9ca0b8fcdf947a41a876009bf593174dcebdfc91f77e1b66b",
  "projects/damp-ascend/operator/production_integer_compaction_v1/op_kernel/qwen36_gdn_damp_integer_compaction_v1_decode_tiling.h": "ac40d62d8a37f8825ffb085beeb133a8b04f359e0e3a34bf4bca6ebf854224cc",
  "projects/damp-ascend/operator/quantizer/exact_quantizer_bits.h": "f5d380534d34d6e4148d94fcfec35b294ca8ca38d09316d98b11e7f645ff6169",
  "projects/damp-ascend/operator/quantizer/fast_integer_certificate/integer_certificate_ascendc.h": "e96cbd0565cdb879016e1970753342151936e3d45bafd375530d1d27cfd7b9cb"
}
LIMITS = {"state": 1e-5, "output": 0.00303}
GUARD = 0x13579bdf
REGIONS = ("high", "low", "scales")

def require(ok, message):
    if not ok: raise RuntimeError(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def bound_json(path, digest):
    require(sha(path) == digest, "JSON SHA mismatch: " + str(path))
    return json.loads(Path(path).read_text())

def check_sources(repo, sources):
    require(isinstance(sources, dict) and sources, "empty source closure")
    for path, digest in sources.items():
        target = Path(repo)/path
        require(target.is_file() and sha(target) == digest, "source mismatch: " + path)
    return sources

def validate_build(receipt):
    require(receipt.get("schema") == "damp-selected-prefill-build/v1" and
            receipt.get("status") == "compiled_no_device", "actual selected build receipt required")
    require(receipt.get("namespace") == NAMESPACE and receipt.get("sources") == COMPILED and
            receipt.get("source_manifest_sha256") == SELECTED_MANIFEST_SHA and
            receipt.get("library_sha256") == SELECTED_SO_SHA, "build/source/SO identity")
    require(receipt.get("image_id") == IMAGE and receipt.get("npu_arch") == "dav-2201" and
            receipt.get("npu_executed") is False and receipt.get("serving_ready") is False,
            "build scope must remain no-device")
    commands = receipt.get("commands", [])
    require(len(commands) == 3 and all(row.get("exit_code") == 0 and
            isinstance(row.get("log_path"), str) and len(row.get("log_sha256", "")) == 64
            for row in commands), "three actual successful build commands")
    exported = receipt.get("exported_kernel", {})
    require(exported.get("name") == "qwen36_damp_selected_prefill_pack_kernel" and
            exported.get("defined") is True and exported.get("type") == "T",
            "host launcher must be actually defined")
    cann = receipt.get("cann_identity", {})
    require(cann.get("opp_version_info_path") == "/usr/local/Ascend/cann-9.1.0/opp/version.info" and
            cann.get("opp_version_info_sha256") == OPP_SHA and
            cann.get("opp_version_info", "").splitlines()[0:1] == ["Version=9.1.0"] and
            receipt.get("cann_version_info_sha256") == OPP_SHA, "actual OPP 9.1 identity, not whole-SDK claim")
    return receipt

def validate_proof(proof, physical, now_ns=None):
    now_ns = time.time_ns() if now_ns is None else now_ns
    ids = proof.get("physical_npu_ids")
    require(physical in (4,5,6,7) and ids == [physical] and
            proof.get("logical_to_physical") == {"0": physical}, "single authorized card mapping")
    require(proof.get("privileged") is False and
            proof.get("exclusive_resource_check_passed") is True, "fresh nonprivileged exclusive check")
    when = proof.get("observed_at_unix_ns")
    require(type(when) is int and 0 <= now_ns-when <= 1800*10**9, "proof <=30min and nonfuture")
    return True

def status_rows(values, p, error=0):
    require(len(values) == p*96+16 and values[:8] == [GUARD]*8 and
            values[-8:] == [GUARD]*8, "complete status ABI/32B guards")
    rows = [values[8+i*8:16+i*8] for i in range(p*12)]
    for row in rows:
        require(len(row) == 8 and row[5:] == [16384,0,0], "status lane count/reserved")
        require(row[0] == int(row[1] == 0) and row[1] in (0,1,2,3) and
                0 <= row[2] <= 4 and 0 <= row[3] <= 16384 and 0 <= row[4] <= 16384,
                "status numeric ranges")
        if error == 0:
            require(row[0:3] == [1,0,4] and row[3]+row[4] == 16384, "all twelve P heads succeeded")
        elif error == 1:
            require(row[0:5] == [0,1,0,0,0], "metadata rejected BEFORE writer")
    if error in (2,3):
        require(any(row[1] == error for row in rows), "expected numerical error absent")
        require(all(row[1] in (0,error) for row in rows), "unexpected numerical failure class")
    return rows

def selection(p, slots, turn=0):
    require(1 <= p <= 16 and slots == p+3, "actual P and S=P+3")
    if p == 1: return [0 if turn%2 == 0 else slots-1]
    order = list(range(slots))
    shift = turn%slots
    order = order[shift:]+order[:shift]
    return order[:p]

def arena_layout(slots, kind):
    require(4 <= slots <= 19 and kind in ("adjacent","guard_gaps"), "arena geometry")
    definitions = [("conv",(slots,3,2560),2),("high",(slots,12,128,16),2),
                   ("low",(slots,12,128,112),1),("scales",(slots,12,4,112),4)]
    gaps = [0,0,0,0] if kind=="adjacent" else [32,64,96,32]
    cursor, rows = 96, []
    for (name,shape,width), gap in zip(definitions,gaps):
        cursor += gap
        size = width
        for dim in shape: size *= dim
        require(cursor%32 == 0 and size%32 == 0, "32B arena writer ownership")
        rows.append({"name":name,"shape":shape,"width":width,"start":cursor,"stop":cursor+size})
        cursor += size
    return {"slots":slots,"kind":kind,"regions":rows,"bytes":cursor+128}

def require_decode_admission(receipt, manifest, library_digest):
    # Actual compile/export identity only; NOT C16 scheduler/service admission.
    require(library_digest == ALL_BATCH_SO_SHA and
            receipt.get("schema") == "damp_all_batch_wrapper_build_v3" and
            receipt.get("status") == "compiled_no_device" and
            receipt.get("namespace") == "qwen36_damp_all_batch_v3" and
            receipt.get("sources") == ALL_BATCH_COMPILED and
            receipt.get("source_manifest_sha256") == ALL_BATCH_MANIFEST_SHA and
            receipt.get("library_sha256") == ALL_BATCH_SO_SHA and
            receipt.get("image_id") == IMAGE and receipt.get("npu_arch") == "dav-2201" and
            receipt.get("npu_executed") is False and receipt.get("serving_ready") is False,
            "actual all-batch build identity/scope")
    require(manifest.get("compiled_sources") == ALL_BATCH_COMPILED and
            manifest.get("namespace") == "qwen36_damp_all_batch_v3", "allbatch manifest identity")
    commands = receipt.get("commands", [])
    require(len(commands) == 3 and all(row.get("exit_code") == 0 and
            isinstance(row.get("log_path"), str) and len(row.get("log_sha256", "")) == 64
            for row in commands), "actual allbatch successful software/config/build")
    exported = receipt.get("exported_kernel", {})
    require(exported.get("name") == "qwen36_gdn_damp_all_batch_v3_decode_kernel" and
            exported.get("defined") is True and exported.get("type") == "T",
            "allbatch actual host launcher export")
    cann = receipt.get("cann_identity", {})
    require(cann.get("root") == "/usr/local/Ascend/cann-9.1.0" and
            cann.get("opp_version_info_sha256") == OPP_SHA and
            cann.get("version_info", "").splitlines()[0:1] == ["Version=9.1.0"] and
            receipt.get("cann_version_info_sha256") == OPP_SHA, "actual allbatch OPP identity")
    return True

def validate_anchor(report):
    require(report.get("schema") == "damp_integer_compaction_npu_gate_v1" and
            report.get("status") == "general_numerical_pass" and report.get("npu_executed") is True and
            report.get("steps") == 160 and report.get("limits") == LIMITS,
            "complete original native/reference trust anchors")
    variants = ("SR1_identity_plans","SR1_perHv_permutations","power2_perHv_permutations")
    expected = {(b,v) for b in (1,16) for v in variants}
    seen = set()
    for case in report.get("cases", []):
        if case.get("stage") != "anchor": continue
        key = (case.get("batch"),case.get("variant"))
        require(key in expected and key not in seen and case.get("status") == "passed",
                "anchor matrix identity")
        seen.add(key)
        steps = case.get("steps", [])
        require(len(steps) == 160, "full 160-step anchor")
        for index,row in enumerate(steps,1):
            guards = row.get("guards", {})
            require(row.get("step") == index and row.get("passed") is True and guards and
                    all(value is True for value in guards.values()) and
                    guards.get("complete_state_bitwise") is True and
                    guards.get("original_output_bitwise") is True, "all original anchor guards")
            for name in ("complete_transformed_state","original_output"):
                metric = row.get(name, {})
                require(metric.get("finite") is True and metric.get("max_head_relative_l2") == 0,
                        "native-reference anchor must remain bitwise, not tolerant")
    require(seen == expected, "six native anchors missing")
    native = report.get("native_source_manifest", {})
    require(native.get("native_commit") == "5cb98caaadeff42b5b62b996e34bb2aaa29d20fd" and
            native.get("native_header_sha256") == "96e6d9667af1e3457316ffce92a8a983fcb90096df08e3efd13ec0b35b8b1c5b" and
            native.get("image_id") == IMAGE and native.get("source_contract_passed") is True and
            native.get("reference_source_hashes") == REFERENCE, "native/reference source closure")
    loaded = report.get("loaded_libraries_final", {})
    for role in ("native_runtime","reference"):
        require(loaded.get(native.get(role+"_library_path")) == native.get(role+"_library_sha256"),
                "actual loaded native/reference identity")
    return native

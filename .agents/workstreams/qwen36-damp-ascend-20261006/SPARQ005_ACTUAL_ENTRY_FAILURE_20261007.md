# SparQ005 actual no-device failure

Actual MAIN operation exec-000000000000108f exited1 in63.893s. Source manifest4fbe73b1f8106ae37c53456f3af60b781f3fa800ca4da9dc643bca4310311d92; whole terminal is preserved in SPARQ005_ORIGINAL_TERMINAL_20261007.json.

The minimal ops-before-device_op import fix succeeded. The remaining failure is the source predicate that admits only dispatcher namespace npu. The actual two torch_npu exports are lazy ATB wrappers in torch_npu.op_plugin.atb._atb_ops; complete native signatures are atb::_npu_paged_attention and atb::_npu_reshape_and_cache, including slot_indices and optional workspace. The observation was made before initialization with no Ascend nodes/FDs. This is an adapter ABI-proof defect, not an algorithm or NPU numerical failure.

Original RESULT: /cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq-v6-005-native-20261007-001/RESULT.json SHAa0cfa0708b60676f30e70be6523acf74fcc78d6b628c655260d5372298d8e701.
CPU ABI SHAe18737761ed8c6fa3d3cff650323a6ce2403491d745fed3939d32edef7348df9; original ABI_OBSERVATIONS SHA6276dd65241ff82e2860725a0e9fb1b831d407bc1bfc1fbf24bfd05f471b9247. CPU native child SHAff766b9af9aae5f7beafe1189a807e3259af5614a163022d0b9bd9293b4f3ec9.

Exact CPU CID79dff6e66e655c5fa1b5aed8f869eb3a8ab4928a8647b637c121d985f089fa6d is stopped/retained/Pid0/noExec/noOOM. MAIN independent read-only MA1094 verified frozen owner/mount/device/source identity and fresh SMI all NPUs idle/healthOK. The preceding read-only MA1093 omitted the exact source parent on sys.path and failed before inspect; preserve it as failed, never relabel. NPU CID=null; no NPU/model/E2E/task execution.

Next is an isolated minimum successor proving exact package wrapper/source/closure to the real ATB dispatcher with positive and impersonation-negative regressions; do not broadly permit foreign namespaces or relax full-argument/ABI/numerical/resource gates. No unchanged005 rerun.

86 software regressions/source27 passed at actual MA108e before this real no-device failure. They are not native authority. Hugepage32GiB authority remains spent; OVS and complete NUMA3 unchanged. Portfolio cutoff remains2026-10-09T11:17:31Z.

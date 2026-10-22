# Frozen command operand binding

Pure API: bind_source_operand.source_ref_from_commands(commands, reviewed_source_ref, manifest, template_ref, expected).

The caller first verifies complete actual COMMANDS/source/template/command_contract Refs. Pass the actual source-owned command_contract.expected, not a recreated generator. The helper extracts exactly one identical --source-ref operand from frozen MODEL and CPU, checks its typed semantic Ref against the reviewed source, preserves JSON insertion order, and validates original MODEL/CPU/bind argv closure. The bind template operand's original key order is preserved too. The return value is only source_ref; no owner, approval, source file, command or NPU execution is created. Direct CLI is default OFF.

Config assembly:
1. cfg['source_ref'] = source_ref_from_commands(...).
2. Serialize config with json.dumps(cfg, sort_keys=False). Sorting an outer config recursively also sorts its nested Ref and reproduces the original defect. Do not canonicalize, use compact separators, or reconstruct the embedded command operand.
3. Reopen the saved actual config and run original MAIN.source_inputs before any resource/device admission. Its original gates remain authoritative.

Semantically equal Ref dictionaries do not imply literal argv equality. Existing command_contract.expected uses json.dumps(sr), so [bytes,path,sha256] and [path,bytes,sha256] generate different command strings. This helper follows the frozen argv rather than weakening its validator. It is not proof that an unchecked or modified COMMANDS object is authentic; original complete Ref checks remain required.

Actual controlled fixture is V6 CONFIG.ON.actual-v3.json plus unchanged frozen SOURCE_BOUND/COMMANDS and actual original command_contract.expected AST. test_source_operand.py --real-main-controls calls original MAIN.source_inputs in independent source-only subprocesses: deliberately sorted config must reject; preserved frozen order must pass. No MAIN main(), Docker, NPU or command dispatch is called. Original failure attempts are retained in operation records; no frozen file is edited.

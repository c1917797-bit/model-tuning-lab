# Source/evidence checkpoint boundaries

2026-10-06, work/qwen36-damp-ascend-20261006, base bb9a758.
MAIN reviewed the collector/calibration/integration preparation, v4 production
and trace sources in this logical workstream and preserved actual build/library/
native gate/trace receipts. The stage records attempted/failed/inconclusive
work as well as the valid diagnostic result; it does not activate or accept a
compressed model service. Original runtime/image/reference repositories are
not modified. All new functionality remains independently named/opt-in.

Native full capture MA0161 uses frozen collector and launcher bytes. Launcher
SHA9ad5e359766578a24f06e127a990ab93d1e86555baa15d1abb7bb2b3ffc51122.
Git checkpointing alone does not alter those files. Dataset/tensors/SO/logs
remain outside Git; raw identities are referenced in MIGRATION_PREP_RESULT.json.

Checks: repository Maintainer Skill Tree20 skills PASS and tracked working-tree
diff check PASS. Full staged diff check additionally found whitespace-only
findings (trailing blanks / extra blank EOF) in copied license bytes and frozen
operator/integration/probe source. This full staged check is NOT reported PASS.
Preserve exact bytes of source snapshots tied to existing builds; any later
format-only revision needs a new source identity and must not rewrite historical
receipts. These style findings are not a NPU numerical result. Main software
identity12, same-image calibration19, integration15, operator library/schema/
Meta and saved-fixture trace evidence remain scoped to their exact receipts.

Pending source drafts excluded from this checkpoint:

- operator/reference/**: independent generalSR FP32 reference pending output-ND
  repair/build/NPU native anchoring;
- tests/GENERAL_SR_NATIVE_GATE.md, general_sr_contract.py,
  general_sr_native_gate.py and test_general_sr_contract.py: future matrix,
  raw-after retention and pointer/byte-range strengthening not complete;
- operator/quantizer/**: exact integer boundary draft/software math checks;
  independent wrapper/build/NPU and fast-path receipts absent.

These remain on the target host under explicit owners; they are not deleted,
discarded or misrepresented as source-reviewed accepted functionality. Next
checkpoint must publish them after MAIN review and scoped verification.

Original restricted compressed recurrence is still FAILED. No current DAMP
throughput/TTFT/TPOT, LongBench-v2 or GSM8K result exists. The 72h deadline and
one genuinely usable non-HYPIC requirement are unchanged.

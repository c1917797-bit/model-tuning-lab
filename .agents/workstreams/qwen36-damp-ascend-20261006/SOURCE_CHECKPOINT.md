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

## Reviewed preparation checkpoint after7d60821

The earlier pending list is historical. MAIN now fully reviewed the frozen
16 quantizer files,10 independent reference files and four general-SR gate/
contract documents/scripts, plus the eight-source audit. Actual CANN9.1
NO-device quantizer compile/load/Meta and independent-reference compile/source
contract/15 software checks passed with receipt identities in
MIGRATION_PREP_RESULT.json. No NPU arithmetic, production recurrence, graph,
full service, E2E performance or task-quality pass is inferred.

The new fast_integer_certificate subdirectory and
projects/kvbuffer-parallel-ascend remain explicitly excluded: mathematical/
software preparation is not actual source/ASC/NPU integration approval.
Old production/trace/collector bytes and failed reports are untouched.
All binary artifacts, tensors and raw build logs stay outside Git.

MA028a staged exactly35 reviewed files and verified their staged SHA bytes.
Maintainer Skill Tree20 skills PASS. Full staged whitespace check exited2,
not PASS: copied native/license trailing whitespace and extra EOF blanks in
frozen quantizer sources/docs. Keep these exact built-source bytes and the
negative check; do not silently reidentify sources to make a style scan green.
KVBuffer and fast-integer-certificate drafts are absent from this stage.

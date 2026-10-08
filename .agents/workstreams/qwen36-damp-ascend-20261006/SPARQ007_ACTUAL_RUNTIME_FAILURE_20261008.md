# SparQ007 actual native runtime failure — 2026-10-08

## Established results

- MAIN1138: canonical100 stdlib tests,27 frozen source/AST checks, actual
  numeric_gate default-OFF CLI and separate public ATB source identity passed.
- MAIN1139:188456ms,exit1. Manifest40875a65f5a493a1b1c0da94bc3ef2802b4b84d1e6d5dbd6e5bd40e16bed506b.
- Same-image Devices[] ABI passed; CPU stopped before physical6->guest0 began.
  Fresh physical6 canary passed. The matrix child actually ran20.599s.
- ATB ReshapeAndCacheOperation setup failed during initial native KV writes.
  REPORT cases=[];0raw steps. This is not a tensor accuracy result.
- MAIN1145 independently verified both owned CIDs stopped/retained,noExec,
  noOOM; all0–7 have no NPU processes.0–3 protected before/after unchanged.

## Exact retained identities

Output: /cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq-v6-007-native-20261008-001.
RESULT81961B SHA1046e29049865199671f83b2d04d3126ce156cd95bb2e9d3d80bfd6548e3affa.
REPORT25086B SHAb8d534d3f921a3ad73df2ea8be1721413f3d9d99bcfe8b633ee3717cbc2255c8.
NPU CID3f9ed75cc9c66a7cb65cc6de0c2d5c4c72224ed02041b2d834dcee4345635d91.
CPU CID65a4c21fea6728320e3fa6d28b4660c0a691a50519cae264f179cbfa8157b74c.
NPU cleanup1210B SHA041baaf4a6cd985748e4def9871fcec7d17194358a629cef0ed5176d72f5d81a.
CPU cleanup1228B SHAb282359afbe09cec098c21e1fa9f986e67fc9d27e93b257633c0bf30a1d4b1d0.

## Next admissible work

MAIN1149 actual stopped-owned ATB log confirms the cause: inTensor4 slot
indices were int64,nd; all three supported combinations require int32,nd.
The other four BF16,ND inputs match supported comb2. Actual907B log had6
lines and invalid-param error13. A successor should repair native slot dtype
only, retain internal64bit index/mean semantics, and preserve all matrix/gates.

No unchanged rerun. Read original4321B matrix.stderr and actual native writer
source to compare legal parameter layout/format/dtypes/strides/device placement.
The async traceback on mean.prefill cannot identify the failing producer.
A proved minimal successor must preserve numerical thresholds and the complete
preregistered matrix. No model, matched1024 throughput, TTFT/TPOT or final2048
LongBench-v2/GSM8K result has been produced by this run.

## Memory authority is completed

Exactly32GiB free1GiB hugepages released onOct7, not again. MAIN1145 fresh
ordinaryRAM116680776KiB (~111.28GiB) at02:15:33Z; some later RAM changes are
not attributable to that32GiB operation. OVSsamePID27118/start11471 uses24GiB
hugetlb; wholeNUMA3pool474GiB/free450 retained. No permanent config or service
restart, protected0–3 untouched. Do not reuse this authorization for another
release.

## Model path correction

Original config ref /cache/efim/Qwen3.6-27B/config.json is physically confirmed
4308B/SHA69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c.
Other austinov directory differs only transformers_version in config; weights/
tokenizer equality was not established. Use original path, freeze remaining
identities before full-model comparison. CPU19 inventory tests are fixtures,
not a model run or task-data identity.

# Native-only G2 PDC observation — prospective2026-10-16

Pinned official metrics/loggers.py source inspected0977 SHA256
ce2a0535d2b2b69e4368f34b692dac081be764e8d0eadab4f791b1afdcf43df4.
Official prefix_cache_queries/hits count queried/cached TOKENS, request_success
counts finishreason. Actual0978 sameimage endpoint labels engine0/modelqwen3.5;
4 length warmups,0cachequeries/hits in currentG3 PDCoff,12running4waiting.
Do not treat thisG3probe as G2evidence. Completioncached_tokens gatedoff bydefault096e.

Chosen minimal nonalgorithm host-only observer: separate entrypoint imports reviewed
formal_r15_tp4 controller unchanged; wrap ONLY host workload.run_full40. Wait official
metrics BEFORE measured invocation until exactly4successfulwarmups and0running/waiting;
capture metrics. Run original full40 UNCHANGED (allrequesttimers insideoriginalsend).
AFTER alloriginalrequests finish, wait exactly44success/0running/waiting and capture.
No metrics polling within measured invocation; no enable_prompt_tokens_details flag,
no runtime/image/model/input/output change; no extra inference request. Pre/post
metadata overhead is explicitly outside request TTFT/TPOT and not a speed contribution.
Use same observation wrapper for G2/G4 pairs; G1/G3 noPDC pairs remain unchanged.
Capture own wrapper/module/contract SHA and actualcontainer/sourceidentity;exclusive
native-pdc-observation.json + rawmetrics before/after. Guard during waits, bound60s,
metric HTTP10s/2MiB; exceptions propagate to originalcontroller exactrelease path.

Independent nativePDC audit checks source/hash/contract/CID, officialcounter labels,
4->44successful withzeroabort/error/repetition and0active boundaries, nondecreasing
counters, strictlypositive measured cachequeries/hits with hits<=queries. Evidence
supports aggregate realhits among the40 measured requests, NOT40perrequest hits.
This is sufficient nativePDC-on control mechanism observation; G4 additionally requires
existing new full40 perrequest/fourrank >=7680 nativeprefix+PIC/1536 evidence.
Baseline hasnoHYPIC hooks, cannotinventfourrankPICreceipts. No stricter unsupported
perrequestG2condition; do not weaken G4mechanismproof.

All new files outside current0967's141bindings; freeze wrapper/source/auditor hashes in
new G2/G4 prospective contracts before admission, no retrospective raw mutation.
Tests:zero/negative/reset/missing/duplicate/nonfinite/badlabels/foreignengine counts,
wrongsuccessdenominator/activeboundary rejected; originalcall once; no callback during
measured; pre/post capturesordered;finallyrestorehostfunction;disabledmode absent.
After implementation focusedhosttests+structure/diff/141unchanged check, publishcheckpoint.
Not newNPUacceptance, not fullquality/lifecycle. DeadlineOct17T06:48:09Z unchanged.

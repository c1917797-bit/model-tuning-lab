# PDC post-run audit model correction — freeze before code
Original087b audit FAIL remains frozen: required scheduler cap event per request.
Readonly087d proves all16 scored requests/all4 ranks first computed_tokens=7680.
Most have actual1536 cap receipts; some have no cap event.
Source independent_pic_scheduler_admission.py emits only if result!=proposed.
Thus no cap event is not equivalent to no PDC, and requiring that incidental
event for every request is an erroneous observer assumption.

Do not edit original audit, contract,132 runtime source files or raw data.
New separately hashed post-run audit must:
1 run unchanged packed/base/source/physical/release audit;
2 strict16 HTTP<->runtime map and unitindex join to hash-bound immutable input;
3 derive PIC start/end for EACH request from original tokenartifact, validate
public-segment token slice and exact32768/native8192 shape;
4 independently prove actual scheduler block1536 from nonempty sourcebound
cap records, reject ANY conflicting block or geometry for relevant requests;
5 each of16/all4rank actual first native runner progress>=7680 and<=its PICstart,
stable worker/source/step rules as original audit_initial_prefix.
Do not fabricate per-request cap records or lower7680/all16/all4 requirements.
Add CPU tests for missing global block, wrong hash/geometry/mapping, missing rank,
no-hit and conflicting observed cap. Report both original frozen gate FAIL and
new explicit revised observational acceptance; no silent retroactive pass.
No new device repetition. Numeric/packed/PDC receipt proofs remain distinct from
speed/taskquality/full-goal acceptance. Stop19:04:09UTC unchanged.

# R12 capture selector repair — mixed native1 control
Raw R12r1 is immutable, numerical gate failed and no capture was sealed.
Independent07b5 checks126sources/174clean isolation/exact97922c91 release/no8233
listener/physical0-3empty. Prior live NSpid/cgroup proof covers all4workers.

Raw rank0/layer0/step10 contains5 private native1 entries AND2 packed hot requests.
Original selector wrongly requires the whole plans batch to have exactly2entries
and every request to have leased hot material. Thus it deterministically rejects
this real7-entry mixed batch. This is a diagnostic selector bug, not a numerical
rootcause. Preserve the failed attempt, not a new statistical repetition.

Changed premise: select exactly2 nonempty packed hot chains with leased material;
allow separately batched empty-chain native1 entries without sampling or altering
them. Require all nonempty chains to be the selected2hot requests and2live windows
per request. Capture only the FIRST HOT request/head0, not the first batch entry.
Coordinates cover only the actual packed shadow group. Keep <=12000 packedlive
rows,32records/64MiB; no limit increase. Emit bounded positive/negative selection
receipts with total entries, hot count, native1 exclusion and reason.

Host tests must reproduce the7-entry rejection then prove corrected2hot+5native1
selection, exact hot slots, no native token sampling, unchanged buffers/math,
and selection receipt fail-closed audit. All prior observer rollback/tamper and
CPU tests remain. Rebind new r2 config/manifest/contract/newrawroot, publish, fresh
direct/physical0-3/8233/HCCL admission before ONE integrated successor.
No tolerance/statepass/algorithm changes. Old R11/R12disabled controls notadmitted.
If r2 capture is incomplete, explain exact evidence gap; do not call rootcause
found or retry unchanged. Full performance/quality/lifecycle/Skills unfinished.
Fixed stop2026-10-15T19:04:09Z, no extension.

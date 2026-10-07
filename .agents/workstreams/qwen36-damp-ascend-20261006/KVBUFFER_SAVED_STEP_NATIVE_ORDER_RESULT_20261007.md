# KVBuffer native-order-v2: actual saved-step result

Observed 2026-10-07 09:49Z; MAIN immutable readback MA09fb completed exit0.
This is one real Ascend eager saved-step diagnostic, NOT full-matrix acceptance.

## Actual evidence

- Source checkpoint faa7a8d1d7a1fd3ec67bafd44198c17b4e1a3a32 was normally pushed
  and remote-verified by MA09d0. Native operator sources remain unchanged.
- MA09d4 completed exit0 in102.664s, stderr empty. Its original control-plane
  record is retained externally, never reconstructed from status text.
- Output root:
  /cache/cch/qwen36-kvbuffer-parallel-20261006/saved-step-native-order-v2-20261007-0944
- Report diagnostic/report.json SHA256:
  46750d48be7327b3ab39a347b10b8348ce8736d25517d4844550f92c15d6555d
- Original MA09d4 archive:
  /cache/cch/qwen36-kvbuffer-parallel-20261006/native-order-v2-MA09d4-saved-step-original.json
  SHA4933767eacd80fc89b785d1f7f7f63dfa59192d37ed0aad3b74f9ce0097b23ee.
- Original child diagnostic-child.json SHA8302b6d053b7a6eaed69e55dd0a1dfa149dcaafcf13e188e3a62ec6ba529104f,
  actual exit0 and physical5 PID401699/cgroup/exact target proofs at09:49:23/25Z.
- Nonprivileged owned container a8690ccd004c465fa68c94a7f242a44009b8c7ccded34ae9f2ea341eb16d6a46:
  physical5->logical0,8GiB/1CPU. release.json SHA5ab9883b299cc8d705fee9e40c8d0e0081caeed79a4fa1fc616a6782f361bf44.
  MAIN MA09ee fresh Docker inspection confirms stopped/Pid0/noExec/noOOM,
  retained/not deleted. Container exit137 is owned cleanup, not numerical child failure/OOM.

## Paired saved-input diagnostic

The old production library byte-reproduced the saved B1 graph trial2 step104
after-state, actual/native output, independent expected state, guards and inputs.
All six reproduction predicates are true. Its original failure remains FAILED.

| Same retained input | Old production | NEW native-order-v2 | Unchanged gate |
| --- | ---: | ---: | ---: |
| Output maxabs normalized error | 0.003355704697986577 | 0 | <=0.00303 |
| Complete state relative L2 | 1.1455440726423622e-7 | 1.145579426469926e-7 | <=2e-6 |
| Maximum per-head relative L2 | 1.370211474290999e-7 | 1.370211474290999e-7 | <=2e-6 |

Both native/independent expected results also reproduce the saved input oracle.
New full state/logs, guards, untouched slots, nonflush dense base, pointers,
immutable inputs, padding and all finite checks are true. No BF16 snapping,
tolerance relaxation or retrospective promotion of the old failure occurred.

Raw evidence was retained BEFORE metrics:
- diagnostic/before.pt:349002e6b319f4035e0bd595a0a66c6ba701a258cd587d8c40ccd6c7e2a29c4c
- diagnostic/old-production-raw.pt:9b58a440b3b1c102729d2a25d7d86aff2cf4aac93a02777d3734e7a4f8b5d395
- diagnostic/new-native-order-raw.pt:b7df46a2505da4e685ae128157c109dfebf57bbad6eb7448194a3893c0c37530

MA09fb verifies64 before/after/current source hashes, current manifest508ff...,
new SO77b4.../buildff4c.../Meta fb765..., all Ref bytes, raw identities and
actual mapped native SOeaa945.... Numerical child stderr retains the known
in-container npu-smi command warning and32-padding allocator warning; these
were not hidden or converted into numerical failure.

## Decision / next gate

A source-specific repair has positive REAL-device single-step evidence.
This does NOT prove full160-step feedback/three graph replays, B16 domain,
middle T2..15, real48-layer mixed cache lifecycle, serving or a speedup.
Report flags matrix_verified/graph_matrix_verified/matched_e2e_verified/
accuracy_verified/serving_ready are ALL false.

Next: source-reviewed NEW retention-safe host producer with ONE summed
B1physical5+B16physical6 numerical budget. Run the unchanged1eager+3graph,
160 changing-feedback steps/arm; only complete actual terminals/source-after/
physical PID/release authority can admit the middle-T gate. Consumer/service
patch must use the v2 namespace and actual v2 report; the old v1 consumer
must not be fed a forged legacy PASS.

Known preparation error: the frozen successful saved-step host producer
does not retain accumulated child PID proofs/nullable exit on timeout or
monitoring exceptions. It was NOT triggered by MA09d4 and is NOT a repaired
old-source claim. Use a NEW exception-safe producer, preserving original
primary exceptions; candidate math and all gates stay unchanged.

## Live memory boundary, not cleanup authority

MA09ee at09:55:31Z: MemAvailable66810564KiB (~63.7GiB), HugeTLB1916GiB,
pool free1892GiB/reserved0; OVS process27118 has24GiB private HugeTLB plus
~1.83GiB ordinary RSS. Do NOT stop that networking service or resize its pool.

New outside hypic_npu03_cpuset96175_20261007 container4e96... uses~18.04GiB
ordinary memory and actual physical0–3 worker PIDs430733..430736. MAIN did
not start or stop it; no HYPIC re-run is credited to this workstream.
Cards4–7 are idle, enough for the24GiB numerical summed budget after fresh
admission, but below the UNCHANGED72GiB full-model floor. Exited owned
containers have no resident process; deleting them would free disk, not RAM.
No HugeTLB release, global drop_caches, outsider stop or container deletion
was performed. Historical memory snapshot~80GiB is not current admission.

MA09eb read-only inventory failed at missing assumed /usr/bin/ss. Its original
exception is retained; NEW MA09ee resolves actual /usr/sbin/ss, keeps partial
errors explicit, and completed exit0. MA09fc git fetch timed out at30s with
nullable exit; no fresh fetch success is claimed or unchanged retry performed.

KV cutoffOct8 08:29:54Z; portfolioOct9 11:17:31Z unchanged. No accepted
non-HYPIC usable technique. DAMP37/64 fixed time-gate remains closed/scoped
deployment-inconclusive, not a paper-wide rejection.

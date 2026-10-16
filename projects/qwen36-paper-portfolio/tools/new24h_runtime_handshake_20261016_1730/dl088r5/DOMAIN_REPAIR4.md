# R4 domain source-frontdoor and durable child diagnostics

Source-only successor; old R3 N16 owner6ac94996... remains FAILED, producer72b1956d... is saved evidence, not a new qualification. No numerical/domain FAIL can be inferred from an absent DOMAIN035.json.

Minimal changes: domain PINNED producer now exact028e1c8cebe3b756023d54a301b3f1524c148c0eccadbd9e0bfed6d4ce558e94; existing R3 inverse control still reconstructs pre-frontdoor8884b001... byte-for-byte. Producer, all recurrence/materialization/reference thresholds, seed and host/resource controller are unchanged.

consume_pair persists exclusive CHILD-01-consume.json / CHILD-02-domain_entry.json immediately after each subprocess returns, before checking returncode, retaining full stdout/stderr. Old failures are not overwritten. New CPU entry loads actual source-pinned domain_consumer and calls static_proof on the complete real manifest before importing torch. Actual fixed hashes, all source files, probe and DSO are checked; receipt DOMAIN_STATIC_PROOF.json is linked from STAGE_RESULT.

57 local tests passed. New regression executes actual static_proof against real current local fixed-source files (ordinary local endpoint fixtures only for probe/library file-identity tests, not a library receipt); rejects old pin and changed producer; executes a real Python exit7 and verifies stderr was durably retained before failure. The same-image CPU entry must independently check the real source/probe/library refs. No same-image/NPU execution claimed locally.

Fixed cutoff1792135097, original CPU/NPU/cleanup budgets and defaultOFF remain. MAIN must run newsource CPU→16→160. R3 failed owner and prior-source16 must not be relabelled as same-source success. Optional read-only savedraw replay can diagnose original R3 source-pin failure separately, not promote it to NPU PASS.

# 093: source-only second storage seal

Not executed remotely. No ledger generation, evidence receipt, numerical PASS, or
resource admission is claimed. Original069 N160 FAIL is retained byte-for-byte.

The exact original069 helper remains the authority for the old three closed
phases, exact refs, and tree checks. 093 preserves every old generation through
the reviewed ledger7. The only new transition is ledger7 -> a new retained seal
generation using EVIDENCE093; subsequent reservations must chain that evidence
and source. All six old rows remain unchanged. Closed bytes replace commitments
only for those six trees; untracked bytes and future 1/33GiB allocations still
count against80GiB, and filesystem free100GiB is unchanged.

Historical0a40/49/58 operation receipts are unavailable. The new receipt says
exactly that, never that old operations exited successfully. Present closure is
proved by pinned original owner RESULT, original five create receipts/CIDs,
fresh read-only inspect stopped/Pid0/noExec/noOOM and exact exits0/0/0/1/0,
complete host command + write-FD/shared-map scans, two full stable tree hashes,
and preserved cleanup receipts. Main must declare no future writes to closed
leaves. This proves current storage accounting, not that an arbitrary future
actor cannot write. Runtime stat checks and final full rehash reject mutations.

Collector output is an exclusive50MiB leaf, fully charged to80/100; no existing
data is removed or overwritten. A failed collection retains its partial output.
The captured local projections are locators/audit inputs, not final sealed
evidence. Actual MAIN collector execution must produce exact fresh Ref3s.

API: install(storage,evidence_ref,authority_ref,template_ref),
seal_generation(evidence_ref,root,authority_ref,template_ref),
final_verify(evidence_ref). The original storage061.reserve remains unchanged.
Its import sealed_storage069.ref computes the same Ref3; keep original module
read-only available. New runtime must source-bind093 helper and all dependencies.

Budget: bounded stdlib CPU only, parent512MiB, no torch/device import, max50MiB
evidence. Each readonly Docker inspect uses original prlimit AS-unlimited child
wrapper,20s bound,2MiB stdout/64KiB stderr. No Docker mutations. MAIN should allow
600s collector bound plus90s cleanup within NEW24H. Full hashing traverses old
and new evidence, so no unsupported30s promise is made.

Windows tests intentionally skip the real Linux /proc short-writer case. Before
sealing, MAIN must run the same tests in the actual Linux host environment,
including that case. This is not a Devices[] guest scan: host /proc is necessary.

# Independent fixed-frame FIA owner review

This proposed source adapts the executed paged component's independent CPU and
single-NPU owners. It does not use, shorten, or admit the whole-model PHASE3600
path. No remote CPU or NPU execution is claimed by this preparation package.

## Actual donor and current authority

The paged component source is `bole-paged-tree-owned-new24h-v1-118t-repair1/`:
SOURCE_MANIFEST.json is 25,737 bytes, SHA256
`fdafbb8872ad9da1ff8150ddafa1e66acae3a80e05aa2b62bb04202da6e33faa`.
Its owner116.py is 16,858 bytes, SHA256
`a5bf934cd7e749aa3b630da2039969a2d8e3cce52d4c0756a52e73299edc543d`;
owned_cpu116.py is 16,387 bytes, SHA256
`6159466bc6347ab6f28c18537cc9dcc6fee37db0bb288e94652b32e6c8288812`.
Exact copies in this new package are controls, not replacement old owners.

The new manifest fixes MAIN continuation batch MAIN-CONTINUE-20261018T192427Z-v1 and the exact
new authority Ref3, start 2026-10-18 19:24:27 UTC and cutoff
2026-10-19 19:24:27 UTC. The 24-hour limit is MAIN's bounded batch
execution limit, not a duration stated by the user. The user explicitly
requested continued actual execution and repair until success. It fixes the original image digest
`sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`.
The old donor module is loaded into a private instance; its START/CUT values are
set from this new exact authority before compiling its original Lane class.
The donor file, donor source and prior cutoffs are never edited.

## Resource and time gates

| Stage | Whole | Child/work | Cleanup | Latest full-lease admission |
|---|---:|---:|---:|---|
| Same-source CPU preflight | 1,000 s | 600 s child; 180 s software controls total | 90 s | Strictly before 2026-10-19 19:07:47 UTC |
| Independent FIA NPU | 900 s | 600 s guest; 560 s FIA including guest startup | 90 s | Strictly before 2026-10-19 19:09:27 UTC |

Source preparation and ticket checking are charged from each new owner's main
entry. NPU Lane.call preserves its 180-second cleanup reserve. The guest work
deadline is further capped by the owner deadline and fixed cutoff. Each whole
lease must fit at admission; remaining time does not replace its declared whole.
CPU must terminate, retain its exact CID, verify release, and produce a valid
actual-ABI ticket before the NPU owner is eligible. MAIN serializes the stages.

The CPU owner retains Devices[], a read-only container root, exactly one 8 GiB
memory=memory-swap child, one disjoint inherited CPU, 256 MiB private shared
memory and a 512 MiB host soft AS limit with unchanged unlimited hard limit.
The NPU owner retains original physical4 to logical0 mapping plus the three
original control device nodes, 8 GiB memory=memory-swap, one CPU, private IPC
with 2 GiB shared memory, network none, dropped capabilities and no new
privileges. All other protected and nonselected observations remain in the
original composed scope adapter.

Fresh ordinary RAM must satisfy the original 16.5 GiB idle admission floor;
the original observer rechecks the live 8 GiB reserve plus 0.5 GiB host and,
when not active, 8 GiB guest allocation. NPU host subprocess peak accounting,
CPU pool checks, original terminal fence, SMI/proc/namespace/start/cgroup/full
argv proof and exact CID inspect/stop/retain are preserved.

The complete new profile, including CPU evidence, ticket and numeric output,
is capped at 1 GiB. Original live filesystem free floor is 8.5 GiB; new admission
requires 9.5 GiB. Raw FIA outputs remain capped at 64 MiB. No DeltaLog ledger is
read, reset or advanced. Existing R6 raw data and original failed reports are
read-only inputs. The source binder does not create experimental output roots.

## Entry order

1. Copy every fixed new source file byte-for-byte to the registered new root.
   `SOURCE_TEMPLATE.json` has prepared_only=true and every executable, test,
   original helper and fixed input Ref in its closure.
2. Run `bind.py --execute --template-ref <exact Ref3> --output <new root>/SOURCE_MANIFEST.json`.
   It checks the entire readset and compiles actual Python source, creates the
   previously absent manifest and reopens it. This is source binding only.
3. After MAIN verifies the source and current resources, create the ordinary
   new output parent and `replay` directory. The `cpu` and `numeric` leaves must
   remain absent. Use actual inherited, disjoint host and guest CPU IDs.
4. Run `cpu_owner.py --execute --source-ref <bound Ref3> --host-cpu <H> --guest-cpu <G> --output <profile>/cpu`.
   Its actual same-image Devices[] child executes all registered software
   controls without skips, records the installed FIA ABI and reopens the exact
   retained R6 frames and original numerical failure witnesses on CPU.
5. Require the actual CPU owner RESULT primary=null, secondary=[], exact release
   verified and stopped-retained; inspect FINAL_INSPECT independently. Run
   `ticket.py --execute --source-ref <bound Ref3> --cpu-owner-ref <actual CPU RESULT Ref3> --output <profile>/ABI_TICKET.json`.
   The new ticket preserves the original guest-path refs and resolves only the
   three exact expected filenames through the actual sole RW bind. It rechecks
   CID, image, source argv, labels, stopped state, no OOM and no device exposure.
6. MAIN may run `owner.py --execute --source-ref <bound Ref3> --cpu-owner-ref <actual CPU RESULT Ref3> --abi-ticket-ref <ticket Ref3> --host-cpu <H> --guest-cpu <G> --output <profile>/numeric` only if every prerequisite and the full 900-second cutoff gate pass.
7. Reopen actual NPU result, inner probe reports/raw refs and original cleanup
   receipts. A normal container exit or cleanup is not numerical qualification.

## Numerical interpretation

The original tree call replays all three queries and all 4,608 BF16 output
elements, with its original paged KV, mask, table, shape and inner_precise=2.
The original native call replays its dense 1,536-element output with
inner_precise=0. Both complete baseline outputs must match the saved BF16 bits
and the original numerical failure identities before either intervention.
Each intervention changes only its original inner_precise value between 0 and
2; no precision semantics or internal kernel route is inferred from the number.

A baseline mismatch writes the full observed evidence, suppresses both
interventions, and causes the outer owner to report the precise baseline
mismatch as primary failure while still attempting exact cleanup. An operator
error preserves its original exception and traceback. No fallback changes the
shape, layout, mask, parameters, API or image. All results remain qualified=false,
replay_qualified=false and whole_model_qualified=false.

## Verification scope

The local owner controls compare the exact donor bytes and the unchanged
resource helper ASTs, invert every registered controller interface change and
compare the entire resulting controller AST with the executed donor. They
exercise exact CPU inspection rejection, whole-lease cutoff boundaries,
no-intervention after baseline mismatch, no qualification promotion and software
control counting. Additional ticket controls exercise the exact final-inspect
alias join. The full installed-image software pass, actual ABI receipt, CPU
saved-input witness, NPU run, protected-resource observations and release proof
are still required on the selected host; local controls cannot substitute for
them.

## Bound-only predecessor and unchanged evidence

The prior FIA source was bound by operation exec-000000000000171b,
but the subsequent source-audit dispatch failed because the tool catalog
changed. No CPU or NPU owner was started for that prior source. Its exact
bound source is retained as predecessor_source_ref; it is provenance,
not a CPU preflight or ABI ticket for this successor.

All original R6 raw, source, producer, rank-report and actual ABI Refs
remain identical. probe.py, guest.py, cpu_guest.py, bind.py, test_owner.py
and both donor files remain byte-identical. New source/owner labels,
authority/window bindings and the fixed cutoff control literals are
the executable changes. All 44 actual controls remain required.

The new manifest also binds the exact separate REUSE_SCOPE Ref required
by the current authority. Its schema, batch, base_authority and full
start/cutoff must agree; it grants read-only validation of explicitly
bound historical inputs, not a current pass ticket or new capacity.

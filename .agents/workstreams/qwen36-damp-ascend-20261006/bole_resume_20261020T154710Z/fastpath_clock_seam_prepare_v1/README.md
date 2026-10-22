# Short8 current-authority clock seam: prepared only

The unchanged7b7910c3 short8 source has a deterministic runtime rejection:
`host_service.main` calls `g2_cold_clock.phase_admission`, which uses the old
contract090.CUT=1792597630. A new qualification authority does not update that
constant. `controller_admission` separately requires the same old cutoff even
though `owned_substrate.load` correctly installs the new authority in025.

## Minimal source repair

`prepare_clock.render()` returns420 source files in memory. Four files differ
from the current short8 parent: g2_cold_clock, new qualification_clock_delta,
qualification_short_prepare and qualification_source_validate. The last two
make the exact clock delta reconstructible by the ACTUAL source-owned renderer
and verify its non-stdlib helper Ref before import. The complete inverse restores
all419 parent source bytes. No stable parent file is edited.

The active phase/controller gates resolve the actual source-owned qualification
FSV.execution_window at runtime. The original monotonic main-entry timestamp,
3600-second phase,180-second cleanup and60-second create allowance remain.
Controller-created/deadline identities and its original remaining() check stay.
No numeric/resource/ownership gate, algorithm, tensor expression or worker
transaction is changed. A prepared/unbound, expired, unapproved, wrong-scope or
insufficient-window source still fails closed. No default epoch is substituted.

## Actual reachable chain audited

- Public qualification_source_producer.bind reconstructs the whole source and
  uses the current qualification authority. It does NOT call expired
  bind_model.main. write_commands emits the current producer command.
- contract090.source uses current FSV.execution_window; bind_model.readset only
  reopens the actual independent component/math lineage and source references.
- host_service uses the qualification-specific FSV.validate and admission API,
  then the repaired phase gate. Neither gate demands formal performance_ready
  or numerical_qualified; both must remain false in qualification mode.
- owned_substrate.load installs current c.CUTOFF/c.CUT before loading actual025
  safety/host modules. Their time checks dereference that module at call time;
  no captured/default old cutoff was found on the active helper path.
- performance_software_stages passes V.active_cutoff into the unchanged Budget.
  service_entry invokes this lane, not old g2_software_stages.run. Worker
  bootstrap checks actual current FSV authority and every source Ref; server and
  metadata entry use contract090.source. FAST qualification explicitly accepts8.

Old cutoff literals remain in retained inverse/history paths: bind_model.main,
g2_software_stages.run, g3_software_stages, historical g3_parent/performance
validators, and g2_cold_clock.validate's archived source-metadata result. Those
are not dispatched by the current COMMANDS/host/service software path. They were
not blindly rewritten or promoted into current execution proof.

## Source-only tests and their limits

`exec-00000000000009eb`:420-source preparation/compilation and whole inverse,
exit0. `exec-00000000000009f2`:27.426 seconds, exit0, actual functions exercised
inside the already reviewed read-only virtual filesystem/import sandbox:

1. Real whole-source qualification validator, reconstruction and real historical
   component readset, against explicitly SYNTHETIC IN-MEMORY source/authority.
2. Real contract090.source and public COMMANDS/model host_service.main, reaching
   the stop sentinel at owned_substrate.load BEFORE actual ownership/devices.
3. Real controller_admission accepting the matching synthetic current cutoff.
4. Actual rejection of old controller cutoff, insufficient original phase,
   expired authority, insufficient full3600+180 window, wrong scope, unapproved
   and unbound authority. No25-test lane was rerun.

The harness does not stub V.validate with source_validated=True. It executes the
actual gate with virtual JSON/Refs. Only process identity/affinity/rlimit calls
in the synthetic host invocation are isolated, and owned helper load is stopped;
there is no Docker/scheduler/device call. All synthetic JSON exists in memory
only: no physical approval, SOURCE_BOUND, new authorization window or output
directory is created. This is NOT actual bound validation or same-image/NPU
qualification. MAIN must review, then bind/audit under a genuinely new window.

No earlier deterministic conflict was found in the audited public bind/source
gate path; the identified first old rejection was the phase gate. This is a
scoped source finding, not proof that future environment/resource admission,
native load, numerical checks or performance will pass.

Default CLI is OFF. Explicit read-only software commands:

```text
python3 -I -B prepare_clock.py --check
python3 -I -B check_public_clock.py --check
```

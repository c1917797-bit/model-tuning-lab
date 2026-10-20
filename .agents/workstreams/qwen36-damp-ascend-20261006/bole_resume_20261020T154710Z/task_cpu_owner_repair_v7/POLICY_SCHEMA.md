# Explicit MAIN lifecycle policy

Supply `--main-quiescence-ref` as the exact whole-byte Ref of a new JSON file. Exact keys:

- `schema`: `bole.MAIN-NPU-quiescence-policy/v1`.
- `authority_ref`: the same whole Ref used for the new CPU owner.
- `declared_complete_MAIN_NPU_inventory`: true, a MAIN declaration about the explicit inventory below.
- `units`: nonempty list (max64) of `{unit, controller_ref}`. `unit` is the full exact historical/current MAIN NPU service name beginning `bole-` and ending `.service`, without wildcards. `controller_ref` pins the exact original controller script. A historical successful `RemainAfterExit=yes` unit can remain active/exited while having no process/job/task. Collected units can be not-found.
- `owned_refs`: nonempty list (max64) of actual earlier MAIN model `OWNED.json` Refs, each distinct full CID. These must retain original025 receipt fields: cid/name/image/arm/guest_cpus/source/host_sha256/create_receipt. The model arm cannot be cpu-preflight and has four actual declared CPUs. Original successful create receipt and source are reopened. The same immutable create receipt uniquely supplies the original owner label, and independently joins name/image/run/arm/source/controller fields before any current inspect comparison. The same exact image/CID/name/owner/source/controller labels are checked against a fresh full actual inspect. Container Running=false/Pid0/no ExecIDs/no restart are required.
- `serial_schedule`: exact keys `no_MAIN_NPU_start_during_CPU_owner=true`, `external_lock_path` (absolute path whose final name is MAIN_ADMISSION.lock), `external_lock_argv_prefix=["/usr/bin/flock","--nonblock","--no-fork",<same path>]`, `lock_lifetime="entire-owner"`, `lock_verification_owner="MAIN-submitter"`.

All Refs are ordinary original Ref2 or Ref3, but new outputs use Ref3. The actual units/CIDs are supplied by MAIN; this packet invents none. Source/input hashes are captured before/after. Do not include or stop foreign containers. Static foreign declarations stay in the unmodified original025 observation and the additional observation copies them with `declaration_is_actual_compute_evidence=false`.

The original controller runs its full actual resource/NPU observation first. An added `MAIN-QUIESCENCE-*.json` records policy Ref, original observation Ref, actual unit show/owned inspect receipt Refs and observed lifecycle states. It explicitly labels the external lock as not verified by this reader. MAIN must supply the actual external submitter/ExecStart/lock proof separately and serialize every CPU/NPU owner under that same lock. The inventory declaration alone does not prove future exclusion.

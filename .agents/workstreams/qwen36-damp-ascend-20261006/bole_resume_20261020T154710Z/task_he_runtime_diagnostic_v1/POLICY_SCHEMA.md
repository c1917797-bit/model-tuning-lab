# Exact explicit MAIN CPU3 registry and quiescence policy

New policy exact keys: schema="bole.MAIN-NPU-quiescence-policy/v2", authority_ref, declared_complete_MAIN_NPU_inventory=true, units, owned_refs, serial_schedule, CPU3_registry_ref. Original units/fullCID inventory/authority/lock properties retain their strict old semantics and limits; CPU3_registry_ref must be strict whole Ref3.

Registry exact keys: schema="bole.explicit-MAIN-CPU3-owned-registry/v1", authority_ref (identical to policy), entries (max64). Each entry has exactly owned_ref:Ref3, source_ref:Ref3, cid:full64hex, profile:the original fixed CPU3_PROFILE. Every complete OWNED Ref must occur in policy.owned_refs. Duplicate CID/path, dangling membership, wrong authority/profile/types, changed whole source/owned bytes, unlisted CPU3 or unsupported CPU counts fail.

All actual OWNED/SOURCE JSONs are reopened with whole-byte hashes. OWNED.cid==entry.cid, normalized OWNED.source==entry.source_ref, guest_cpus exactly integer[0,1,2], and actual SOURCE.stream_resource_profile must equal the fixed partition in both values and JSON types:

schema bole.untimed-stream-CPU-budget/v1; TP_world_size4; host[166]/budget1; model[0,1,2]/budget3; consumer[145]/budget1; reserve[3,144]/budget2; total_budget7; formal_timing=false.

The registry is permission to recognize those explicit historical stopped records, not permission to launch/overlap them and not evidence of model/math/timing success. Every prior fourCPU check stays unchanged. Successful original create receipt fullCID/name/image/run/arm/source/controller/unique owner label is still reopened and joined; current exact inspect must match all labels/identity and show Runningfalse/Pid0/noExecIDs/noRestart. Each known service must have no main/control PID/job/task; inactive/failed or active/exited RemainAfterExit with zero lifecycle is allowed. No foreign discovery/stop exists. Original025 actual resource guards precede every added quiescence observation. External whole-owner lock is declared/verified by MAIN submitter, not silently claimed by this reader.

CPU3_ACTUAL_ENTRIES.json supplies the actual G2v5 OWNED209038/cb33... + SOURCE414541/6dc571.../CIDadb0905d... and actual G2v6 OWNED266560/4f64... + SOURCE475051/41a3.../CID2dd27aef.... It is data awaiting actual host reopen/current authority; no source or failed model is promoted. Future actual CPU3 records require an explicit new source-bound registry entry and complete MAIN inventory; they are never inferred from a static device declaration.

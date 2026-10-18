# DeltaLog R36 independent geometry consumer

## Scope and identities

This is a new CPU consumer source. The R36 model source, R36 payload source,
all original reports, geometry JSONL, raw tensors, comparisons and Ref3 values
remain unchanged. The old owner result remains `status=failed`; no prior failure
is rewritten. The separate consumer identity is recorded as `consumer_source`.

The predecessor `firstdecode_consume.py` is exactly 14,493 bytes with SHA256
`6725eca40dc08cef07b6e1c7255f9d72abc30ab889d8463667f798a95bb7d6c7`.
The predecessor `firstdecode_cli.py` SHA256 is
`6d7f232c3bb386fe6ec9ca9283c484720d5d2fbccf08856e38df33817151c4fc`.
These are the frozen R36 payload file identities, not hashes of materialized
snapshots with an extra transport newline. The new CLI checks this lineage.

## Proven accounting defect and exact repair

The production observer writes one scalar JSONL row for every registered view,
including all 48 GDN layers with seven roles and all 16 FA layers with two roles:
368 rows. `Collector.end_decode` charges these actual bytes in
`controls_before_final_bytes`, alongside the original prefill control file.
The old consumer incorrectly required that field to equal only the prefill
control file size. Complete nonzero observations therefore fail the old ledger.

The replacement equality is:

```
controls_before_final_bytes == prefill_control.bytes + authenticated_geometry_bytes
```

The 16 MiB control reserve, 512 MiB raw limit, absolute 8 GiB worker cap,
allocated 7.5 GiB worker cap, baseline/comparison byte ledger and original
serialized final-report byte count stay unchanged. The helper reads and hashes
the complete original JSONL; it never substitutes a reserialized byte count,
zero bytes, a caller-supplied byte allowance or a synthetic receipt.

The publication READY marker is produced after the final REPORT. It is covered
by the existing producer and owner accounting; its Ref cannot be inserted into
the original REPORT because READY itself binds that REPORT hash. This repair
does not rewrite either publication object or change the publication barrier.

## Files and minimal numerical difference

- `geometry_witness.py`: stdlib-only, complete stable Ref3/JSONL authentication,
  exact source/model/CID/rank/host PID/start/namespace PID joins, original
  worker-root filename and mount alias join, all 368 roles matched to the saved
  full pool and view inventory, strict original observer schema and ND2/type/
  shape/stride/storage joins, and the corrected exact control equation.
- `consume_rank_new.py`: a new-file copy of the frozen predecessor with five
  exact substitutions: helper import; mandatory keyword-only `geometry_ref`;
  witness validation; replacement control-accounting call; added nonqualifying
  witness/accounting evidence in the rank result. All mathematical code remains.
- `consumer_cli.py`: new source-checked module loading and geometry sidecar join,
  with the original owner failure, stopped CID, source, device mount, loaded PID,
  four-rank report, numerical loader and causal DiagnosticStop checks retained.
- `test_geometry_witness.py`: pure CPU controls, no Torch/NPU/raw/model work.

AST comparison against the frozen predecessor confirms identical `bits`,
`metadata_union`, `compact_sidecar`, `unchanged_decode`, complete baseline
comparison loop, complete 48-layer numerical decode loop, `AliasIO`, and
`numerical_modules`. Numerical state limit `7.92e-7`, output peak `.00303`,
L2 `2**-13`, original CPU64/oracle/precast/rounding gates and complete inactive
byte comparison are unchanged.

## Public interface and sidecar

```
consumer_cli.consume(
    consumer_sr, model_sr, payload_sr,
    owner_ref, inspect_ref, loaded_ref, reports_ref,
    geometry_refs_ref
)
```

The original seven-key INPUT is unchanged. `geometry_refs_ref` separately binds
an immutable JSON sidecar with exactly these keys:

```
schema: "deltalog.geometry-witness-refs/v1"
consumer_source: consumer Ref3
model_source: original actual R36 model Ref3
payload_source: original R36 payload Ref3
reports_ref: original all-four report collection Ref3
geometry: four {rank, namespace_pid, report_ref, geometry_ref} objects
```

Ranks must be exactly 0, 1, 2, 3; namespace PIDs, report paths and geometry paths
are distinct. The sidecar carries host Ref3s. For namespace PID `p`, its paths
must be exactly (substitute the integer namespace PID):

```
<original host_payload_root>/FIRST-DECODE-{namespace_pid}/FIRST-DECODE-REPORT.json
<original host_payload_root>/FIRST-DECODE-GEOMETRY-p{namespace_pid}.jsonl
```

For example PID 311 means `FIRST-DECODE-311/FIRST-DECODE-REPORT.json` and
`FIRST-DECODE-GEOMETRY-p311.jsonl`. The second file is at the payload root,
not inside the worker directory. The helper derives the original guest alias
`/adakv-results/model/capture/FIRST-DECODE-GEOMETRY-p311.jsonl`, maps it through
the original authenticated CID mounts and requires exact equality to the host
Ref. It does not edit original REPORT guest refs.

The top-level result keeps `deltalog.independent-all4-firstdecode/v1` and all
old diagnostic fields. It adds `consumer_source`, `geometry_refs_ref` and
`repair_scope="geometry-control-accounting-only"`. Each successful rank result
adds `geometry_witness` and `geometry_accounting`; their qualification is false.
All full-model, normal-EOS, lifecycle, long160, performance and task qualification
flags remain false. A complete single-decode diagnostic still requires four
successful original per-rank numerical/inactive consumers and causally joined
actual DiagnosticStop logs.

## Controls and evidence limits

48 local pure CPU controls passed with no skips. They cover complete 368-role
positive evidence, nonzero production serialization causing the old equality
to fail while the new helper passes, original byte counting despite whitespace,
under/over/zero accounting, unchanged caps, stale source/model/CID/PID/start/rank,
wrong path/alias, content tampering, truncated bytes and truncated complete rows,
duplicate row roles/report roles/pool indices/pool extents, wrong storage/layout/
dtype/ND2/device/schema, duplicate/nonfinite JSON, symlink file/parent, mutation
during read, and complete or invalid four-rank sidecars.

The historical R34 retained reports and JSONL for PIDs 311, 312 and 314 were
also checked with these same two production helper functions. Each original
file was authenticated using the supplied original length and SHA256 before
parsing or temporarily materializing exact JSONL bytes. All three passed the
complete 368-role metadata join and the corrected accounting:

```
2968 prefill-control bytes + 495748 geometry bytes = 498716 charged bytes
```

Each original final REPORT is exactly 353782 bytes. The old equality fails for
all three reports. Results and original source/model/file identities are retained
in `R34_METADATA_FIXTURE_RESULT.json`. This was a metadata-only, nonacceptance
fixture check: no raw tensors, baseline contents, mathematics, NPU or model
execution. Original source identities remain R34; three retained ranks cannot
satisfy the CLI's all-four gate or qualify the R36 model.

The new host entry/recipe separately controls CPU-only Devices[], fixed cutoff,
read-only source/data set, stopped/no-writer checks, the original model-bound
snapshot journal/lease, original 2 GiB opt plus 30 GiB P/32 GiB workspace and
80 GiB total commitments, free-space reserve, cleanup and postverification.
The new consumer Ref must never replace the model Ref in the original P journal.

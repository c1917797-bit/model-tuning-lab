# R37 storage admission preparation review

## Status and hard clock

This is a new prepared source package. No R37 bound source, early owner result,
model owner result or model qualification is implied by these files. The frozen
R36 source, R36 payload, existing consumer source, historical reports and storage
ledger remain unchanged.

The original host admission still requires `time.time() + 3600 <= 1792313000`.
The last actual `h.main` entry is therefore **2026-10-18 07:43:20 UTC**. Source
preparation, own closure, early software, complete binding and source audit must
all finish before that entry. The early owner retains whole 180 seconds, its
original creation/child and cleanup bounds, and the model retains 3600/270/900/90.
The observed R36 failed binder duration of about 207 seconds is a failure prefix,
not an upper bound on a successful complete R37 bind. R37 must additionally
complete the original full closed15 verification and component admission.

If that sequence cannot finish in time, retain the prepared package. Do not
shorten PHASE, borrow an earlier receipt or manually set `prepared_only=False`.
The model's later CPU consumer needs its own original whole-budget admission
after exact model release; a model start close to this cutoff does not provide
a later CPU-consumer window.

## Minimal changed execution files

| File | Change |
|---|---|
| `firstdecode_refs.py` | Add `model_manifest=None` to `bind_closed`; replace its one `seal.readset` call with `readonly_closed_admission.readset(O, seal, contract, model_manifest)`. |
| `bind_source.py` | Pass `model_manifest=m` at the existing guarded `F.bind_closed` call. All ordering and binder qualification calls remain. |
| `readonly_closed_admission.py` | New strict read-only closed2 prevalidation, original adjusted accounting, original real storage061 check, complete original closed15 validation/readset and final no-writer/ledger/free-space fences. |
| `test_readonly_closed_admission.py` | 12 new positive/negative pure CPU controls; same-image full discovery must actually execute them. |
| `packet_contract.py` | New R37 root/output/owner identity; full software count 243 → 255. |
| `model_snapshot_budget.py` | Only new P leaf and journal identity strings; original adjusted arithmetic and runtime lease logic remain unchanged. |
| early `owner.py` | New early root, output identity, candidate name and exact R37 model-template root. Resource and cleanup logic remains unchanged. |
| `software_dependencies/early_scan_owner.py` | Byte-identical mirror of the new early owner for the existing source-based controls. |

The early owner `OWNER_EDITS.json` is regenerated with the complete original
donor body retained as `before` and the new identity-only owner body as `after`.
Existing mathematical/plugin source, historical inverse evidence and encoded
fixtures retain their original bytes. The 278 original model own files and ten
early own files are read against their complete frozen Ref3s before deriving
the new trees; copying just the small edited files would leave an incomplete
source closure.

## Generation and binding order

1. Materialize and hash the four reviewed patch files. Construct a new actual
   patch manifest from `PATCHES_LOCAL.json` with real remote file paths and
   unchanged file bytes/SHA256. Bind that patch manifest by its actual Ref3.
2. Run `prepare_r37.py --emit-patch --patch-manifest-ref ...`. The generator
   authenticates the original two templates and every declared own file, then
   composes the new trees entirely in memory. It emits UTF8 file contents and a
   receipt for structured `a_apply_patch` materialization. This mode creates no
   directory, source, output, process, ledger or lock.
3. Generate the early code, complete donor inverse and its `SOURCE_TEMPLATE`.
   Its actual Ref is needed in the model's early-software policy.
4. Generate plugin own Ref paths and `plugin/SOURCE_TEMPLATE`. Preserve all
   original bridge/operator/numerical predecessor refs.
5. Generate the model own files, all active own Ref3 replacements, new policy
   identity, the 255-case declaration and `COMMANDS_SPEC`. The command spec uses
   the original template-ref and SHA placeholders.
6. Generate model `SOURCE_TEMPLATE`, then derive `COMMANDS_FINAL` from the exact
   spec plus the actual new template Ref. The prepared template does not pin its
   own derived final ticket. Original `prebind_static.prepare` later adds that
   actual ticket to the bound file closure.
7. Apply both new trees through the structured patch writer and verify every
   emitted Ref against actual file bytes. Review retained old-identity tokens
   reported by the generator; historical copied evidence legitimately retains
   old names, while current executable identity expectations must match R37.
8. Run the original new-root cheap-prebind guard. Bind the new early source with
   `bind22.py`, run its source audit, then run the new same-image early owner
   using the exact final R37 model-template Ref.
9. Require **253 prepared-stage model controls + 26 unchanged payload controls**,
   no skips, exact source/template/image/PID joins and verified early release.
   The two existing bound-only controls remain deferred to the original model
   CPU stage. Its full discovery remains **255**.
10. Run the new ordinary binder: source/ticket guard → exact new early receipt →
    existing readonly binder guard → strict new closed admission helper →
    complete original component qualification → actual plugin and model bound
    source publication. The generator never produces either bound manifest.
11. Run source audit and the original fresh owner resource/time gates before
    actual model admission. Retain any failure and every existing file.

## Source identities and reuse boundary

The R37 payload source is the unchanged R36 all-four publication payload:
`deltalog-selected-firstdecode-renew24h-20261018-001-r36-all4-publication`.
Its JSONL observer, publication barrier, numerical math and qualification gates
are not edited by this storage-admission repair.

The prepared model has a new source root ending
`deltalog-first-real-decode-owned-renew24h-v1-101-repair37-closed-admission-20261018-001`,
runtime identity `NEW24H_FIRSTDECODE101R37admission_001`, new P leaf
`first-real-decode-model-snapshots-renew24h-R37admission-20261018-001` and journal
`MODEL_SNAPSHOTS_LEDGER.R37admission.json`. The fixed shared parent and original
`.storage061.lock` remain the same; the preparation generator touches neither.

The already prepared geometry CPU consumer host pins R36 model root, R36
template and R36 P leaf. It cannot accept an R37 Ref by changing only a manifest
field. R37 posterior consumption needs an explicitly reviewed new consumer
successor and an authorized full time window; keep the existing consumer source
unchanged.

## Local checks completed

The two entry changes have whole-source inverse checks against frozen R36 and
are recorded in `ENTRY_DELTAS.json`. The new admission helper's 12 controls
passed locally; their two source hashes were checked before creating
`PATCHES_LOCAL.json`. The generator parses successfully, its default mode runs
as a read-only plan, and its emitted identity gives the exact hard host-main
epoch `1792309400`. Actual full source emission, same-image early execution,
binder success, new bound Ref and all model gates remain separate evidence.

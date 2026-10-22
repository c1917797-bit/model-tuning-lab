# ON v3 continuation: completed startup failure, no numerical or performance result

This checkpoint records the completed ON v3 experiment under its original
12:00:55–18:00:55 UTC continuation envelope. It does not extend the original
2026-10-22 12:38:41 UTC report window. The user subsequently repeated the
instruction to continue; a new text-only diagnostic has its own authority,
source and output identity and is not admitted by this checkpoint.

## Actual result and classification

The immutable host RESULT has primary `subprocess.TimeoutExpired`: the
four-second host command running the two-second HTTP health probe did not
finish. Secondary errors are empty. Cleanup took 40.35200875008013 seconds;
the full 6,306-entry source-before and source-after mappings agree. The source,
RESULT, complete log and read receipts are pinned in INPUT_REFS.json.

The complete server log records an earlier AI Core error during multimodal
encoder memory profiling. Its asynchronous traceback is insufficient to name
the originating kernel or to attribute it to BOLE, the observer, or hardware.
Classification is **service-startup / environment-or-adaptation failure with
an unresolved native AI Core cause**, followed by a host health-probe timeout.
It is not an ON/OFF numerical mismatch, a performance result, or a successful
model run. Increasing the health timeout alone would not establish a repair.

Four G0 observer-install records exist. The complete receipt inventory has
13 files, but no G1/G2 request or projection-callsite result. The independent
projection reader has not been run because its actual input prerequisites
were not produced. This preserves the distinction between source controls,
observer installation, successful requests and independent numerical analysis.

## Termination and resource release

The unit `bole-boundary-on-v3-continuation-20261022t120055z-u3.service`
was observed failed with MainPID=0, ControlPID=0 and ExecMainStatus=3.
Both exact owned containers were retained, exited with code 137, OOMKilled=false,
PID=0 and no ExecIDs. Code 137 does not by itself mean OOM; the actual inspect
fields and own-stop receipts are retained.

The CPU cleanup has primary_error=null. The dense cleanup retains
primary_error equal to `repr(host_result.primary)`. Both have errors=[],
stopped=true, retained=true, deleted=false and own_on_protected=false. The
exception path did not emit summary.model_release. New lifecycle admission
must join the independently pinned dense cleanup through its exact owner,
source, first-host-fault and full inspect/stop/release chain; it must neither
invent that missing summary field nor change the failed primary to null.

The actual 17:07:30 UTC observation found no running NPU processes and the two
owners stopped. This is a historical observation, not future admission.
The actual Docker root is `/cache/docker`; the independently captured 17:12
observation found about 10.26 GB free there. `/var/lib/docker` is not the
configured Docker root. A new complete resource snapshot is mandatory before
another owner is created. Physical NPU 0–3 remain protected throughout.

## Evidence-driven next change

The retained image exposes native `--language-model-only`. Its actual source
chain sets all multimodal input limits to zero; with enable_mm_embeds=false,
the registry has no supported multimodal inputs. The model's tower marker
uses an uninitialized placeholder for disabled towers, and the native weights
loader skips that placeholder. This is source-based expectation, not proof of
the configuration or execution of a new service.

The next source therefore declares language_model_only=true,
skip_mm_profiling=false, enable_mm_embeds=false and limit_mm_per_prompt={}.
It must validate the real parser and EngineArgs, then obtain new true-NPU
requests and complete lifecycle evidence. Dense/candidate must later share
the identical text-only configuration and all other tested settings. Reduced
vision startup work or a changed cache budget is not a candidate generation
throughput gain, and this branch is not a claim to fix the native visual fault.

## Goal status

The corrected original short-pair gate still fails on complete frame-key
sets: ON 36 versus OFF 32, with earlier observed cross-generation differences.
Its evidence is unchanged. The low-observation performance path remains
unqualified on actual NPU numerical and multistep state gates. There is no
accepted whole-model >=10% gain, no formal TTFT/TPOT pair, and no final
GSM8K/HumanEval/MMLU acceptance. CPU controls, static source review and this
checkpoint do not substitute for those results.

The complete deliverable still requires a non-HYPIC, training-free opt-in
plugin; real NPU numerical/state/lifecycle gates; three same-config formal
dense/candidate pairs with fixed 1024-token output; and all three final tasks
with thinking off, max_tokens=2048, normal EOS and the allowed 1% loss reported
in both percentage points and relative terms. The next steps preserve every
original numerical threshold and exclusive output rule.

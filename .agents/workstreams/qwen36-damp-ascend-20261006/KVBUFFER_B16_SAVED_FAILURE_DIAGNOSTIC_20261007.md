# KVBuffer B16 saved failure diagnostic — 2026-10-07

## Goal and fixed gates

Long-term acceptance remains Qwen3.6-27B, Ascend plugin/monkeypatch,
same-stack/common-optimized dense paired E2E >=10%, separate TTFT/TPOT,
fixed1024 performance output and final LBv2/GSM8K thinkingOFF/max2048/normalEOS.
User task-loss<=1% is reported both pp/relative and never relaxes tensor gates.
The current short loop removes the first retained native-order-v2 B16 failure;
it does not reopen expired DAMP, reset clocks or substitute reports for E2E.
KV cutoff2026-10-08T08:29:54Z; portfolio2026-10-09T11:17:31Z unchanged.

## Original matrix evidence preserved

External root /cache/cch/qwen36-kvbuffer-parallel-20261006.
Full matrix /full-native-order-v2-20261007-1010 under that root.
MA0a5f parent exit1; actual B1 child exit0/all640 steps passed. MA0a79 and
MA0a7e independently verify exact unchanged64 source hashes and74 live-PID
proofs. This validates a numerical component only; old parent exit stays1,
consumer operation_authority=false, serving/E2E/task false. No synthetic PASS.
MA0a60 parent/child exit1; B16 eager160 passed, graphtrial0step37 active12
output_error0.003048780487804878 exceeds unchanged0.00303. Complete-state
L2=1.2322678210409127e-7, maxhead=2.2013525678823553e-7; state gate2e-6.
All finite/guards/pointers/input/untouched/log checks passed in that saved row.
Report SHA f5ad5ce944bccb8a4b536b8d5b218357d140b3ad9c54024f97922dcdbdc90b93.
Raw99004309B SHAff6c632f7655e396d1f9752591688496791538c6b787a2af24fb2f43f9353f14.
Both own matrix containers stopped/retained/Pid0/noExec/noOOM in MA0a6a.
Genuine MA0a5f/MA0a60/MA0a6a tool originals archived outsideGit, readback MA0a7e0:
8d295c13dfe4563f65e01f00359cde33a634ab909b8f2635d58dcf30bf987577,
4a1ea3cac7cc2258b1ea32073f102496ee2552031a7be83bb8c55bb8495d896c,
619d7b9c33913a6be9caf48ad12af5466549300bb4a0ee492548de5d57235ad9.

## NEW4 source reviewed and actual prerequisites

Only tools/b16_saved_step_diagnostic_v1/{replay.py,host.py,test_diagnostic.py,READY.md}
is added. Draft49967B SHAed70c22287aab8ca2fca315870c9f2c266606d1d4b64dbbd80495541715078cd;
MAIN reviewed complete source and applied via constrained a_apply_patch,
trace b57aede9-e741-49ce-8d76-4764c839518a, commit:false.
MA0a83 actual target-host17stdlib/defaultOFF/source64/3artifact/AST/diff checks0.
MA0a85 actual immutable-image660 no-device import/defaultCLI/source-audit and
CPU raw-format check0, Python3.12.13/Torch2.10.0+cpu/autoloadOFF. It performs
NO NPU validation. CPU_FORMAT_PREREQ.json SHAdc047ca9c77c9a4ed2790c608c99e2da844b075aa65c7854ddb33350255faa92,
external b16-diagnostic-no-device-preflight-20261007-1106. Owned530bf8... stopped
and retained/Pid0/noExec/noOOM; no device mappings.
Saved output has3 differing BF16 points among18432 active elements; max at
[b6,h5,d6]:0.00396728515625(bits15234) vs0.003997802734375(bits15235),
absolute3.0517578125e-5, native maxabs0.010009765625. This observed one-ULP
maximum is NOT a numerical pass or an E2E accuracy conclusion; exact candidate
precast cause is still pending actual single-step reproduction/history branch.

## Single new NPU diagnostic (unexecuted at this checkpoint)

/usr/bin/python3 -B /opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/b16_saved_step_diagnostic_v1/host.py --execute --script-sha256 f8dd33b87b65b64ae206f535ee4ff50d365dbb1ca346eab993382b44ca96e07c

Physical6->logical0, independent nonprivileged/no-network container,
8GiB/1CPU plus8GiB ordinary RAM reserve,600s TOTAL/90s cleanup reserve,
unique output b16-saved-step-diagnostic-v1-20261007. Fresh4–7 idle and actual
workload PID attribution are required; no unchanged matrix retry/threshold
change/old-result overwrite. Both eager+graph single steps must reproduce
original failed bytes; history branch is independent Torch logical-before,
not an exact candidate-UB/precast trace. All new raw before metrics retained.

## Safety and unresolved authority

Memory MA0a81 had~77.5GiB ordinary available; HugeTLB/network processes untouched.
Transient physical4 Python PIDs in MA0a81 were gone by MA0a82; disappearance
is not attributed, and MAIN stopped no external job. AgentGPU-v0 declares0–7
but onlysleep; cannbench_ds is active/privileged and not ours. Never stop it
for declarations alone; new actual unknown compute fails admission.
Current c388597 local commit remains unpublished: MA0a5c normal HTTPS push128,
missing GitHub authentication; MA0a65/MA0a7c found no configured auth seam.
No TLS weakening,forcepush,main edit or credential in code. Research proceeds
with exact reviewed local SHA evidence, remote publication remains pending.
No new E2E throughput/task result or usable non-HYPIC technique is claimed.

# Cross-chat BOLE takeover checkpoint (2026-10-22 19:40 UTC)

The user requested continuation in the current Codex chat from the ChatGPT chat
`继续昇腾论文迁移 Rerun Verification` (id
`6ad9b4f4-26a0-83ed-a321-0e7e1bf673c4`). Reading or messaging that chat
returned `ChatGPT conversation history was rate limited`. Its sidebar status
remained active, last updated at 2026-10-22 17:07:29 UTC. Therefore message
delivery and exclusive conversational ownership are **not** confirmed.
Archiving was not used as a surrogate for stopping execution.

Fresh direct target: chicaihong01/ma, peer
`lgw_a6109c51076a4a2c9d2674ca5a8704a0`, route decision `peer_direct`.
At 19:38 UTC, physical NPU 4–7 had 0% AICore, about 2868–2872 MiB HBM
each, and no NPU process. A matching process search found no BOLE, Qwen,
vLLM, or torchrun process. The BOLE continuation model container from V4 was
stopped and retained per its cleanup receipt. The shared
`MAIN_ADMISSION.lock` was acquirable nonblocking. Historical systemd units
shown as `active/exited` had no running main PID; this is not an active owner.
These are snapshots, not proof that the other chat can never resume.

The V4 text-only ON-only diagnostic result is
`/opt/host/vnf/austinov/run-bole-boundary-ON-v4-textonly_20261022T171000Z/RESULT.json`.
It has `primary:null`, `secondary:[]`, two completed 131-input/8-output
requests, and successful retained-container cleanup. It explicitly has
`candidate_qualification:false`, `formal_performance:false`,
`performance_gain_measured:false`, and `task_accuracy:false`.
Its short diagnostic request rate is **not** the fixed-1024-token formal
throughput result. No new BOLE success or matched dense/candidate result
may be claimed from V4.

Independent read-only comparison of the four ranks' V4
`G1/G2-PROJECTION-INTERNAL.json` receipts:

- Within each rank, full logical hashes of `projection_input`,
  `quant_return`, and `pre_reduce` are identical across G1 and G2.
- Each generation has one common `post_reduce` hash across all four ranks;
  the G1 and G2 post-reduce hashes differ. Rank 0 pre-reduce begins
  `9fe229b2e8b3f254` in both generations; post-reduce begins
  `604a2e4109963fd1` in G1 and `9ef3f29b51aa6816` in G2.
- The first **observed** divergence is thus at the row-parallel output
  reduction boundary, not before it. The trace captures a Python callsite,
  not the collective implementation or transport kernel. Weight bytes were
  not hashed. The reduction output aliases the local output storage.
  G1 is warmup and G2 is measured, so phase is confounded. This does **not**
  establish a BOLE mathematics defect or a native collective defect.
- The V4 `G2-COMPLETE.json` still says `alias_exclusion_proven:false` and
  `draft_actual_write_footprint_known:false`. The earlier ON/OFF V2 pair
  has unequal complete frame sets (36 versus 32). No numerical gate passes.

The reviewed V4 launcher at
`textonly_main_admission_v1_20261022T171000Z/main_admission_textonly_v1.py`
opens the same `MAIN_ADMISSION.lock`, takes exclusive nonblocking flock,
makes its FD inheritable, then execs the source-owned model command. Any
successor that uses the cards must also hold this lock for its **entire**
owner lifetime, use fresh source/output identities, and recheck actual
devices/processes, container lifecycle, resources, and source closure.
The internal V4 batch cutoff is 2026-10-22 23:10 UTC; this does not extend
the original 12:38:41 UTC report deadline.

Next discriminating diagnostic, if a separately frozen successor can be
prepared and admitted within its real time budget: compare at least two
already-warmed identical text requests, include matched OFF control, and
capture bounded per-rank local partial and reduced values with pinned
collective/callee provenance and weight identity. Check alias/in-place
semantics and state/request lifecycle independently. Preserve V4 failure and
do not rerun it unchanged. Only after actual NPU numerical/state/replay gates
pass may a fixed-1024-token, same-stack dense/candidate end-to-end screen
start; final GSM8K, HumanEval, MMLU and the applicable LongBench-v2 contract
remain outstanding. Do not touch physical NPU 0–3.

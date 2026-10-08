# Ascend architecture fit: HYPIC C1/C2 versus complete paper

Status: **partial-evidence**, reviewed 2026-10-09 against exact
`origin/main=ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2`.
This reuses the retained source/target audit, model bytes and historical NPU
receipts; it does not rerun an unchanged benchmark or consume NPU. The main
`ascend-architecture-fit` Skill and branch have the same Git blob. Its
required *pre-implementation* Git decision was not made in that order for
this already-running HYPIC derivative. The later audit cannot retroactively
satisfy that timing gate.

## Selected target and exact identity

- User-selected host lane: chicaihong01 physical NPU0–3, one TP4 model
  replica on 910B4 with HCCL AIV. The prior same-lane measurements used the
  pinned official vLLM-Ascend image
  `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`,
  `enable_cpu_binding=false` as a common setting and a BF16 text service.
  NPU4–7 and other containers are outside this case.
- Checkpoint directory `/cache/efim/Qwen3.6-27B`; live `config.json`
  SHA256 `69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c`
  reports `Qwen3_5ForConditionalGeneration` / `qwen3_5`, not a new Qwen3.6
  architecture. Its text config has 64 layers, 48 linear attention and 16
  full attention, BF16. Model index SHA256
  `a8ad2c26fb707ff8c245806315b03e3b4b74595528492423af5dae0ce39b4d9b`;
  tokenizer config/tokenizer hashes and text-only scope are in the immutable
  `PAPER_ARCHITECTURE_FIT.md` audit. Merely naming the model would not prove
  these features.
- The tested derivative is vLLM-Ascend plugin Git
  `3ad0967589304cd8fc4e7cff02f48ecc6125c89f`, not author SGLang. A
  later source revision `c12060c` was used in r12; do not merge these source
  identities when making activation or quality claims.

## Paper mechanism versus target/runtime

| Required part | Target fact and runtime seam | Fit level now |
| --- | --- | --- |
| C1 cached transition plus zero-start linear state | 48 linear-attention layers; derivative has a bounded GDN/state-reuse source path. The historical six-unit NPU0–3 performance pair independently validated same-lane execution, but not the whole paper. | `fits-now` only for the already-configured single-instance text hot-reuse seam; default launch still needs declared config. |
| C2 relocated full-attention KV plus seam repair | 16 full-attention layers and source-symbol audit for relocated/repaired hot reuse. The historical performance arm activated its worker path. Full explicit-boundary max-2048 quality has not passed. | `fits-now` as a bounded implementation mechanism, not quality/adoption acceptance. |
| C3 scatter/combine cold-segment parallelism | One TP4 instance supplies four ranks of one replica, not multiple independently routed replicas. Source audit expects full-scope C3.1–C3.6 absence. | `does-not-fit` the current service; needs new multi-replica implementation and resources. |

The source audits in `PAPER_ARCHITECTURE_FIT.md` passed bounded `hot-reuse`
and `qwen35-single-instance`, while `paper-complete` failed as expected for
C3.1–C3.6. They are symbol/capability audits, not substitutes for device
measurements. Historical same-identity c16/1024 performance audit SHA256
`de2f8af4a12dad9331e675ca1587aed6720aa8adc8aab551f6cfb2065ca78ac1`
records six valid units and 22.356163958% lower weighted TPOT median for
the HYPIC arm. This only supports that bounded configured path at that time.
Natural clean2 max-2048 quality had zero worker-hot PIDs; r12 explicit
segments had 52/57 scored four-worker proofs without a matched control.
Neither is a current full-pair quality pass.

MTP head and vision tower exist in the model, but this experiment does not
test MTP/multimodal behavior. No checkpoint retraining is required for the
already-tested text C1/C2 seam; a retraining method would require separate
authority and target. No claimed compatibility is inferred for quantized,
MoE, sparse or other checkpoints from this BF16 target.

## Decision and chronology boundary

The bounded architecture decision is C1/C2 `fits-now` only on the pinned
configured derivative and text checkpoint; complete HYPIC is
`does-not-fit` this single-replica service because C3 is absent. This is
**not** a declaration that full Paper-to-Ascend reproduction, lossless
quality, adoption or generalization passed. The old architecture note calls
itself retrospective; implementation and measurements were already under
way. Thus exact-main Skill step 6, "record the decision and evidence in Git
before implementation", remains unverified for this historical workstream.
The case is partial rather than a false verified pass.

The next new architecture-changing contribution must use a prospective
decision before source edits: pin target config/tokenizer/weights, operator
and runtime image versions, source/API seam, card topology, one-switch
hypothesis, missing mechanisms and allowed fit level. Only then implement
and measure. For this HYPIC campaign, finish the previously frozen
same-identity explicit-boundary max-2048 paired quality and repeated
performance on actually idle physical NPU0–3; keep C3 in a separately
authorized multi-replica workstream rather than treating TP ranks as replicas.

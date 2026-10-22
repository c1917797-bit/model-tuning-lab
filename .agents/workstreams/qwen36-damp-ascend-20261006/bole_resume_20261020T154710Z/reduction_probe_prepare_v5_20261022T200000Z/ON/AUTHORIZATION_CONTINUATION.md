# BOLE full-reduction diagnostic preparation ON

Derived from the existing user continuation and unchanged internal batch 2026-10-22 17:10:00–23:10:00 UTC. Old report cutoff 12:38:41 UTC is unchanged. MAIN review and resource admission remain pending. This preparation creates no resource owner or source freeze.

Arm ON: two existing 131-input/8-output requests plus retirement barrier, same text-only eager/native MTP configuration and observation path. Save complete pre/post-reduce BF16 operands to distinguish observed rounding and adaptation hypotheses. Warmup/measured is not two warmed repeats. Only BOLE observation policy differs between arms.

Original phase3600 and cleanup180 seconds, physical NPU4–7, protected0–3, unchanged numerical gates, OTHER3MiB/METADATA64MiB/RAW1GiB aggregate limits. An explicit8MiB projection-raw suballocation fits inside original64MiB and1GiB totals. No formal performance or task admission. MAIN must check exact source closure, both-arm inverse, original controls and new raw/arm controls before any freeze or device use.

Source /opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-reduction-ON-v5_20261022T200000Z
Output /opt/host/vnf/austinov/run-bole-reduction-ON-v5_20261022T200000Z
Batch MAIN-BOLE-REDUCTION-20261022T200000Z-ON-V5

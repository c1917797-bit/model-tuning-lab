# Compaction probe: actual build and Meta evidence

Recorded 2026-10-06. Scope: the independent packed-mask / GatherMask / exact-fallback diagnostic only. This records actual CANN compilation and no-device dynamic-load/Meta checks, not NPU arithmetic, production admission, graph replay, model accuracy, or end-to-end performance.

## Actual build v2

MAIN operation MA0346 completed with terminal exit 0. The configuration and build commands both returned 0; CXX, ASC, and linking completed. Artifact root: `/cache/cch/qwen36-damp-20261006/compaction-build-v2`. Build interval: 2026-10-06T13:18:36.970203+00:00 to 2026-10-06T13:21:38.209623+00:00. Receipt status: `compiled_no_device`.

- Image: `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`.
- CANN OPP 9.1.0, target `dav-2201`. Version source: `/usr/local/Ascend/cann-9.1.0/opp/version.info`, SHA256 `841279757459d4eabc1c8cfea69d3e1dc0fc9db3eb0c18100294cd5c1301b9e6`.
- Library: `/cache/cch/qwen36-damp-20261006/compaction-build-v2/libqwen36_damp_compaction_probe_ops.so`, SHA256 `080075a52c8a9b3736e9077149268bb48481b15a8e855e3dca82617bf8489b9c`.
- Actual defined symbol: `000000000009fe00 T qwen36_damp_compaction_kernel`.
- Dynamic-symbol artifact SHA256: `fddc42d93ba7a9742f7affb0b49cf8da8a6eb7e88295fee7b44851e0161bce72`.

Commands were `cmake -S /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/operator/quantizer/compaction_probe -B /cache/cch/qwen36-damp-20261006/compaction-build-v2 -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3`, then `cmake --build /cache/cch/qwen36-damp-20261006/compaction-build-v2 -j2`. Log SHA256 values respectively: `6be9d900b568c4de90e2cd758a7fea4ae71d96654d25189c1917ff0abb8608cd` and `ceabd6176ef104ecb1ce50b0c2c37f1b6bc84acfaedf007d9ff9a0efe3ad5304`.

The receipt retains the schema tag `damp_compaction_probe_build_v1`; the actual v2 directory, source hashes, and library hash identify this build. It is not the failed v1 binary. The v1 source snapshots and failure artifacts remain preserved; the two minimal compatibility changes are documented in `V2_CHANGES.md`.

## Actual no-device load and Meta

MAIN operation MA0358 completed with terminal exit 0. Artifact root: `/cache/cch/qwen36-damp-20261006/compaction-meta-v1`. The parent report completed at 2026-10-06T13:23:38.123994+00:00 with status `pass`, scope `actual no-device load/schema/Meta only`. The frozen gate completed at 2026-10-06T13:23:38.008030+00:00 with status `pass`, scope `Meta shape/dtype ONLY`.

Actual registrations:

```text
qwen36_damp_compaction_probe::prepare(Tensor accepted, Tensor x_bits, Tensor scale_bits, Tensor magnitude) -> ()
qwen36_damp_compaction_probe::compact(Tensor accepted, Tensor x_bits, Tensor scale_bits, Tensor magnitude) -> (Tensor, Tensor, Tensor, Tensor)
```

The hash-bound runner's Meta loop/assertions passed for N=64, 448, and 896: prepare returned void and compact returned four INT32[N+16] tensors. The gate report has `rows: []`; it does not serialize individual positive rows. The parent report separately preserves 18 raw negative rejection records: N=0/63/65/447/449/897, wrong dtype, wrong shape, and noncontiguous input, each at both entrypoints. All were rejected. These are shape/dtype/contiguity checks, not device-value or device-memory tests.

Actual versions were torch `2.10.0+cpu`, torch_npu `2.10.0.post4`, and ASCEND_HOME_PATH `/usr/local/Ascend/cann-9.1.0`. Actual loaded-library records contain the above probe library and `/usr/local/python3.12.13/lib/python3.12/site-packages/torch_npu/lib/libtorch_npu.so`, SHA256 `83fb9a0eb249aef6bca7f8463047fcb4d3062cc4849f17ddf31a5e050c838842`.

## Read-only identity cross-check

The recorded build sources (8 entries, including the external frozen exact helper) match the runtime manifest (13 entries, including external helper/oracle). Each runtime source hash matches the current file; no runtime source was changed by this evidence note. The actual SO file matches the build, parent, and gate library hashes. Receipt hashes were independently recomputed:

- `compaction-build-v2/build-receipt.json`: `b874ed8b88d2343e3f4457a6090b34f386b4a891ef047695cb02c8306f53b98d`.
- `compaction-build-v2/source-receipt.json`: `15df39d2252e53dd7cb0f1e4f99c1fe51f3214650be24f76d8439cb64f0278bc`.
- `compaction-meta-v1/parent-report.json`: `5f87f31d1b70a7c481787e6a39a53a740b71c8d4a37642701276b1c8def40bfa`.
- `compaction-meta-v1/gate/report.json`: `7244a76ff7c2dc1d223f880742979bada3a9e8a675e128335913f62b3d69bbd4`.

The parent embeds the same build/source receipt hashes. Child read-only identity check completed with exit 0. This note is deliberately outside the frozen runtime receipt; it changes neither the runner nor the compiled inputs.

## Remaining gates

All reports explicitly have NPU executed=false. Physical SoC was not runtime-observed. Graph, production integration, recurrence, and performance were not executed/measured. Meta success does not establish physical ND layout, packed-mask semantics, retained ordering/count, guards, input preservation, pointer stability, exact fallback/scatter correctness, or actual CANN stream behavior.

Next: MAIN alone may run the preregistered, fresh physical-NPU4 eager compaction/scatter matrix (49 changed-buffer cases across N=64/448/896), preserving its first failure without overwrite/retry. Only its actual result can admit this seam for production review. The production DAMP candidate still separately requires saved-step45 parity, B1/B16 160-step independent-feedback state/output gates, general-SR coverage, graph validation, paired end-to-end performance, and final task accuracy. This diagnostic is not a performance candidate. The existing DAMP deadline is not reset.

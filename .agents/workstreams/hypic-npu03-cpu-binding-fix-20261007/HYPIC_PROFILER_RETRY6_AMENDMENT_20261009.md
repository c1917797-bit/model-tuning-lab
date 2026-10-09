# HYPIC profiler retry6 amendment — prospective Decode diagnostic

Retry5 is terminal and environment-invalid: the external `Maxon4ick_vllm`
container entered physical NPU0 before any valid Decode capture. Its raw root
remains immutable. The valid retry2 Prefill is not repeated.

Only the Decode *diagnostic stimulus* changes prospectively. The original
32-token stream could yield 16 HTTP chunks after `/start_profile` even if the
server had generated them before the endpoint completed and buffered them.
Retry6 uses a 512-token fixed-output, `ignore_eos=true` streaming request and
requires at least 64 nonempty post-start chunks. It records successful
profile-start and profile-stop UTC times. The independent audit must parse a
copy of all four ranks and demonstrate actual NPU Decode kernels inside the
capture window; HTTP chunk count alone is insufficient. This is a diagnostic
protocol change, not a new paired quality/performance ruler or a revision of
the frozen r13 decision. The other model, image, source, service, warmup,
physical NPU0-3, port 8223, guard, and exact-cleanup settings are unchanged.

New, unused root:
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/profiler-hypic-hotcold-20261009-r6`.
The container name, Docker label, and guard attempt field now derive from this
root to avoid the stale r4 label retained in retry5's guard JSON.

Do not launch until a fresh direct-route snapshot proves physical NPU0-3 and
port 8223 actually idle and no other controller owns the lane. Keep the
continuous process guard; any external re-entry invalidates this attempt and
releases only its exact owned resources. The original Prefill `>=47` numeric
column gate remains missed; this amendment cannot retroactively change it.

# H8 B6 separate-fence diagnostic and comparator defect

## Actual outcome, not a successful full gate

MA exec-0000000000000ec6 completed exit1 in281.384s.
Root: /cache/cch/qwen36-paper-preparation-20261007/recurrent/MAIN-h8-b6-fenced-diagnostic-20261007-001.
Original whole operation is H8_B6_DIAGNOSTIC_OPERATION_20261007.json
SHA13d938d74b1fdc8480c95d7c1192c3a5965ba4a1eee7ad6374219cb3856a86d2.
RESULT.json SHA d1303a5263764912256c8482cdc68a5c65f90246053e5bd6282256a9e9bf9b5b,
293724 bytes, status diagnostic_failed, secondary=[].

Native and H8 ran in distinct actual processes, each exactly one B6 target.
Their separate target synchronizations passed; H8 prepare synchronization also
passed. The exact common actual pre-target.pt SHA is
f4801eb52ba937141ce5b303917693a4525910f22deedec6e9938d001ed82b5b.
This did not reproduce the historical warm fullv2 vector-core507035 exception.

The original CPU receipt SHA
e1896f5c15dceb8adaa6dc7846868e12cae1bc2f262bafbd15daa4180312ce82
reported output_error0, complete_state_l2=1.1331556615308631e-08 and
max_per_head_l2=5.7787388639726184e-08, inside original .00303/2e-6/2e-6
limits; guards=false caused actual comparison exit1.
Those partial metrics do not override the original failure.

## Source-proven observer defect and narrowly scoped next action

The frozen fullv2 oracle guarded() allocates a full raw tensor with64 FP32
sentinel elements on either side, and returns both the interior writable view
and the FULL raw tensor. allocate() guards[name] is that full backing storage.

The diagnostic v1 compare_cpu.py used torch.equal on the complete before/after
guards[name] tensors. It therefore compares legitimately mutable payload as
if it were a redzone. This is a real comparator error, not proof that the
actual boundary guards passed or failed.

Next action: a new immutable-source CPU-only reanalysis of retained actual
pre/post tensors. Compare both64-element redzones bitwise and sentinel values;
check interior payload equality to the actual state view, source-bound storage
offset/shape/stride/pointer relations, all other original state/log/input/finite
invariants and unchanged numerical limits. Include a legitimate-payload-change
positive check and left/right guard-corruption negative checks. Do not restart
the old NPU container, rerun an unchanged device matrix, rewrite raw files,
relax limits or relabel original operation exit1 as success.

A corrected one-step comparison, if it passes, remains a one-step diagnostic.
It cannot resolve the historical warm B14/B11-to-B6 transition, graph/allocator/
cache/device attribution, all-batch/lifecycle/mixed/model correctness, paired
end-to-end performance or task accuracy.

## Independent authority and cleanup

MA0ece independently checked exact RESULT/raw/report hashes, exact own CID
c6409c857ce80ab21c0e34d832bc5e0f00a1f69bff47c448a541c4c7f7ad2da3
stopped/retained/Pid0/noExec/noOOM, physical4–7 idle and healthOK.
Protected0–3 original worker PIDs585850–53/start31858811 were unchanged.
MA0ed1 independently consumed the WHOLE original failed operation and RESULT:
original_authority_verified=true, diagnostic_success=false,
complete_matrix_steps_verified=0, model/E2E/tasks=false.
Their original envelopes are retained in H8_B6_DIAGNOSTIC_INDEPENDENT_20261007.json
and H8_B6_DIAGNOSTIC_CONSUMER_20261007.json. No external container was stopped.

The authorized32GiB free HugeTLB release is already complete; OVS and its24GiB
NUMA3 capacity remain intact. No further memory release is authorized here.
KVBuffer cutoff remains2026-10-08 08:29:54Z; portfolio cutoff remains
2026-10-09 11:17:31Z. Neither observer repair nor preparation resets them.

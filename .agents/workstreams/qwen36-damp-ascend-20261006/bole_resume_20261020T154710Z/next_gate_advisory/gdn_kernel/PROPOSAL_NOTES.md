# Advisory scope

These files are an unqualified proposal. Nothing has been installed in the
model source, Git worktree, host, container or device. The only local execution
is Python AST/bytecode compilation, a default-OFF CLI, and a stdlib FP64 algebra
check. The local Python environment has no Torch. No NPU compilation, tensor
correctness, latency or throughput result is claimed.

The public entry is `gdn3_fp32.py`; `gdn3_triton_kernels.py` is its private JIT
sibling. The entry imports neither Torch nor Triton at module load. Executing
it without arguments prints disabled JSON; `--help` uses argparse. There is no
device-launching CLI. An existing owned stage must explicitly set
`BOLE_GDN3_TRITON_ENABLE=1`, pass `enabled=True`, `arm_verified=True`, and supply
exact implementation, kernel and original `core112.py` Ref3 identities through
the existing `sourceio` reader. These switches are not an independent resource
admission mechanism: MAIN must own and validate the actual stage.

The current geometry is deliberately fixed to B1, H12, T3, Dk128, Dv128 and
parents `(-1,0,0)`. This corresponds to the captured TP4 target, not a new batch
or head-count qualification. Arbitrary input strides are explicit, including
the canonical state view whose Dk stride is 1 and Dv stride is 128. A selected
terminal output is a new canonical contiguous tensor; cancellation returns the
original clone semantics and may preserve the input's noncontiguous strides.
No live arena is a store target.
The existing selected-path transaction remains the sole persistent publisher.

# Exact algebra

Let the initial canonical state be S. The original factor matrix is

`P = exp(log(gamma) @ inclusive.T)`.

The proposal keeps that exact Torch operation sequence, including the actual
original inclusive matrix. It also keeps the original Torch FP32 broadcast
division `R[i,j] = P[i]/P[j]`. It does not replace P with direct gamma products,
Triton log/exp, or approximate Triton division. Before launch it checks every
P is positive/finite and every R is finite, including masked-off entries whose
infinity would contaminate the original dense G/C expressions.

For each head, the private kernel computes the six real state-vector products
`q_i @ S` and `k_i @ S` and seven vector inner products. With `r_i = beta_i *
(v_i - P_i * (k_i @ S))`, the fixed depth-one tree has

```
U0 = r0
U1 = r1 - (beta1 * R10 * dot(k1,k0)) * r0
U2 = r2 - (beta2 * R20 * dot(k2,k0)) * r0

O0 = P0*(q0@S) + dot(q0,k0)*U0
O1 = P1*(q1@S) + (R10*dot(q1,k0)*U0 + dot(q1,k1)*U1)
O2 = P2*(q2@S) + (R20*dot(q2,k0)*U0 + dot(q2,k2)*U2)
```

This is exactly the original `r - G@r` because G has only entries (1,0) and
(2,0) and G squared is zero. It is the original `P*(q@S) + C@U`, with forbidden
sibling entries omitted mathematically. Factors remain `(P,U)` in the original
shapes. No normalization, gating, convolution or BF16 output boundary changes.

For terminal 0 the private selected state is
`P0*S + outer(k0,U0)`. For terminal i in {1,2} it is
`Pi*S + (outer(k0*(Pi/P0),U0) + outer(ki,Ui))`. Its division weights are again
formed with the original Torch `P[...,terminal:terminal+1]/P` expression. For
None, the API returns a private clone, matching cancellation semantics.

# Precision and compilation uncertainties

Every load, product, reduction, factor and output is FP32. There is no `tl.dot`,
TF32/HF32 path, FP16/BF16 conversion, or change to the original epsilon. The
global existing NPU HF32 policy must be False. Output conversion to BF16 belongs
to the unchanged caller after this API returns.

The important remaining difference is FP32 summation order. `tl.sum` can use a
different reduction tree than CANN's original FP32 matmul. The backend may also
contract FP32 multiply/add into FMA. This proposal does not claim bitwise O/U or
selected-state identity. It launches with backend defaults; every exact
configuration still requires actual compilation and the unchanged independent
bounds.

The exact installed `triton_ascend_compiler.py` was inspected, SHA256
`253bdb0d9bf2d092c8c1ae40cc610b2d00c534b127f9d258e9e8e1a221934002`.
`NPUOptions.num_warps` is real (default32), and the actual imported native
`l2norm_native.py` uses `num_warps` autotune configurations. The private kernel
there uses FP32 `tl.sum`, 2D broadcasting and `vllm.triton_utils`, providing
primary-source API evidence for those constructs. This does not establish that
the complete proposed kernels compile or run.

In that copied compiler, `enable_fp_fusion` is only a dataclass declaration:
there is no use or forwarding of that option elsewhere in the file. Its False
value would therefore not prove FMA was disabled. `disable_fma` is forwarded to
`--disable-fma` only in the `force_simt_only` branch. The installed default
`compile_mode='unstructured_in_simt'` sets `force_simt_template`, proceeds through
the normal linalg/binary stages, and does not take that SIMT-only branch. The
proposal consequently supplies neither knob and makes no disabled-contraction
claim. It does not assume CUDA `div_rn` or libdevice APIs. Actual TTIR/lowered
IR and emitted binary would be needed to resolve contraction for a compiled
variant.

The primary installed l2norm import has SHA256
`520f4513ef4fc97e6b88dc07877cca8e29da0d34e44673fe989e3af002d86381`.
Keep both exact installed files in the eventual immutable source ticket along
with the actual image and backend version. The wrapper resolves its JIT sibling
by checked absolute path before import, rather than importing an ambient module
with the same name.

P should be bitwise identical to repeated original `core112.verify` on the same
inputs because its Torch expressions are unchanged; the qualification reader
must test this rather than infer it. Ratios should be compared too while the
first replay records them. The reference calculations stay in untouched
`oracle112.py` and `independent_model.old112`; the candidate never imports or
edits those numerical helpers to compute a success flag.

The forward grid is `(12,128/tile_v)` with tile_v32 initially. Every lane is a
real DV column. The selected-state grid is `(12,128/tile_k,128/tile_v)` with
32x32 initially. There is no logical padding, dummy occupancy or device selector.
Alternative 16/32/64 commit tiles or forward64 are separate immutable
configuration variants, not a claim that unexecuted variants are qualified.

# Required first actual qualification

1. Freeze one source ticket with the exact image, original kernel/reference
   files, all 192 actual r23 GDN tree-frame input refs (four ranks times 48),
   fixed geometry, tile_v32 and commit32x32. Reopen the original owner,
   independent result, raw hashes and cleanup chain. Root remains the only
   device admission authority.
2. In the exact same image with Devices[], run the real disabled/help/source
   closure, compile every complete source file without importing native NPU
   workers, and prove exact original mathematical references. Do not count AST
   or the local stdlib algebra check as a device numerical result.
3. In one freshly owned singleton physical4/guest0 stage, replay every saved
   actual normalized q/k/v/beta/gamma/state. Run the original core unchanged and
   the candidate on the same inputs with HF32 OFF. Check every input bitwise
   unchanged, actual noncontiguous strides, no alias stores and finite results.
4. Export actual candidate O/P/U and all three private terminal states under the
   original bounded raw limit. One 192-frame variant needs roughly 440 MiB of
   FP32 result tensors; do not duplicate the immutable large input corpus or
   combine many tile variants into one over-budget capture. Each terminal must
   come from the actual selected-state kernel, not CPU reconstruction.
5. After the NPU owner stops and retains its container, a separate Devices[]
   consumer reconstructs literal FP64 sequential recurrence for parents
   `(-1,0,0)`. For O, U, P and each selected state, use the original `old112`:
   `peak_abs <= 2e-5 + 2e-4 * max_abs(reference)` AND `relative_l2 <= 2e-4`.
   Also prove P bitwise against the unchanged original core's P, scalar factor
   shapes, all 192 frame joins, and original physical/native state orientation.
   Retain failures and all actual metrics; no epsilon relaxation or selective
   frame exclusion is permitted.
6. Only a complete same-image source-bound independent pass can admit a
   service-only opt-in adapter. Preserve the original r23 diagnostic source.
   Require an actual new model lifecycle and normal task acceptance afterward.

The wrapper currently validates sources, finiteness and topology on each call
for a first controlled replay. Its wall time must not be compared against an
unguarded bare original core. A future common-precondition kernel microbenchmark
can separate validation from equally scoped timed regions, but component timing
cannot establish the required >=10% 1024-output-token HTTP gain.

# Earlier optimization to consider

The existing `Bridge._gdn` computes all three candidate states with three
`core112.commit` calls. `service_runner._ctx` then discards those states, while
`stage_selected_path` computes the selected state again. The service consumer
uses all three O/P/U rows and the selected published state only. A separately
source-pinned service-only GDN wrapper can omit these three unused commits
without changing any O/P/U, selected state, or original reference. Keep the
qualified r23 diagnostic's all-node capture unchanged. This should be evaluated
before attributing any gain to the new Triton kernel.

The current service path also performs repeated source/prerequisite JSON reads
inside each native convolution call. Any future capture-disabled production
path must retain the actual source/ABI/callable ownership guarantees while
placing immutable-ticket validation at a declared boundary; silently omitting
those checks or reporting diagnostic timings as formal performance is invalid.

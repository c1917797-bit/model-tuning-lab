"""ADVISORY kernels only; importing defines JIT functions, never launches them.

The public default-OFF wrapper imports this module only inside an existing
admitted owner after exact source checks. No input pointer is ever a store target.
"""
from vllm.triton_utils import tl, triton


@triton.jit
def forward_ou(
    Q, K, V, BETA, P, RATIO, S, O, U,
    q_b: tl.constexpr, q_h: tl.constexpr, q_n: tl.constexpr, q_d: tl.constexpr,
    k_b: tl.constexpr, k_h: tl.constexpr, k_n: tl.constexpr, k_d: tl.constexpr,
    v_b: tl.constexpr, v_h: tl.constexpr, v_n: tl.constexpr, v_d: tl.constexpr,
    be_b: tl.constexpr, be_h: tl.constexpr, be_n: tl.constexpr,
    p_b: tl.constexpr, p_h: tl.constexpr, p_n: tl.constexpr,
    r_b: tl.constexpr, r_h: tl.constexpr, r_i: tl.constexpr, r_j: tl.constexpr,
    s_b: tl.constexpr, s_h: tl.constexpr, s_k: tl.constexpr, s_v: tl.constexpr,
    H: tl.constexpr, DV: tl.constexpr, TILE_V: tl.constexpr,
):
    bh = tl.program_id(0)
    request = bh // H
    head = bh % H
    kk = tl.arange(0, 128)
    vv = tl.program_id(1) * TILE_V + tl.arange(0, TILE_V)
    qb = request * q_b + head * q_h
    kb = request * k_b + head * k_h
    vb = request * v_b + head * v_h
    bb = request * be_b + head * be_h
    pb = request * p_b + head * p_h
    rb = request * r_b + head * r_h
    sb = request * s_b + head * s_h

    # Six vectors, one real state tile; all accumulation stays FP32.
    q0 = tl.load(Q + qb + kk * q_d).to(tl.float32)
    q1 = tl.load(Q + qb + q_n + kk * q_d).to(tl.float32)
    q2 = tl.load(Q + qb + 2 * q_n + kk * q_d).to(tl.float32)
    k0 = tl.load(K + kb + kk * k_d).to(tl.float32)
    k1 = tl.load(K + kb + k_n + kk * k_d).to(tl.float32)
    k2 = tl.load(K + kb + 2 * k_n + kk * k_d).to(tl.float32)
    state = tl.load(S + sb + kk[:, None] * s_k + vv[None, :] * s_v).to(tl.float32)
    qs0 = tl.sum(q0[:, None] * state, axis=0)
    qs1 = tl.sum(q1[:, None] * state, axis=0)
    qs2 = tl.sum(q2[:, None] * state, axis=0)
    ks0 = tl.sum(k0[:, None] * state, axis=0)
    ks1 = tl.sum(k1[:, None] * state, axis=0)
    ks2 = tl.sum(k2[:, None] * state, axis=0)

    kk10 = tl.sum(k1 * k0, axis=0)
    kk20 = tl.sum(k2 * k0, axis=0)
    qk00 = tl.sum(q0 * k0, axis=0)
    qk10 = tl.sum(q1 * k0, axis=0)
    qk11 = tl.sum(q1 * k1, axis=0)
    qk20 = tl.sum(q2 * k0, axis=0)
    qk22 = tl.sum(q2 * k2, axis=0)
    beta0 = tl.load(BETA + bb).to(tl.float32)
    beta1 = tl.load(BETA + bb + be_n).to(tl.float32)
    beta2 = tl.load(BETA + bb + 2 * be_n).to(tl.float32)
    p0 = tl.load(P + pb).to(tl.float32)
    p1 = tl.load(P + pb + p_n).to(tl.float32)
    p2 = tl.load(P + pb + 2 * p_n).to(tl.float32)
    ratio1 = tl.load(RATIO + rb + r_i).to(tl.float32)
    ratio2 = tl.load(RATIO + rb + 2 * r_i).to(tl.float32)
    v0 = tl.load(V + vb + vv * v_d).to(tl.float32)
    v1 = tl.load(V + vb + v_n + vv * v_d).to(tl.float32)
    v2 = tl.load(V + vb + 2 * v_n + vv * v_d).to(tl.float32)

    r0 = beta0 * (v0 - p0 * ks0)
    r1 = beta1 * (v1 - p1 * ks1)
    r2 = beta2 * (v2 - p2 * ks2)
    g10 = (beta1 * ratio1) * kk10
    g20 = (beta2 * ratio2) * kk20
    u0 = r0
    u1 = r1 + (-g10 * r0)
    u2 = r2 + (-g20 * r0)
    o0 = p0 * qs0 + qk00 * u0
    o1 = p1 * qs1 + ((ratio1 * qk10) * u0 + qk11 * u1)
    o2 = p2 * qs2 + ((ratio2 * qk20) * u0 + qk22 * u2)
    outbase = bh * 3 * DV + vv
    tl.store(O + outbase, o0)
    tl.store(O + outbase + DV, o1)
    tl.store(O + outbase + 2 * DV, o2)
    tl.store(U + outbase, u0)
    tl.store(U + outbase + DV, u1)
    tl.store(U + outbase + 2 * DV, u2)


@triton.jit
def selected_state(
    S, K, P, WEIGHTS, U, OUT,
    s_b: tl.constexpr, s_h: tl.constexpr, s_k: tl.constexpr, s_v: tl.constexpr,
    k_b: tl.constexpr, k_h: tl.constexpr, k_n: tl.constexpr, k_d: tl.constexpr,
    p_b: tl.constexpr, p_h: tl.constexpr, p_n: tl.constexpr,
    w_b: tl.constexpr, w_h: tl.constexpr, w_n: tl.constexpr,
    u_b: tl.constexpr, u_h: tl.constexpr, u_n: tl.constexpr, u_d: tl.constexpr,
    H: tl.constexpr, DK: tl.constexpr, DV: tl.constexpr,
    TILE_K: tl.constexpr, TILE_V: tl.constexpr, TERMINAL: tl.constexpr,
):
    bh = tl.program_id(0)
    request = bh // H
    head = bh % H
    kk = tl.program_id(1) * TILE_K + tl.arange(0, TILE_K)
    vv = tl.program_id(2) * TILE_V + tl.arange(0, TILE_V)
    sb = request * s_b + head * s_h
    kb = request * k_b + head * k_h
    pb = request * p_b + head * p_h
    wb = request * w_b + head * w_h
    ub = request * u_b + head * u_h
    state = tl.load(S + sb + kk[:, None] * s_k + vv[None, :] * s_v).to(tl.float32)
    k0 = tl.load(K + kb + kk * k_d).to(tl.float32)
    u0 = tl.load(U + ub + vv * u_d).to(tl.float32)
    p0 = tl.load(P + pb).to(tl.float32)
    if TERMINAL == 0:
        result = p0 * state + k0[:, None] * u0[None, :]
    else:
        pt = tl.load(P + pb + TERMINAL * p_n).to(tl.float32)
        kt = tl.load(K + kb + TERMINAL * k_n + kk * k_d).to(tl.float32)
        ut = tl.load(U + ub + TERMINAL * u_n + vv * u_d).to(tl.float32)
        weighted_k0 = k0 * tl.load(WEIGHTS + wb).to(tl.float32)
        result = pt * state + (weighted_k0[:, None] * u0[None, :] + kt[:, None] * ut[None, :])
    offset = bh * DK * DV + kk[:, None] * DV + vv[None, :]
    tl.store(OUT + offset, result)

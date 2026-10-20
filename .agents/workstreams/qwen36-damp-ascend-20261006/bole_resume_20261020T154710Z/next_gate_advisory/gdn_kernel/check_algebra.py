"""Stdlib FP64 algebra check only. This does not import/execute a tensor kernel."""
import json
import math
import random


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def row_matrix(row, matrix):
    return [sum(row[i] * matrix[i][j] for i in range(len(row)))
            for j in range(len(matrix[0]))]


def literal(q, k, v, beta, gamma, initial):
    states, outputs, updates = [], [], []
    for n, parent in enumerate((-1, 0, 0)):
        before = initial if parent == -1 else states[parent]
        decayed = [[gamma[n] * x for x in row] for row in before]
        prediction = row_matrix(k[n], decayed)
        update = [beta[n] * (value - prediction[j])
                  for j, value in enumerate(v[n])]
        after = [[decayed[i][j] + k[n][i] * update[j]
                  for j in range(len(update))] for i in range(len(k[n]))]
        updates.append(update)
        states.append(after)
        outputs.append(row_matrix(q[n], after))
    return outputs, updates, states


def factored(q, k, v, beta, gamma, initial):
    p = [math.exp(math.log(gamma[0])),
         math.exp(math.log(gamma[0]) + math.log(gamma[1])),
         math.exp(math.log(gamma[0]) + math.log(gamma[2]))]
    ks = [row_matrix(key, initial) for key in k]
    qs = [row_matrix(query, initial) for query in q]
    r = [[beta[n] * (value - p[n] * ks[n][j])
          for j, value in enumerate(v[n])] for n in range(3)]
    updates = [r[0]]
    for n in (1, 2):
        g = (beta[n] * (p[n] / p[0])) * dot(k[n], k[0])
        updates.append([r[n][j] - g * r[0][j] for j in range(len(r[0]))])
    outputs, states = [], []
    for n in range(3):
        path = (0,) if n == 0 else (0, n)
        outputs.append([
            p[n] * qs[n][j] + sum((p[n] / p[a]) * dot(q[n], k[a]) * updates[a][j]
                                  for a in path)
            for j in range(len(v[0]))])
        states.append([
            [p[n] * initial[i][j] + sum(k[a][i] * (p[n] / p[a]) * updates[a][j]
                                       for a in path)
             for j in range(len(v[0]))] for i in range(len(k[0]))])
    return outputs, updates, states


def numbers(value):
    if isinstance(value, (list, tuple)):
        for item in value:
            yield from numbers(item)
    else:
        yield value


def main():
    random_ = random.Random(20261020)
    peak = 0.0
    count = 0
    for _ in range(256):
        dk, dv = 5, 7
        q = [[random_.uniform(-.5, .5) for _ in range(dk)] for _ in range(3)]
        k = [[random_.uniform(-.5, .5) for _ in range(dk)] for _ in range(3)]
        v = [[random_.uniform(-1, 1) for _ in range(dv)] for _ in range(3)]
        beta = [random_.uniform(.01, .99) for _ in range(3)]
        gamma = [random_.uniform(.01, 1.1) for _ in range(3)]
        initial = [[random_.uniform(-1, 1) for _ in range(dv)] for _ in range(dk)]
        truth = literal(q, k, v, beta, gamma, initial)
        actual = factored(q, k, v, beta, gamma, initial)
        error = max(abs(x - y) for x, y in zip(numbers(actual), numbers(truth)))
        peak = max(peak, error)
        assert error <= 2e-12, error
        count += 1
    print(json.dumps(dict(schema='bole.gdn3-stdlib-algebra-check/v1', cases=count,
                          peak_FP64_abs=peak, software_algebra_only=True,
                          tensor_runtime_imported=False, NPU=False,
                          actual_kernel_executed=False,
                          original_FP32_bounds_verified=False,
                          mathematically_qualified=False, formal_success=False)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

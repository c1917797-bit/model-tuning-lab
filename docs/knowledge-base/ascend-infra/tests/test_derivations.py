"""Educational algebra checks only: never NPU/model qualification."""
import unittest


def identity(n):
    return [[float(i == j) for j in range(n)] for i in range(n)]


def add(a, b, scale=1):
    return [[x + scale*y for x, y in zip(ar, br)] for ar, br in zip(a, b)]


def mul(a, b):
    return [[sum(x*y for x, y in zip(ar, bc)) for bc in zip(*b)] for ar in a]


def approx_inverse(l, terms):
    p = [[-x for x in row] for row in l]
    power = identity(len(l))
    result = [[0.0]*len(l) for _ in l]
    for _ in range(terms):
        result = add(result, power)
        power = mul(power, p)
    return result, power


def gdn_step(state, k, v, alpha, beta):
    bar = [[alpha*x for x in row] for row in state]
    residual = [beta*(v[i]-sum(x*y for x, y in zip(row, k)))
                for i, row in enumerate(bar)]
    return add(bar, [[x*y for y in k] for x in residual]), residual


class Derivations(unittest.TestCase):
    def close(self, a, b):
        self.assertEqual(len(a), len(b))
        for ar, br in zip(a, b):
            self.assertEqual(len(ar), len(br))
            for x, y in zip(ar, br):
                self.assertAlmostEqual(x, y, places=11)

    def test_nilpotent_exact_and_truncated_residual(self):
        l = [[0., 0., 0.], [2., 0., 0.], [1., 3., 0.]]
        m, eye = add(identity(3), l), identity(3)
        full, power = approx_inverse(l, 3)
        self.close(mul(m, full), eye)
        self.close(power, [[0.]*3 for _ in range(3)])
        truncated, pn = approx_inverse(l, 1)
        self.close(add(eye, mul(m, truncated), -1), pn)

    def test_residual_correction_without_commuting_assumption(self):
        m = [[2., 1.], [0., 3.]]
        x = [[.4, -.1], [.1, .3]]
        r = add(identity(2), mul(m, x), -1)
        corrected = mul(x, add(identity(2), r))
        self.close(add(identity(2), mul(m, corrected), -1), mul(r, r))
        wrong = mul(add(identity(2), r), x)
        self.assertGreater(max(abs(a-b) for ar, br in zip(corrected, wrong)
                               for a, b in zip(ar, br)), .01)

    def test_zero_spectrum_does_not_mean_small_truncation(self):
        l = [[0., 0., 0.], [100., 0., 0.], [0., 100., 0.]]
        x, _ = approx_inverse(l, 2)
        r = add(identity(3), mul(add(identity(3), l), x), -1)
        self.assertEqual(r[2][0], 10000.)

    def test_deferred_materialization_preserves_residual(self):
        initial = [[.5, -.2], [.1, .7]]
        state = initial
        log, cumulative = [], 1.
        for alpha, beta, k, v in [(.5, .4, [.3, .8], [.1, .5]),
                                   (.8, .7, [.6, -.1], [.9, -.2]),
                                   (.3, .2, [.4, .4], [-.5, .3])]:
            state, u = gdn_step(state, k, v, alpha, beta)
            cumulative *= alpha
            log.append((cumulative, u, k))
            rebuilt = [[cumulative*x for x in row] for row in initial]
            for ai, ui, ki in log:
                rebuilt = add(rebuilt, [[cumulative/ai*x*y for y in ki] for x in ui])
            self.close(state, rebuilt)

    def test_amdahl_necessary_condition_and_extra_cost(self):
        s = 4.3
        threshold = (1.-1./1.1)/(1.-1./s)
        self.assertAlmostEqual(threshold, .118457300275482, places=10)
        gain = lambda p, c: 1./(1.-p+p/s+c)
        self.assertGreater(gain(.12, 0), 1.1)
        self.assertLess(gain(.12, .01), 1.1)


if __name__ == '__main__':
    unittest.main()

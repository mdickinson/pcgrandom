"""
Tests for the PCG_XSH_RR_V0 generator.
"""

import collections
import contextlib
import math
import unittest

from pcgrand.pcg_xsh_rr_v0 import PCG_XSH_RR_V0


# Sequences used for checking reproducibility regressions.
seq0_seed12345_die_rolls = [
    2, 5, 5, 4, 1, 6, 4, 4, 2, 5, 2, 6, 6, 2, 3, 1, 2, 6, 2, 6]
seq0_seed12345_uniforms = [
    float.fromhex('0x1.5086105e5480cp-2'),
    float.fromhex('0x1.90a33ce4414e0p-1'),
    float.fromhex('0x1.2be0bbe139574p-3'),
    float.fromhex('0x1.21bded2552e57p-1'),
    float.fromhex('0x1.0a20e3d9cff22p-2'),
    float.fromhex('0x1.5307c0ebb6114p-2'),
    float.fromhex('0x1.cdd6de4f8e4a2p-1'),
    float.fromhex('0x1.65d8359313d5ep-2'),
    float.fromhex('0x1.ea43f2f716334p-3'),
    float.fromhex('0x1.0be283f46182ap-2'),
]



@contextlib.contextmanager
def count_samples_generated(gen):
    """
    Keep track of number of samples produced by the given generator.
    """
    word_generator = gen._next_word

    def replacement_word_generator():
        replacement_word_generator.call_count += 1
        return word_generator()

    replacement_word_generator.call_count = 0

    # Shadow the class method with a local definition.
    gen._next_word = replacement_word_generator
    try:
        yield replacement_word_generator
    finally:
        del gen._next_word


class Test_PCG_XSH_RR_V0(unittest.TestCase):
    def test_creation_without_seed(self):
        gen1 = PCG_XSH_RR_V0()
        gen2 = PCG_XSH_RR_V0()

        sample1 = [gen1.random() for _ in range(10)]
        sample2 = [gen2.random() for _ in range(10)]

        # Possible in theory for these two samples to be identical; vanishingly
        # unlikely in practice.
        self.assertNotEqual(sample1, sample2)

    def test_reproducibility(self):
        gen = PCG_XSH_RR_V0(seed=12345, sequence=0)
        die_rolls = [gen.randint(1, 6) for _ in range(20)]
        self.assertEqual(
            die_rolls,
            seq0_seed12345_die_rolls,
        )

        # Assumes IEEE 754 binary64 floats. For other formats, we'd only expect
        # to get approximate equality here. If this ever actually breaks on
        # anyone's machine, please report to me and I'll fix it.
        gen = PCG_XSH_RR_V0(seed=12345, sequence=0)
        uniforms = [gen.random() for _ in range(10)]
        for actual, expected in zip(uniforms, seq0_seed12345_uniforms):
            self.assertEqual(actual, expected)

    def test_sequence_default(self):
        gen1 = PCG_XSH_RR_V0(seed=12345, sequence=0)
        gen2 = PCG_XSH_RR_V0(seed=12345)
        self.assertEqual(gen1.getstate(), gen2.getstate())

    def test_independent_sequences(self):
        # Crude statistical test for lack of correlation. If X and Y are
        # independent and uniform on [0, 1], then (X - 0.5) * (Y - 0.5) has
        # mean 0 and standard deviation 1/12. By the central limit theorem, we
        # expect the average V of N such independent values to be roughly
        # normally distributed with mean 0 and standard deviation 1 /
        # (12*sqrt(N)). So we expect |V| to be at most 1 / (4*sqrt(N)) with
        # over 99% probability.
        gen1 = PCG_XSH_RR_V0(seed=12345, sequence=0)
        gen2 = PCG_XSH_RR_V0(seed=12345, sequence=1)
        N = 10000
        xs = [gen1.random() for _ in range(N)]
        ys = [gen2.random() for _ in range(N)]
        v = sum((x - 0.5) * (y - 0.5) for x, y in zip(xs, ys)) / N
        # Check we're within 3 standard deviations of the mean.
        self.assertLess(abs(v), 0.25/math.sqrt(N))

    def test_no_shared_state(self):
        # Get samples first from gen1, then from gen2.
        gen1 = PCG_XSH_RR_V0(seed=12345, sequence=0)
        gen2 = PCG_XSH_RR_V0(seed=12345, sequence=1)
        sample1_1 = [gen1.random() for _ in range(10)]
        sample2_1 = [gen2.random() for _ in range(10)]

        # Now in the opposite order: from gen2, then from gen1.
        gen1 = PCG_XSH_RR_V0(seed=12345, sequence=0)
        gen2 = PCG_XSH_RR_V0(seed=12345, sequence=1)
        sample2_2 = [gen2.random() for _ in range(10)]
        sample1_2 = [gen1.random() for _ in range(10)]

        # Now interleaved.
        gen1 = PCG_XSH_RR_V0(seed=12345, sequence=0)
        gen2 = PCG_XSH_RR_V0(seed=12345, sequence=1)
        sample1_3 = []
        sample2_3 = []
        for _ in range(10):
            sample1_3.append(gen1.random())
            sample2_3.append(gen2.random())

        # Results should be the same in all cases.
        self.assertEqual(sample1_1, sample1_2)
        self.assertEqual(sample1_1, sample1_3)
        self.assertEqual(sample2_1, sample2_2)
        self.assertEqual(sample2_1, sample2_3)

    def test_save_and_restore_state(self):
        gen = PCG_XSH_RR_V0(seed=15206, sequence=27)

        # Generate some values.
        samples1 = [gen.random() for _ in range(10)]

        # Save the state, generate some more.
        state = gen.getstate()
        samples2 = [gen.random() for _ in range(10)]

        # Restore the state, check we get the same samples.
        gen.setstate(state)
        samples3 = [gen.random() for _ in range(10)]
        self.assertEqual(samples2, samples3)

    def test_restore_state_from_different_generator(self):
        gen = PCG_XSH_RR_V0(seed=15206, sequence=27)
        state = gen.getstate()

        bad_version = 'pcgrand.PCG_XSH_RR_V1'
        bad_state = (bad_version,) + state[1:]
        with self.assertRaises(ValueError):
            gen.setstate(bad_state)

    def test_state_preserves_gauss(self):
        gen = PCG_XSH_RR_V0(seed=15206, sequence=27)

        # Test a state with gauss_next = None
        state = gen.getstate()
        samples1 = [gen.gauss(0.0, 1.0) for _ in range(5)]
        gen.setstate(state)
        samples2 = [gen.gauss(0.0, 1.0) for _ in range(5)]
        self.assertEqual(samples1, samples2)

        # ... and a state with gauss_next non-None.
        state = gen.getstate()
        samples1 = [gen.gauss(0.0, 1.0) for _ in range(5)]
        gen.setstate(state)
        samples2 = [gen.gauss(0.0, 1.0) for _ in range(5)]
        self.assertEqual(samples1, samples2)

    def test_getrandbits(self):
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)

        N = 10000
        k = 5
        samples = [gen.getrandbits(k) for _ in range(10000)]
        self.assertLess(max(samples), 2**k)
        self.assertGreaterEqual(min(samples), 0)

        # Perform a chi-squared test for uniformity.
        # pp = scipy.stats.chi2(31).ppf(0.99)
        pp = 52.191394833191922
        counts = collections.Counter(samples)
        expected = float(N) / 2**k
        cs = sum(
            (counts[i] - expected)**2 / expected
            for i in range(2**k)
        )
        # 1% chance of test failure.
        self.assertLess(cs, pp)

    def test_getrandbits_large(self):
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)

        k = 379
        samples = [gen.getrandbits(k) for _ in range(1000)]

        self.assertGreaterEqual(min(samples), 0)
        self.assertLess(max(samples), 2**379)
        # It's possible, but vanishingly unlikely, that all values
        # are less than 2**378.
        self.assertGreaterEqual(max(samples), 2**378)

    def test_getrandbits_zero_bits(self):
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)
        result = gen.getrandbits(0)
        self.assertEqual(result, 0)

    def test_getrandbits_negative_bits(self):
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)
        with self.assertRaises(ValueError):
            gen.getrandbits(-1)

    def test_randrange_uniform(self):
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)

        # Indirect test of our _randbelow override.
        trials = 10000
        n = 13
        # pp = scipy.stats.chi2(n-1).ppf(0.99)
        pp = 26.216967305535849

        samples = [gen.randrange(13) for _ in range(trials)]

        counts = collections.Counter(samples)
        expected = trials / n
        cs = sum(
            (counts[i] - expected)**2 / expected
            for i in range(n)
        )

        # Should fail <1% of the time, on average.
        self.assertLess(cs, pp)

    def test_randrange_one(self):
        # Corner case.
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)
        state_before = gen.getstate()

        samples = [gen.randrange(1) for _ in range(10)]
        self.assertEqual(samples, [0]*10)

        state_after = gen.getstate()
        self.assertEqual(state_before, state_after)

    def test_randrange_of_wordsize(self):
        # Using randrange(2**32) should consume exactly one
        # sample each time.
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)

        with count_samples_generated(gen) as wordgen:
            for index in range(10000):
                self.assertEqual(wordgen.call_count, index)
                gen.randrange(2**32)
                self.assertEqual(wordgen.call_count, index+1)

    def test_count_samples_generated(self):
        # This is really a test for our count_samples_generated helper
        # rather than for the PRNG.
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)

        samples = [gen.randrange(13) for _ in range(14)]
        with count_samples_generated(gen) as wordgen:
            samples = [gen.randrange(27) for _ in range(21)]
            self.assertEqual(wordgen.call_count, 21)
            samples = [gen.random() for _ in range(10)]
            self.assertEqual(wordgen.call_count, 41)

        samples = [gen.randrange(27) for _ in range(13)]
        self.assertEqual(wordgen.call_count, 41)

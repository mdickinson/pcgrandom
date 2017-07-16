"""
Tests for the PCG_XSH_RR_V0 generator.
"""
from __future__ import division

import collections
import contextlib
import itertools
import math
import unittest

from pcgrandom.pcg_xsh_rr_v0 import PCG_XSH_RR_V0


# Sequences used for detecting reproducibility regressions.
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
seq0_seed12345_choices = [
    'HT', 'D2', 'CK', 'DJ', 'S7', 'C8', 'DJ', 'DT',
    'HA', 'D4', 'HT', 'CT', 'C7',
]
seq0_seed12345_sample = [
    'HT', 'C3', 'C8', 'DA', 'CA', 'D6', 'C6', 'H9',
    'SK', 'H8', 'HJ', 'H2', 'H6',
]


# 99% values of the chi-squared statistic used in various
# tests below, indexed by degrees of freedom. Values
# calculated using scipy.stats.chi2(dof).ppf(0.99)
chisq_99percentile = {
    3: 11.344866730144371,
    12: 26.21696730553585,
    23: 41.63839811885848,
    31: 52.19139483319192,
}


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

        gen = PCG_XSH_RR_V0(seed=12345, sequence=0)
        suits = 'SHDC'
        values = 'AKQJT98765432'
        cards = [suit+value for suit in suits for value in values]

        # Selection with repetition.
        choices = [gen.choice(cards) for _ in range(13)]
        self.assertEqual(choices, seq0_seed12345_choices)

        # Sampling
        sample = gen.sample(cards, 13)
        self.assertEqual(sample, seq0_seed12345_sample)

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
        [gen.random() for _ in range(10)]

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

        bad_version = 'pcgrandom.PCG_XSH_RR_V1'
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

        k = 5
        samples = [gen.getrandbits(k) for _ in range(10000)]
        self.check_uniformity(range(2**k), samples)

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
        n = 13
        samples = [gen.randrange(n) for _ in range(10000)]
        self.check_uniformity(range(n), samples)

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

    def test_jumpahead(self):
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)
        # Generate samples, each sample consuming exactly one word
        # from the core generator.
        samples = [gen.randrange(2**32) for _ in range(1000)]

        # Rewind, check we can produce the exact same samples.
        gen.jumpahead(-1000)
        same_again = [gen.randrange(2**32) for _ in range(1000)]
        self.assertEqual(samples, same_again)

        # Corner case: jumpahead(0) should work.
        state_before = gen.getstate()
        gen.jumpahead(0)
        state_after = gen.getstate()
        self.assertEqual(state_before, state_after)

        # Now jump around randomly within the collection of samples. Use a
        # separate generator for the positions to jump to.
        posgen = PCG_XSH_RR_V0(seed=19733, sequence=22)

        current_pos = 1000
        for _ in range(100):
            next_pos = posgen.randrange(1000)
            gen.jumpahead(next_pos - current_pos)
            sample = gen.randrange(2**32)
            self.assertEqual(sample, samples[next_pos])
            current_pos = next_pos + 1

    def test_randrange_float_arguments(self):
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)

        with self.assertRaises(TypeError):
            gen.randrange(5.0)
        with self.assertRaises(TypeError):
            gen.randrange(2.0, 7)
        with self.assertRaises(TypeError):
            gen.randrange(2, 7.0)
        with self.assertRaises(TypeError):
            gen.randrange(2, 7, 1.0)
        with self.assertRaises(TypeError):
            gen.randrange(2, 7, 2.0)

    def test_randrange_start_only(self):
        # See http://bugs.python.org/issue9379 for related discussion.
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)
        samples = [gen.randrange(23) for _ in range(1000)]
        # Chance of getting only 22 of the possible 23 outcomes is < 1.2e-18.
        self.assertEqual(set(samples), set(range(23)))

        with self.assertRaises(ValueError):
            gen.randrange(0)
        with self.assertRaises(ValueError):
            gen.randrange(-5)

    def test_randrange_start_and_stop(self):
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)
        samples = [gen.randrange(-10, 13) for _ in range(1000)]
        self.assertEqual(set(samples), set(range(-10, 13)))

        with self.assertRaises(ValueError):
            gen.randrange(20, 20)
        with self.assertRaises(ValueError):
            gen.randrange(21, 20)

    def test_randrange_start_stop_and_step(self):
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)

        test_ranges = [
            (16, 37, 5),
            (5, 35, 5),
            (4, 35, 5),
            (35, 5, -5),
            (36, 5, -5),
        ]

        for test_range in test_ranges:
            samples = [gen.randrange(*test_range) for _ in range(1000)]
            self.assertEqual(set(samples), set(range(*test_range)))

        with self.assertRaises(ValueError):
            gen.randrange(0, 20, 0)
        with self.assertRaises(ValueError):
            gen.randrange(0, -20, 0)
        with self.assertRaises(ValueError):
            gen.randrange(0, 5, -1)
        with self.assertRaises(ValueError):
            gen.randrange(0, -5, 1)
        with self.assertRaises(ValueError):
            gen.randrange(22, 22, -1)
        with self.assertRaises(ValueError):
            gen.randrange(47, 47, 1)

    def test_choice(self):
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)

        with self.assertRaises(IndexError):
            gen.choice([])

        nsamples = 1000
        seq = "ABCD"
        choices = [
            gen.choice(seq) for _ in range(nsamples)
        ]
        self.check_uniformity(seq, choices)

    def test_sample(self):
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)

        samples = [tuple(gen.sample(range(4), 3)) for _ in range(10000)]
        population = list(itertools.permutations(range(4), 3))
        self.check_uniformity(population, samples)

    def test_sample_set(self):
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)

        s = set('ABCDEFG')
        sample = gen.sample(s, 3)
        self.assertLess(set(sample), s)

    def test_sample_dict(self):
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)

        d = dict(a=1, b=2, c=3)
        with self.assertRaises(TypeError):
            gen.sample(d, 2)

    def test_sample_corner_cases(self):
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)
        self.assertEqual(gen.sample([], 0), [])
        with self.assertRaises(ValueError):
            self.assertEqual(gen.sample([], 1))
        with self.assertRaises(ValueError):
            self.assertEqual(gen.sample([], -1))

    def test_shuffle(self):
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)
        population = list(range(13))

        result = gen.shuffle(population)
        self.assertIsNone(result)
        self.assertNotEqual(population, list(range(13)))
        self.assertEqual(set(population), set(range(13)))

        population = list(range(4))

        samples = []
        for _ in range(10000):
            gen.shuffle(population)
            samples.append(tuple(population))

        self.check_uniformity(
            list(itertools.permutations(range(4))),
            samples,
        )

    def test_shuffle_corner_cases(self):
        # shuffling a length 0 or 1 sequence shouldn't be a problem
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)
        population = []
        gen.shuffle(population)
        self.assertEqual(population, [])

        population = [13]
        gen.shuffle(population)
        self.assertEqual(population, [13])

    def test_count_samples_generated(self):
        # This is really a test for our count_samples_generated helper
        # rather than for the PRNG.
        gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)

        [gen.randrange(13) for _ in range(14)]
        with count_samples_generated(gen) as wordgen:
            [gen.randrange(27) for _ in range(21)]
            self.assertEqual(wordgen.call_count, 21)
            [gen.random() for _ in range(10)]
            self.assertEqual(wordgen.call_count, 41)

        [gen.randrange(27) for _ in range(13)]
        self.assertEqual(wordgen.call_count, 41)

    def check_uniformity(self, population, sample):
        """
        Check uniformity via a chi-squared test with p-value 0.99.

        Requires that there's an entry for len(population) - 1
        in the chisq_99percentile dictionary.
        """
        counts = collections.Counter(sample)
        expected = len(sample) / len(population)
        stat = sum(
            (counts[i] - expected)**2 / expected
            for i in population
        )
        self.assertLess(stat, chisq_99percentile[len(population) - 1])

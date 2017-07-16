"""
Tests for the PCG_XSL_RR_V0 generator.
"""
from __future__ import division

import collections
import contextlib
import itertools
import math
import unittest

from pcgrandom.pcg_xsl_rr_v0 import PCG_XSL_RR_V0


# Sequences used for detecting reproducibility regressions.
seq0_seed12345_die_rolls = [
    1, 2, 4, 4, 1, 4, 2, 2, 6, 1, 6, 2, 4, 6, 6, 5, 1, 1, 2, 6]
seq0_seed12345_uniforms = [
    float.fromhex('0x1.36feb111851b8p-3'),
    float.fromhex('0x1.d0eab4d2dacd0p-3'),
    float.fromhex('0x1.3153584d8fc39p-1'),
    float.fromhex('0x1.2839f1285a962p-1'),
    float.fromhex('0x1.dd8596e786ab0p-5'),
    float.fromhex('0x1.295b84d5041f7p-1'),
    float.fromhex('0x1.86227587a6c34p-3'),
    float.fromhex('0x1.5ac08820e8fc8p-3'),
    float.fromhex('0x1.bbdbd5409790bp-1'),
    float.fromhex('0x1.1b964efcf0d0cp-3'),
]
seq0_seed12345_choices = [
    'S7', 'S3', 'D9', 'DT', 'SJ', 'DT', 'S5', 'S6',
    'C8', 'S7', 'C9', 'HK', 'DQ'
]
seq0_seed12345_sample = [
    'C8', 'S5', 'D6', 'DK', 'CK', 'S9', 'C2', 'HJ',
    'SK', 'S7', 'D2', 'C6', 'C5',
]
seq0_seed12345_shuffle = [
    19, 1, 9, 5, 18, 2, 15, 8, 6, 3,
    4, 0, 14, 10, 12, 11, 13, 16, 17, 7,
]


# 99% values of the chi-squared statistic used in various
# tests below, indexed by degrees of freedom. Values
# calculated using scipy.stats.chi2(dof).ppf(0.99)
chisq_99percentile = {
    3: 11.344866730144371,
    4: 13.276704135987622,
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


class Test_PCG_XSL_RR_V0(unittest.TestCase):
    def test_creation_without_seed(self):
        gen1 = PCG_XSL_RR_V0()
        gen2 = PCG_XSL_RR_V0()

        sample1 = [gen1.random() for _ in range(10)]
        sample2 = [gen2.random() for _ in range(10)]

        # Possible in theory for these two samples to be identical; vanishingly
        # unlikely in practice.
        self.assertNotEqual(sample1, sample2)

    def test_seed_resets_gauss_state(self):
        gen = PCG_XSL_RR_V0()

        gen.seed(2143)
        x1 = gen.random()
        y1 = gen.gauss(0.0, 1.0)

        gen.seed(2143)
        x2 = gen.random()
        y2 = gen.gauss(0.0, 1.0)

        self.assertEqual(x1, x2)
        self.assertEqual(y1, y2)

    def test_reproducibility(self):
        gen = PCG_XSL_RR_V0(seed=12345, sequence=0)
        die_rolls = [gen.randint(1, 6) for _ in range(20)]
        self.assertEqual(
            die_rolls,
            seq0_seed12345_die_rolls,
        )

        # Assumes IEEE 754 binary64 floats. For other formats, we'd only expect
        # to get approximate equality here. If this ever actually breaks on
        # anyone's machine, please report to me and I'll fix it.
        gen = PCG_XSL_RR_V0(seed=12345, sequence=0)
        uniforms = [gen.random() for _ in range(10)]
        self.assertEqual(uniforms, seq0_seed12345_uniforms)

        gen = PCG_XSL_RR_V0(seed=12345, sequence=0)
        suits = 'SHDC'
        values = 'AKQJT98765432'
        cards = [suit+value for suit in suits for value in values]

        # Selection with repetition.
        choices = [gen.choice(cards) for _ in range(13)]
        self.assertEqual(choices, seq0_seed12345_choices)

        # Sampling
        sample = gen.sample(cards, 13)
        self.assertEqual(sample, seq0_seed12345_sample)

        # Shuffling
        population = list(range(20))
        gen.shuffle(population)
        self.assertEqual(population, seq0_seed12345_shuffle)

    def test_sequence_default(self):
        gen1 = PCG_XSL_RR_V0(seed=12345, sequence=0)
        gen2 = PCG_XSL_RR_V0(seed=12345)
        self.assertEqual(gen1.getstate(), gen2.getstate())

    def test_independent_sequences(self):
        # Crude statistical test for lack of correlation. If X and Y are
        # independent and uniform on [0, 1], then (X - 0.5) * (Y - 0.5) has
        # mean 0 and standard deviation 1/12. By the central limit theorem, we
        # expect the average V of N such independent values to be roughly
        # normally distributed with mean 0 and standard deviation 1 /
        # (12*sqrt(N)). So we expect |V| to be at most 1 / (4*sqrt(N)) with
        # over 99% probability.
        gen1 = PCG_XSL_RR_V0(seed=12345, sequence=0)
        gen2 = PCG_XSL_RR_V0(seed=12345, sequence=1)
        N = 10000
        xs = [gen1.random() for _ in range(N)]
        ys = [gen2.random() for _ in range(N)]
        v = sum((x - 0.5) * (y - 0.5) for x, y in zip(xs, ys)) / N
        # Check we're within 3 standard deviations of the mean.
        self.assertLess(abs(v), 0.25/math.sqrt(N))

    def test_no_shared_state(self):
        # Get samples first from gen1, then from gen2.
        gen1 = PCG_XSL_RR_V0(seed=12345, sequence=0)
        gen2 = PCG_XSL_RR_V0(seed=12345, sequence=1)
        sample1_1 = [gen1.random() for _ in range(10)]
        sample2_1 = [gen2.random() for _ in range(10)]

        # Now in the opposite order: from gen2, then from gen1.
        gen1 = PCG_XSL_RR_V0(seed=12345, sequence=0)
        gen2 = PCG_XSL_RR_V0(seed=12345, sequence=1)
        sample2_2 = [gen2.random() for _ in range(10)]
        sample1_2 = [gen1.random() for _ in range(10)]

        # Now interleaved.
        gen1 = PCG_XSL_RR_V0(seed=12345, sequence=0)
        gen2 = PCG_XSL_RR_V0(seed=12345, sequence=1)
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
        gen = PCG_XSL_RR_V0(seed=15206, sequence=27)

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
        gen = PCG_XSL_RR_V0(seed=15206, sequence=27)
        state = gen.getstate()

        bad_version = 'pcgrandom.PCG_XSL_RR_V1'
        bad_state = (bad_version,) + state[1:]
        with self.assertRaises(ValueError):
            gen.setstate(bad_state)

    def test_state_preserves_gauss(self):
        gen = PCG_XSL_RR_V0(seed=15206, sequence=27)

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
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)

        k = 5
        samples = [gen.getrandbits(k) for _ in range(10000)]
        self.check_uniform(range(2**k), samples)

    def test_getrandbits_large(self):
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)

        k = 379
        samples = [gen.getrandbits(k) for _ in range(1000)]

        self.assertGreaterEqual(min(samples), 0)
        self.assertLess(max(samples), 2**379)
        # It's possible, but vanishingly unlikely, that all values
        # are less than 2**378.
        self.assertGreaterEqual(max(samples), 2**378)

    def test_getrandbits_zero_bits(self):
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)
        result = gen.getrandbits(0)
        self.assertEqual(result, 0)

    def test_getrandbits_negative_bits(self):
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)
        with self.assertRaises(ValueError):
            gen.getrandbits(-1)

    def test_randrange_uniform(self):
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)

        # Indirect test of our _randbelow override.
        n = 13
        samples = [gen.randrange(n) for _ in range(10000)]
        self.check_uniform(range(n), samples)

    def test_randrange_one(self):
        # Corner case.
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)
        state_before = gen.getstate()

        samples = [gen.randrange(1) for _ in range(10)]
        self.assertEqual(samples, [0]*10)

        state_after = gen.getstate()
        self.assertEqual(state_before, state_after)

    def test_randrange_of_wordsize(self):
        # Using randrange(2**64) should consume exactly one
        # sample each time.
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)

        with count_samples_generated(gen) as wordgen:
            for index in range(10000):
                self.assertEqual(wordgen.call_count, index)
                gen.randrange(2**64)
                self.assertEqual(wordgen.call_count, index+1)

    def test_jumpahead(self):
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)
        # Generate samples, each sample consuming exactly one word
        # from the core generator.
        samples = [gen.randrange(2**64) for _ in range(1000)]

        # Rewind, check we can produce the exact same samples.
        gen.jumpahead(-1000)
        same_again = [gen.randrange(2**64) for _ in range(1000)]
        self.assertEqual(samples, same_again)

        # Corner case: jumpahead(0) should work.
        state_before = gen.getstate()
        gen.jumpahead(0)
        state_after = gen.getstate()
        self.assertEqual(state_before, state_after)

        # Now jump around randomly within the collection of samples. Use a
        # separate generator for the positions to jump to.
        posgen = PCG_XSL_RR_V0(seed=19733, sequence=22)

        current_pos = 1000
        for _ in range(100):
            next_pos = posgen.randrange(1000)
            gen.jumpahead(next_pos - current_pos)
            sample = gen.randrange(2**64)
            self.assertEqual(sample, samples[next_pos])
            current_pos = next_pos + 1

    def test_randrange_float_arguments(self):
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)

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
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)
        samples = [gen.randrange(23) for _ in range(1000)]
        # Chance of getting only 22 of the possible 23 outcomes is < 1.2e-18.
        self.assertEqual(set(samples), set(range(23)))

        with self.assertRaises(ValueError):
            gen.randrange(0)
        with self.assertRaises(ValueError):
            gen.randrange(-5)

    def test_randrange_start_and_stop(self):
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)
        samples = [gen.randrange(-10, 13) for _ in range(1000)]
        self.assertEqual(set(samples), set(range(-10, 13)))

        with self.assertRaises(ValueError):
            gen.randrange(20, 20)
        with self.assertRaises(ValueError):
            gen.randrange(21, 20)

    def test_randrange_start_stop_and_step(self):
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)

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
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)

        with self.assertRaises(IndexError):
            gen.choice([])

        nsamples = 1000
        seq = "ABCD"
        choices = [
            gen.choice(seq) for _ in range(nsamples)
        ]
        self.check_uniform(seq, choices)

    def test_sample(self):
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)

        samples = [tuple(gen.sample(range(4), 3)) for _ in range(10000)]
        population = list(itertools.permutations(range(4), 3))
        self.check_uniform(population, samples)

    def test_sample_set(self):
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)

        s = set('ABCDEFG')
        sample = gen.sample(s, 3)
        self.assertLess(set(sample), s)

    def test_sample_dict(self):
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)

        d = dict(a=1, b=2, c=3)
        with self.assertRaises(TypeError):
            gen.sample(d, 2)

    def test_sample_corner_cases(self):
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)
        self.assertEqual(gen.sample([], 0), [])
        with self.assertRaises(ValueError):
            self.assertEqual(gen.sample([], 1))
        with self.assertRaises(ValueError):
            self.assertEqual(gen.sample([], -1))

    def test_shuffle(self):
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)
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

        self.check_uniform(
            list(itertools.permutations(range(4))),
            samples,
        )

    def test_shuffle_corner_cases(self):
        # shuffling a length 0 or 1 sequence shouldn't be a problem
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)
        population = []
        gen.shuffle(population)
        self.assertEqual(population, [])

        population = [13]
        gen.shuffle(population)
        self.assertEqual(population, [13])

    def test_choices(self):
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)

        population = list(range(5))

        sample = gen.choices(population, k=10000)
        self.check_uniform(population, sample)

        weights = [2, 3, 0, 1, 4]
        sample = gen.choices(population, weights=weights, k=10000)
        self.check_goodness_of_fit(dict(zip(population, weights)), sample)

        cum_weights = [2, 5, 5, 6, 10]
        sample = gen.choices(population, cum_weights=cum_weights, k=10000)
        self.check_goodness_of_fit(dict(zip(population, weights)), sample)

    def test_choices_subnormal_weights(self):
        # Corner case where random.Random triggers an IndexError.
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)

        population = list(range(5))
        weights = [1e-323, 0.0, 2e-323, 2e-323, 1e-323]
        sample = gen.choices(population, weights=weights, k=10000)
        self.check_goodness_of_fit(dict(zip(population, weights)), sample)

        population = list(range(6))
        weights = [1e-323, 0.0, 2e-323, 2e-323, 1e-323, 0.0]
        sample = gen.choices(population, weights=weights, k=10000)
        self.check_goodness_of_fit(dict(zip(population, weights)), sample)

    def test_choices_error_conditions(self):
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)

        # Can't specify both weights and cum_weights.
        with self.assertRaises(TypeError):
            gen.choices(range(3), weights=[1, 2, 3], cum_weights=[1, 3, 6])

        # Two errors here: empty population, and both weights and cum_weights
        # specified. The TypeError for the bad signature should win.
        with self.assertRaises(TypeError):
            gen.choices([], weights=[1, 2, 3], cum_weights=[1, 3, 6])

        # Empty population: IndexError to match random.choice. We should get an
        # exception even in the corner case that zero samples are requested.
        with self.assertRaises(IndexError):
            gen.choices([], weights=[])
        with self.assertRaises(IndexError):
            gen.choices([], cum_weights=[])
        with self.assertRaises(IndexError):
            gen.choices([])
        with self.assertRaises(IndexError):
            gen.choices([], weights=[], k=0)
        with self.assertRaises(IndexError):
            gen.choices([], cum_weights=[], k=0)
        with self.assertRaises(IndexError):
            gen.choices([], k=0)

        # Number of weights doesn't match population.
        with self.assertRaises(ValueError):
            gen.choices(range(3), weights=[1, 2])
        with self.assertRaises(ValueError):
            gen.choices(range(3), cum_weights=[1, 2])

        # Total weight is zero.
        with self.assertRaises(ValueError):
            gen.choices(range(3), weights=[0.0, 0.0, 0.0])
        with self.assertRaises(ValueError):
            gen.choices(range(3), cum_weights=[0.0, 0.0, 0.0])

    def test_count_samples_generated(self):
        # This is really a test for our count_samples_generated helper
        # rather than for the PRNG.
        gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)

        [gen.randrange(13) for _ in range(14)]
        with count_samples_generated(gen) as wordgen:
            [gen.randrange(27) for _ in range(21)]
            self.assertEqual(wordgen.call_count, 21)
            [gen.random() for _ in range(10)]
            self.assertEqual(wordgen.call_count, 31)

        [gen.randrange(27) for _ in range(13)]
        self.assertEqual(wordgen.call_count, 31)

    def check_uniform(self, population, sample):
        """
        Check uniformity via a chi-squared test with p-value 0.99.

        Requires that there's an entry for len(population) - 1
        in the chisq_99percentile dictionary.

        Parameters
        ----------
        population : sequence
            The population that the samples are drawn from.
        sample : sequence
            The generated sample.
        """
        weights = {i: 1 for i in population}
        self.check_goodness_of_fit(weights, sample)

    def check_goodness_of_fit(self, weights, sample):
        """
        Perform a chi-squared goodness of fit test.

        Requires that there's an entry for len(expected) - 1
        in the chisq_99percentile dictionary.

        sample : the sample to be tested
        weights : mapping from members of the population to their
            expected weights. The weights need not be normalised.
        """
        counts = collections.Counter(sample)
        # Expected frequencies for this sample.
        total = sum(weights.values())
        expected = {
            i: w / total * len(sample) for i, w in weights.items() if w}

        # Check that we don't have any extraneous objects in our sample.  This
        # also acts as a check that elements with zero weight haven't been
        # generated.
        self.assertLessEqual(set(counts), set(expected))

        stat = sum(
            (counts[i] - expected[i])**2 / expected[i]
            for i in expected
        )
        self.assertLess(stat, chisq_99percentile[len(expected)-1])

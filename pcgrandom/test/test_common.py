"""
Tests common to all generators.
"""

import collections
import itertools
import math

# 99% values of the chi-squared statistic used in the goodness-of-fit tests
# below, indexed by degrees of freedom. Values calculated using
# scipy.stats.chi2(dof).ppf(0.99)
chisq_99percentile = {
    3: 11.344866730144371,
    4: 13.276704135987622,
    12: 26.21696730553585,
    23: 41.63839811885848,
    31: 52.19139483319192,
}


class TestCommon(object):
    def test_getrandbits(self):
        k = 5
        samples = [self.gen.getrandbits(k) for _ in range(10000)]
        self.check_uniform(range(2**k), samples)

    def test_getrandbits_large(self):
        k = 101
        nsamples = 10000
        samples = [self.gen.getrandbits(k) for _ in range(nsamples)]

        # Count number of times individual bits have appeared.
        counts = {}
        for bitpos in range(k):
            bit = 2**bitpos
            counts[bitpos] = sum(1 for sample in samples if (sample & bit))

        # Assuming that each bit is "fair", each count roughly follows a normal
        # distribution with mean 0.5*nsamples and standard deviation
        # 0.5*sqrt(nsamples). We'll call a count bad if it's more than 3
        # standard deviations from the mean.

        bad_counts = 0
        for count in counts.values():
            if abs(counts[0] - 0.5*nsamples) > 1.5*math.sqrt(nsamples):
                bad_counts += 1

        # There's about a 1 in 370 chance of any one count being bad,
        # and the counts should be independent. To be safe, we allow
        # up to three bad counts before failing.
        self.assertLessEqual(bad_counts, 3)

    def test_getrandbits_zero_bits(self):
        # getrandbits(0) is a valid operation (unlike the random.Random
        # version), but since it doesn't need any randomness it shouldn't
        # advance the state.
        state = self.gen.getstate()
        for _ in range(10):
            result = self.gen.getrandbits(0)
            self.assertEqual(result, 0)
        self.assertEqual(self.gen.getstate(), state)

    def test_getrandbits_negative_bits(self):
        with self.assertRaises(ValueError):
            self.gen.getrandbits(-1)

    def test_randrange_uniform(self):
        n = 13
        samples = [self.gen.randrange(n) for _ in range(10000)]
        self.check_uniform(range(n), samples)

    def test_randrange_one_doesnt_advance_state(self):
        # randrange(1) should work, but doesn't need any random
        # input, so shouldn't end up advancing the state.
        state_before = self.gen.getstate()

        samples = [self.gen.randrange(1) for _ in range(10)]
        self.assertEqual(samples, [0]*10)

        state_after = self.gen.getstate()
        self.assertEqual(state_before, state_after)

    def test_randrange_float_arguments(self):
        with self.assertRaises(TypeError):
            self.gen.randrange(5.0)
        with self.assertRaises(TypeError):
            self.gen.randrange(2.0, 7)
        with self.assertRaises(TypeError):
            self.gen.randrange(2, 7.0)
        with self.assertRaises(TypeError):
            self.gen.randrange(2, 7, 1.0)
        with self.assertRaises(TypeError):
            self.gen.randrange(2, 7, 2.0)

    def test_randrange_start_only(self):
        # See http://bugs.python.org/issue9379 for related discussion.
        samples = [self.gen.randrange(23) for _ in range(1000)]
        # Chance of getting only 22 of the possible 23 outcomes is < 1.2e-18.
        self.assertEqual(set(samples), set(range(23)))

        with self.assertRaises(ValueError):
            self.gen.randrange(0)
        with self.assertRaises(ValueError):
            self.gen.randrange(-5)

    def test_randrange_start_and_stop(self):
        samples = [self.gen.randrange(-10, 13) for _ in range(1000)]
        self.assertEqual(set(samples), set(range(-10, 13)))

        with self.assertRaises(ValueError):
            self.gen.randrange(20, 20)
        with self.assertRaises(ValueError):
            self.gen.randrange(21, 20)

    def test_randrange_start_stop_and_step(self):
        test_ranges = [
            (16, 37, 5),
            (5, 35, 5),
            (4, 35, 5),
            (35, 5, -5),
            (36, 5, -5),
        ]

        for test_range in test_ranges:
            samples = [self.gen.randrange(*test_range) for _ in range(1000)]
            self.assertEqual(set(samples), set(range(*test_range)))

        with self.assertRaises(ValueError):
            self.gen.randrange(0, 20, 0)
        with self.assertRaises(ValueError):
            self.gen.randrange(0, -20, 0)
        with self.assertRaises(ValueError):
            self.gen.randrange(0, 5, -1)
        with self.assertRaises(ValueError):
            self.gen.randrange(0, -5, 1)
        with self.assertRaises(ValueError):
            self.gen.randrange(22, 22, -1)
        with self.assertRaises(ValueError):
            self.gen.randrange(47, 47, 1)

    def test_choice(self):
        with self.assertRaises(IndexError):
            self.gen.choice([])

        nsamples = 1000
        seq = "ABCD"
        choices = [
            self.gen.choice(seq) for _ in range(nsamples)
        ]
        self.check_uniform(seq, choices)

    def test_sample(self):
        samples = [tuple(self.gen.sample(range(4), 3)) for _ in range(10000)]
        population = list(itertools.permutations(range(4), 3))
        self.check_uniform(population, samples)

    def test_sample_set(self):
        s = set('ABCDEFG')
        sample = self.gen.sample(s, 3)
        self.assertLess(set(sample), s)

    def test_sample_dict(self):
        d = dict(a=1, b=2, c=3)
        with self.assertRaises(TypeError):
            self.gen.sample(d, 2)

    def test_sample_corner_cases(self):
        self.assertEqual(self.gen.sample([], 0), [])
        with self.assertRaises(ValueError):
            self.assertEqual(self.gen.sample([], 1))
        with self.assertRaises(ValueError):
            self.assertEqual(self.gen.sample([], -1))

    def test_shuffle(self):
        population = list(range(13))

        result = self.gen.shuffle(population)
        self.assertIsNone(result)
        self.assertNotEqual(population, list(range(13)))
        self.assertEqual(set(population), set(range(13)))

        population = list(range(4))

        samples = []
        for _ in range(10000):
            self.gen.shuffle(population)
            samples.append(tuple(population))

        self.check_uniform(
            list(itertools.permutations(range(4))),
            samples,
        )

    def test_shuffle_corner_cases(self):
        # shuffling a length 0 or 1 sequence shouldn't be a problem
        population = []
        self.gen.shuffle(population)
        self.assertEqual(population, [])

        population = [13]
        self.gen.shuffle(population)
        self.assertEqual(population, [13])

    def test_choices(self):
        population = list(range(5))

        sample = self.gen.choices(population, k=10000)
        self.check_uniform(population, sample)

        weights = [2, 3, 0, 1, 4]
        sample = self.gen.choices(population, weights=weights, k=10000)
        self.check_goodness_of_fit(dict(zip(population, weights)), sample)

        cum_weights = [2, 5, 5, 6, 10]
        sample = self.gen.choices(population, cum_weights=cum_weights, k=10000)
        self.check_goodness_of_fit(dict(zip(population, weights)), sample)

    def test_choices_subnormal_weights(self):
        # Corner case where random.Random triggers an IndexError.
        population = list(range(5))
        weights = [1e-323, 0.0, 2e-323, 2e-323, 1e-323]
        sample = self.gen.choices(population, weights=weights, k=10000)
        self.check_goodness_of_fit(dict(zip(population, weights)), sample)

        population = list(range(6))
        weights = [1e-323, 0.0, 2e-323, 2e-323, 1e-323, 0.0]
        sample = self.gen.choices(population, weights=weights, k=10000)
        self.check_goodness_of_fit(dict(zip(population, weights)), sample)

    def test_choices_error_conditions(self):
        # Can't specify both weights and cum_weights.
        with self.assertRaises(TypeError):
            self.gen.choices(
                range(3), weights=[1, 2, 3], cum_weights=[1, 3, 6])

        # Two errors here: empty population, and both weights and cum_weights
        # specified. The TypeError for the bad signature should win.
        with self.assertRaises(TypeError):
            self.gen.choices([], weights=[1, 2, 3], cum_weights=[1, 3, 6])

        # Empty population: IndexError to match random.choice. We should get an
        # exception even in the corner case that zero samples are requested.
        with self.assertRaises(IndexError):
            self.gen.choices([], weights=[])
        with self.assertRaises(IndexError):
            self.gen.choices([], cum_weights=[])
        with self.assertRaises(IndexError):
            self.gen.choices([])
        with self.assertRaises(IndexError):
            self.gen.choices([], weights=[], k=0)
        with self.assertRaises(IndexError):
            self.gen.choices([], cum_weights=[], k=0)
        with self.assertRaises(IndexError):
            self.gen.choices([], k=0)

        # Number of weights doesn't match population.
        with self.assertRaises(ValueError):
            self.gen.choices(range(3), weights=[1, 2])
        with self.assertRaises(ValueError):
            self.gen.choices(range(3), cum_weights=[1, 2])

        # Total weight is zero.
        with self.assertRaises(ValueError):
            self.gen.choices(range(3), weights=[0.0, 0.0, 0.0])
        with self.assertRaises(ValueError):
            self.gen.choices(range(3), cum_weights=[0.0, 0.0, 0.0])

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

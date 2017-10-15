# Copyright 2017 Mark Dickinson
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Tests common to all generators.
"""
from __future__ import division

import collections
import itertools
import math
import pickle


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


class TestPCGCommon(object):
    """
    Mixin class providing tests common to all generators in the
    PCG family.
    """
    def test_creation_without_seed(self):
        gen1 = self.gen_class()
        gen2 = self.gen_class()

        sample1 = [gen1.random() for _ in range(10)]
        sample2 = [gen2.random() for _ in range(10)]

        # Possible in theory for these two samples to be identical; vanishingly
        # unlikely in practice.
        self.assertNotEqual(sample1, sample2)

    def test_creation_with_seed_and_sequence(self):
        gen1 = self.gen_class(seed=12345, sequence=1)
        gen2 = self.gen_class(12345, sequence=2)
        # Regression test for mdickinson/pcgrandom#25.
        gen3 = self.gen_class(12345, 1)
        self.assertNotEqual(gen1.getstate(), gen2.getstate())
        self.assertEqual(gen1.getrandbits(64), gen3.getrandbits(64))

    def test_seed_from_buffer(self):
        gen1 = self.gen_class(seed=b"your mother was a hamster")
        gen2 = self.gen_class(seed=bytearray(b"your mother was a hamster"))
        self.assertEqual(gen1.getstate(), gen2.getstate())

    def test_version_is_unicode(self):
        self.assertIsInstance(self.gen.VERSION, type(u''))

    def test_pickleability(self):
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            pickled_gen = pickle.dumps(self.gen, protocol=protocol)
            words = [self.gen.getrandbits(10) for _ in range(20)]
            recovered_gen = pickle.loads(pickled_gen)
            new_words = [recovered_gen.getrandbits(10) for _ in range(20)]
            self.assertEqual(
                self.gen.getstate(),
                recovered_gen.getstate(),
            )
            self.assertEqual(words, new_words)

    def test_direct_generator_output(self):
        # XXX Really a test of the core generator.
        coregen = self.gen._core_generator
        
        nsamples = 10000
        output_size = coregen.output_bits
        samples = [next(coregen) for _ in range(nsamples)]

        # Check that all samples are in the expected range.
        self.assertLessEqual(0, min(samples))
        self.assertLess(max(samples), 2**output_size)

        # Count number of times individual bits have appeared.
        counts = {}
        for bitpos in range(output_size):
            bit = 2**bitpos
            counts[bitpos] = sum(1 for sample in samples if (sample & bit))

        # Assuming that each bit is "fair", each count roughly follows a normal
        # distribution with mean 0.5*nsamples and standard deviation
        # 0.5*sqrt(nsamples). We'll call a count bad if it's more than 3
        # standard deviations from the mean.
        bad_counts = sum(
            abs(count - 0.5*nsamples) > 1.5*math.sqrt(nsamples)
            for count in counts.values()
        )

        # There's about a 1 in 370 chance of any one count being bad,
        # and the counts should be independent. To be safe, we allow
        # up to three bad counts before failing.
        self.assertLessEqual(bad_counts, 3)

    def test_state_includes_multiplier(self):
        gen = self.gen_class(seed=123, sequence=0, multiplier=5)
        coregen = gen._core_generator
        state = gen.getstate()
        
        words = [next(coregen) for _ in range(10)]

        gen2 = self.gen_class()
        gen2.setstate(state)
        coregen2 = gen2._core_generator
        same_again = [next(coregen2) for _ in range(10)]
        self.assertEqual(words, same_again)

    def test_bad_multiplier(self):
        with self.assertRaises(ValueError):
            self.gen_class(seed=123, sequence=0, multiplier=7)

    def test_independent_sequences(self):
        # Crude statistical test for lack of correlation. If X and Y are
        # independent and uniform on [0, 1], then (X - 0.5) * (Y - 0.5) has
        # mean 0 and standard deviation 1/12. By the central limit theorem, we
        # expect the average V of N such independent values to be roughly
        # normally distributed with mean 0 and standard deviation 1 /
        # (12*sqrt(N)). So we expect |V| to be at most 1 / (4*sqrt(N)) with
        # over 99% probability.
        gen1 = self.gen_class(seed=12345, sequence=0)
        gen2 = self.gen_class(seed=12345, sequence=1)
        N = 10000
        xs = [gen1.random() for _ in range(N)]
        ys = [gen2.random() for _ in range(N)]
        v = sum((x - 0.5) * (y - 0.5) for x, y in zip(xs, ys)) / N
        # Check we're within 3 standard deviations of the mean.
        self.assertLess(abs(v), 0.25/math.sqrt(N))

    def test_no_shared_state(self):
        # Get samples first from gen1, then from gen2.
        gen1 = self.gen_class(seed=12345, sequence=0)
        gen2 = self.gen_class(seed=12345, sequence=1)
        sample1_1 = [gen1.random() for _ in range(10)]
        sample2_1 = [gen2.random() for _ in range(10)]

        # Now in the opposite order: from gen2, then from gen1.
        gen1 = self.gen_class(seed=12345, sequence=0)
        gen2 = self.gen_class(seed=12345, sequence=1)
        sample2_2 = [gen2.random() for _ in range(10)]
        sample1_2 = [gen1.random() for _ in range(10)]

        # Now interleaved.
        gen1 = self.gen_class(seed=12345, sequence=0)
        gen2 = self.gen_class(seed=12345, sequence=1)
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

    def test_restore_state_from_different_generator(self):
        state = self.gen.getstate()

        bad_version = 'pcgrandom.BOGUS'
        bad_state = (bad_version,) + state[1:]
        with self.assertRaises(ValueError):
            self.gen.setstate(bad_state)

    def test_save_and_restore_state(self):
        # Generate some values.
        [self.gen.random() for _ in range(10)]

        # Save the state, generate some more.
        state = self.gen.getstate()
        samples2 = [self.gen.random() for _ in range(10)]

        # Restore the state, check we get the same samples.
        self.gen.setstate(state)
        samples3 = [self.gen.random() for _ in range(10)]
        self.assertEqual(samples2, samples3)

    def test_jumpahead(self):
        # Generate samples, each sample consuming exactly one output
        # from the core generator.
        get_sample = lambda: self.gen.getrandbits(self.gen._output_bits)

        original_state = self.gen.getstate()
        samples = [get_sample() for _ in range(1000)]

        # Rewind, check we can produce the exact same samples.
        self.gen.jumpahead(-1000)
        same_again = [get_sample() for _ in range(1000)]
        self.assertEqual(samples, same_again)

        # Now jump around randomly within the collection of samples,
        # and check we can reproduce them.
        positions = [self.gen.randrange(1000) for _ in range(1000)]

        self.gen.setstate(original_state)
        current_pos = 0
        for next_pos in positions:
            self.gen.jumpahead(next_pos - current_pos)
            sample = get_sample()
            self.assertEqual(sample, samples[next_pos])
            current_pos = next_pos + 1

    def test_jumpahead_zero(self):
        # Corner case: jumpahead(0) should work.
        state = self.gen.getstate()
        self.gen.jumpahead(0)
        self.assertEqual(self.gen.getstate(), state)

    def test_invertible(self):
        get_sample = lambda: self.gen.getrandbits(self.gen._output_bits)

        state = self.gen.getstate()
        self.gen.jumpahead(-1)
        get_sample()
        self.assertEqual(self.gen.getstate(), state)

    def test_state_preserves_gauss(self):
        # Test a state with gauss_next = None
        state = self.gen.getstate()
        samples1 = [self.gen.gauss(0.0, 1.0) for _ in range(5)]
        self.gen.setstate(state)
        samples2 = [self.gen.gauss(0.0, 1.0) for _ in range(5)]
        self.assertEqual(samples1, samples2)

        # ... and a state with gauss_next non-None.
        state = self.gen.getstate()
        samples1 = [self.gen.gauss(0.0, 1.0) for _ in range(5)]
        self.gen.setstate(state)
        samples2 = [self.gen.gauss(0.0, 1.0) for _ in range(5)]
        self.assertEqual(samples1, samples2)

    def test_seed_resets_gauss_state(self):
        self.gen.seed(2143)
        self.assertIsNone(self.gen.gauss_next)
        x1 = self.gen.gauss(0.0, 1.0)
        self.assertIsNotNone(self.gen.gauss_next)

        self.gen.seed(2143)
        self.assertIsNone(self.gen.gauss_next)
        x2 = self.gen.gauss(0.0, 1.0)
        self.assertIsNotNone(self.gen.gauss_next)

        self.assertEqual(x1, x2)

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
        bad_counts = sum(
            abs(count - 0.5*nsamples) > 1.5*math.sqrt(nsamples)
            for count in counts.values()
        )

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

    def test_getrandbits_int(self):
        # Check that we don't get longs on Python 2, for small inputs.
        xs = [self.gen.getrandbits(31) for _ in range(100)]
        for x in xs:
            self.assertIsInstance(x, int)

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

    def test_randrange_int(self):
        xs = [self.gen.randrange(2**31) for _ in range(100)]
        for x in xs:
            self.assertIsInstance(x, int)

    def test_randint_uniform(self):
        a, b = 10, 22
        samples = [self.gen.randint(a, b) for _ in range(10000)]
        self.check_uniform(range(a, b+1), samples)

    def test_randint_empty_range(self):
        with self.assertRaises(ValueError):
            self.gen.randint(7, 6)
        with self.assertRaises(ValueError):
            self.gen.randint(7, 5)
        self.assertEqual(self.gen.randint(7, 7), 7)

    def test_randint_float(self):
        with self.assertRaises(TypeError):
            self.gen.randint(1, 2.0)
        with self.assertRaises(TypeError):
            self.gen.randint(1.0, 2)
        with self.assertRaises(TypeError):
            self.gen.randint(2.0, 2)

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

    def test_random_uniformity(self):
        sample = [self.gen.random() for _ in range(10000)]

        # Bin and do a chi-squared test.
        binned_sample = [int(13*x) for x in sample]
        self.check_uniform(range(13), binned_sample)

    def test_specification_of_multiplier(self):
        # XXX This is really a test of the core generator.
        gen = self.gen_class(seed=123, sequence=0, multiplier=5)
        coregen = gen._core_generator

        for _ in range(10):
            old_state = coregen._state
            next(coregen)
            new_state = coregen._state
            self.assertEqual(
                new_state,
                (old_state * 5 + coregen._increment) % (2**coregen._state_bits)
            )

    def test_sequence_default(self):
        # XXX This is really a test of the core generator.
        gen = self.gen_class(seed=12345)
        coregen = gen._core_generator

        self.assertEqual(coregen._increment, coregen._default_increment)

    def test_full_period(self):
        # XXX Yep, another test of the core generator.
        gen = self.gen_class(seed=12345)
        coregen = gen._core_generator

        expected_period = 2**coregen._state_bits
        half_period = expected_period // 2

        state_start = coregen.getstate()
        coregen.advance(half_period)
        state_half = coregen.getstate()
        coregen.advance(half_period)
        state_full = coregen.getstate()
        self.assertEqual(state_start, state_full)
        self.assertNotEqual(state_start, state_half)

    def test_seed_from_integer(self):
        # XXX Another test of the core generator.
        gen1 = self.gen_class(seed=17289)
        state_bits = gen1._core_generator._state_bits

        gen2 = self.gen_class(seed=17289 + 2**state_bits)
        gen3 = self.gen_class(seed=17289 - 2**state_bits)
        self.assertEqual(gen1.getstate(), gen2.getstate())
        self.assertEqual(gen1.getstate(), gen3.getstate())

    # XXX Need more tests of core generator; move them to separate class.

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


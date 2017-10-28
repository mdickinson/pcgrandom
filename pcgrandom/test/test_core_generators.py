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
Tests for the core generators.
"""
import math
import pkgutil
import unittest

from pcgrandom.core_generators import (
    core_generator_from_state,
    xsh_rr_64_32,
    xsh_rs_64_32,
    xsl_rr_128_64,
)


class TestCoreGeneratorFromState(unittest.TestCase):
    """
    Tests for core_generator_from_state.
    """
    def test_recover_from_state(self):
        gen = xsh_rr_64_32(sequence=38, multiplier=5)
        recovered_gen = core_generator_from_state(gen.state)
        self.assertEqual(recovered_gen.state, gen.state)

    def test_recover_from_nonexistent_entry_point(self):
        gen = xsh_rr_64_32(sequence=38, multiplier=5)
        bogus_state = ("bogus",) + gen.state[1:]
        with self.assertRaises(ValueError):
            core_generator_from_state(bogus_state)


class CoreGeneratorCommonTests(object):
    """
    Tests common to all the core generators, used as a mixin class.
    """
    def setUp(self):
        self.gen = self.gen_class()

    def test_name_is_unicode(self):
        self.assertIsInstance(self.gen.name, type(u''))

    def test_recreate_from_bad_state(self):
        state = self.gen.state
        bogus_state = ("bogus",) + state[1:]
        with self.assertRaises(ValueError):
            type(self.gen).from_state(bogus_state)

    def test_recover_core_generator_from_state(self):
        state = self.gen.state
        recovered_gen = core_generator_from_state(state)
        self.assertEqual(recovered_gen.state, state)

    def test_direct_generator_output(self):
        coregen = self.gen

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
        gen = self.gen
        state = gen.state

        words = [next(gen) for _ in range(10)]

        gen2 = self.gen_class.from_state(state)
        same_again = [next(gen2) for _ in range(10)]
        self.assertEqual(words, same_again)

    def test_bad_multiplier(self):
        with self.assertRaises(ValueError):
            self.gen_class(sequence=0, multiplier=7)

    def test_advance(self):
        original_state = self.gen.state
        samples = [next(self.gen) for _ in range(1000)]

        # Rewind, check we can produce the exact same samples.
        self.gen.advance(-1000)
        same_again = [next(self.gen) for _ in range(1000)]
        self.assertEqual(samples, same_again)

        # Now jump around randomly within the collection of samples,
        # and check we can reproduce them.
        positions = [next(self.gen) % 1000 for _ in range(1000)]

        gen = self.gen_class.from_state(original_state)
        current_pos = 0
        for next_pos in positions:
            gen.advance(next_pos - current_pos)
            sample = next(gen)
            self.assertEqual(sample, samples[next_pos])
            current_pos = next_pos + 1

    def test_advance_invertible(self):
        state = self.gen.state
        self.gen.advance(-1)
        next(self.gen)
        self.assertEqual(self.gen.state, state)

    def test_full_period(self):
        coregen = self.gen

        expected_period = coregen.period
        # This test assumes that the period is a power of 2.
        self.assertIsPowerOfTwo(expected_period)

        half_period = expected_period // 2

        state_start = coregen.state
        coregen.advance(half_period)
        state_half = coregen.state
        coregen.advance(half_period)
        state_full = coregen.state
        self.assertEqual(state_start, state_full)
        self.assertNotEqual(state_start, state_half)

    def test_iterator(self):
        self.assertIs(iter(self.gen), self.gen)

    def assertIsPowerOfTwo(self, n):
        """
        Assert that the given integer is a power of two.
        """
        self.assertTrue(
            n > 0 and n & (n-1) == 0,
            msg="Expected a power of two, got {}".format(n))


class TestXshRR6432(CoreGeneratorCommonTests, unittest.TestCase):
    """
    Tests specific to the xsh_rr_64_32 generator.
    """
    gen_class = xsh_rr_64_32

    def test_agrees_with_reference_implementation_explicit_sequence(self):
        # Comparison with the C++ PCG reference implementation, version 0.98.
        gen = self.gen_class(sequence=54)
        gen.seed(42)

        expected_raw = pkgutil.get_data(
            'pcgrandom.test', 'data/setseq_xsh_rr_64_32.txt')
        expected_words = expected_raw.decode('utf-8').splitlines(False)
        actual_words = [format(next(gen), '#010x') for _ in range(32)]
        self.assertEqual(actual_words, expected_words)

    def test_agrees_with_reference_implementation_unspecified_sequence(self):
        # Comparison with the C++ PCG reference implementation, version 0.98.
        gen = self.gen_class()
        gen.seed(123)

        expected_raw = pkgutil.get_data(
            'pcgrandom.test', 'data/oneseq_xsh_rr_64_32.txt')
        expected_words = expected_raw.decode('utf-8').splitlines(False)
        actual_words = [format(next(gen), '#010x') for _ in range(32)]
        self.assertEqual(actual_words, expected_words)


class TestXshRS6432(CoreGeneratorCommonTests, unittest.TestCase):
    """
    Tests specific to the xsh_rs_64_32 generator.
    """
    gen_class = xsh_rs_64_32

    def test_agrees_with_reference_implementation_explicit_sequence(self):
        # Comparison with the C++ PCG reference implementation, version 0.98.
        gen = self.gen_class(sequence=54)
        gen.seed(42)

        expected_raw = pkgutil.get_data(
            'pcgrandom.test', 'data/setseq_xsh_rs_64_32.txt')
        expected_words = expected_raw.decode('utf-8').splitlines(False)
        actual_words = [format(next(gen), '#010x') for _ in range(32)]
        self.assertEqual(actual_words, expected_words)

    def test_agrees_with_reference_implementation_unspecified_sequence(self):
        # Comparison with the C++ PCG reference implementation, version 0.98.
        gen = self.gen_class()
        gen.seed(123)

        expected_raw = pkgutil.get_data(
            'pcgrandom.test', 'data/oneseq_xsh_rs_64_32.txt')
        expected_words = expected_raw.decode('utf-8').splitlines(False)
        actual_words = [format(next(gen), '#010x') for _ in range(32)]
        self.assertEqual(actual_words, expected_words)


class TestXslRR12864(CoreGeneratorCommonTests, unittest.TestCase):
    """
    Tests specific to the xsl_rr_128_64 generator.
    """
    gen_class = xsl_rr_128_64

    def test_agrees_with_reference_implementation_explicit_sequence(self):
        # Comparison with the C++ PCG reference implementation, version 0.98.
        gen = self.gen_class(sequence=54)
        gen.seed(42)

        expected_raw = pkgutil.get_data(
            'pcgrandom.test', 'data/setseq_xsl_rr_128_64.txt')
        expected_words = expected_raw.decode('utf-8').splitlines(False)
        actual_words = [format(next(gen), '#018x') for _ in range(32)]
        self.assertEqual(actual_words, expected_words)

    def test_agrees_with_reference_implementation_unspecified_sequence(self):
        # Comparison with the C++ PCG reference implementation, version 0.98.
        gen = self.gen_class()
        gen.seed(123)

        expected_raw = pkgutil.get_data(
            'pcgrandom.test', 'data/oneseq_xsl_rr_128_64.txt')
        expected_words = expected_raw.decode('utf-8').splitlines(False)
        actual_words = [format(next(gen), '#018x') for _ in range(32)]
        self.assertEqual(actual_words, expected_words)

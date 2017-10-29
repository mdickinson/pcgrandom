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
    generator_from_description,
    xsh_rr_64_32,
    xsh_rs_64_32,
    xsl_rr_128_64,
)


class TestCoreGeneratorFromState(unittest.TestCase):
    """
    Tests for core_generator_from_state.
    """
    def test_recover_from_description(self):
        generator = xsh_rr_64_32(sequence=38, multiplier=13)
        recovered = generator_from_description(generator.description)
        self.assertEqual(recovered.description, generator.description)
        self.assertEqual(type(recovered), type(generator))

    def test_recover_from_nonexistent_entry_point(self):
        generator = xsh_rr_64_32(sequence=38, multiplier=13)
        bogus_description = ("bogus",) + generator.description[1:]
        with self.assertRaises(ValueError):
            generator_from_description(bogus_description)


class CoreGeneratorCommonTests(object):
    """
    Tests common to all the core generators, used as a mixin class.
    """
    def setUp(self):
        self.generator = self.generator_class()
        self.stream = self.generator.stream(
            self.generator.state_from_seed(seed=71))

    def test_name_is_unicode(self):
        self.assertIsInstance(self.generator.name, type(u''))

    def test_recreate_from_bad_description(self):
        description = self.generator.description
        self.assertEqual(description[0], self.generator.name)
        bogus_description = ("bogus",) + description[1:]
        with self.assertRaises(ValueError):
            self.generator.from_description(bogus_description)

    def test_direct_generator_output(self):
        output_size = self.generator.output_bits
        coregen = self.stream

        nsamples = 10000
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

    def test_bad_multiplier(self):
        with self.assertRaises(ValueError):
            self.generator_class(sequence=0, multiplier=7)

    def test_advance(self):
        original_state = self.stream.state

        samples = [next(self.stream) for _ in range(1000)]

        # Rewind, check we can produce the exact same samples.
        self.stream.advance(-1000)
        same_again = [next(self.stream) for _ in range(1000)]
        self.assertEqual(samples, same_again)

        # Now jump around randomly within the collection of samples,
        # and check we can reproduce them.
        positions = [next(self.stream) % 1000 for _ in range(1000)]

        stream = self.generator.stream(original_state)
        current_pos = 0
        for next_pos in positions:
            stream.advance(next_pos - current_pos)
            self.assertEqual(next(stream), samples[next_pos])
            current_pos = next_pos + 1

    def test_advance_negative_one(self):
        state = self.stream.state
        self.stream.advance(-1)
        next(self.stream)
        self.assertEqual(self.stream.state, state)

    def test_advance_zero(self):
        state = self.stream.state
        self.stream.advance(0)
        self.assertEqual(self.stream.state, state)

    def test_advance_one(self):
        original_state = self.stream.state
        self.stream.advance(1)
        next_state = self.stream.state

        stream = self.generator.stream(original_state)
        next(stream)
        self.assertEqual(stream.state, next_state)

    def test_full_period(self):
        expected_period = self.generator.period
        # This test assumes that the period is a power of 2.
        self.assertIsPowerOfTwo(expected_period)

        half_period = expected_period // 2

        state_start = self.stream.state
        self.stream.advance(half_period)
        state_half = self.stream.state
        self.stream.advance(half_period)
        state_full = self.stream.state
        self.assertEqual(state_start, state_full)
        self.assertNotEqual(state_start, state_half)

    def test_iterator(self):
        self.assertIs(iter(self.stream), self.stream)

    def test_agrees_with_reference_implementation_explicit_sequence(self):
        # Comparison with the C++ PCG reference implementation, version 0.98.
        generator = self.generator_class(sequence=54)
        stream = generator.stream(generator.state_from_seed(42))

        datafile = "data/setseq_{}.txt".format(generator.name)
        expected_raw = pkgutil.get_data('pcgrandom.test', datafile)
        expected_words = expected_raw.decode('utf-8').splitlines(False)
        word_format = "#0{}x".format(2 + generator.output_bits // 4)
        actual_words = [format(next(stream), word_format) for _ in range(32)]
        self.assertEqual(actual_words, expected_words)

    def test_agrees_with_reference_implementation_unspecified_sequence(self):
        # Comparison with the C++ PCG reference implementation, version 0.98.
        generator = self.generator_class()
        stream = generator.stream(generator.state_from_seed(123))

        datafile = "data/oneseq_{}.txt".format(generator.name)
        expected_raw = pkgutil.get_data('pcgrandom.test', datafile)
        expected_words = expected_raw.decode('utf-8').splitlines(False)
        word_format = "#0{}x".format(2 + generator.output_bits // 4)
        actual_words = [format(next(stream), word_format) for _ in range(32)]
        self.assertEqual(actual_words, expected_words)

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
    generator_class = xsh_rr_64_32


class TestXshRS6432(CoreGeneratorCommonTests, unittest.TestCase):
    """
    Tests specific to the xsh_rs_64_32 generator.
    """
    generator_class = xsh_rs_64_32


class TestXslRR12864(CoreGeneratorCommonTests, unittest.TestCase):
    """
    Tests specific to the xsl_rr_128_64 generator.
    """
    generator_class = xsl_rr_128_64

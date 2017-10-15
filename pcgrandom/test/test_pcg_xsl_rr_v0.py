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
Tests for the PCG_XSL_RR_V0 generator.
"""
import pkgutil
import unittest

from pcgrandom.pcg_xsl_rr_v0 import PCG_XSL_RR_V0
from pcgrandom.test.test_pcg_common import TestPCGCommon


class Test_PCG_XSL_RR_V0(TestPCGCommon, unittest.TestCase):
    gen_class = PCG_XSL_RR_V0

    def setUp(self):
        self.gen = self.gen_class(seed=15206, sequence=1729)

    def test_agrees_with_reference_implementation_explicit_sequence(self):
        # Comparison with the C++ PCG reference implementation, version 0.98.
        gen = self.gen_class(seed=42, sequence=54)

        expected_raw = pkgutil.get_data(
            'pcgrandom.test', 'data/setseq_xsl_rr_128_64.txt')
        expected_words = expected_raw.decode('utf-8').splitlines(False)
        actual_words = [format(gen._next_output(), '#018x') for _ in range(32)]
        self.assertEqual(actual_words, expected_words)

    def test_agrees_with_reference_implementation_unspecified_sequence(self):
        # Comparison with the C++ PCG reference implementation, version 0.98.
        gen = self.gen_class(seed=123)

        expected_raw = pkgutil.get_data(
            'pcgrandom.test', 'data/oneseq_xsl_rr_128_64.txt')
        expected_words = expected_raw.decode('utf-8').splitlines(False)
        actual_words = [format(gen._next_output(), '#018x') for _ in range(32)]
        self.assertEqual(actual_words, expected_words)

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

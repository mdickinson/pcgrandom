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

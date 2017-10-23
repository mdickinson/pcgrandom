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
Tests for the PCG_XSH_RR_V0 generator.
"""
import pkgutil
import unittest

from pcgrandom import PCG_XSH_RR_V0
from pcgrandom.test.test_pcg_common import TestPCGCommon


class Test_PCG_XSH_RR_V0(TestPCGCommon, unittest.TestCase):
    gen_class = staticmethod(PCG_XSH_RR_V0)

    def setUp(self):
        self.gen = self.gen_class(seed=15206, sequence=1729)

    def test_agrees_with_reference_implementation_explicit_sequence(self):
        # Comparison with the C++ PCG reference implementation, version 0.98.
        gen = self.gen_class(seed=42, sequence=54)
        coregen = gen._core_generator

        expected_raw = pkgutil.get_data(
            'pcgrandom.test', 'data/setseq_xsh_rr_64_32.txt')
        expected_words = expected_raw.decode('utf-8').splitlines(False)
        actual_words = [format(next(coregen), '#010x') for _ in range(32)]
        self.assertEqual(actual_words, expected_words)

    def test_agrees_with_reference_implementation_unspecified_sequence(self):
        # Comparison with the C++ PCG reference implementation, version 0.98.
        gen = self.gen_class(seed=123)
        coregen = gen._core_generator

        expected_raw = pkgutil.get_data(
            'pcgrandom.test', 'data/oneseq_xsh_rr_64_32.txt')
        expected_words = expected_raw.decode('utf-8').splitlines(False)
        actual_words = [format(next(coregen), '#010x') for _ in range(32)]
        self.assertEqual(actual_words, expected_words)

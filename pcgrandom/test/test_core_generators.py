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
import unittest

from pcgrandom.core_generators import (
    xsh_rr_64_32,
    xsh_rs_64_32,
    xsl_rr_128_64,
)


class CoreGeneratorCommonTests(object):
    """
    Tests common to all the core generators, used as a mixin class.
    """
    def test_set_bad_state(self):
        state = self.gen.state
        bogus_state = ("bogus",) + state[1:]
        with self.assertRaises(ValueError):
            self.gen.state = bogus_state


class TestXshRR6432(CoreGeneratorCommonTests, unittest.TestCase):
    """
    Tests specific to the xsh_rr_64_32 generator.
    """
    def setUp(self):
        self.gen = xsh_rr_64_32()


class TestXshRS6432(CoreGeneratorCommonTests, unittest.TestCase):
    """
    Tests specific to the xsh_rs_64_32 generator.
    """
    def setUp(self):
        self.gen = xsh_rs_64_32()


class TestXslRR12864(CoreGeneratorCommonTests, unittest.TestCase):
    """
    Tests specific to the xsl_rr_128_64 generator.
    """
    def setUp(self):
        self.gen = xsl_rr_128_64()

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
import unittest

from pcgrandom import PCG_XSL_RR_V0
from pcgrandom.test.test_random import TestRandom


class Test_PCG_XSL_RR_V0(TestRandom, unittest.TestCase):
    gen_class = staticmethod(PCG_XSL_RR_V0)

    def setUp(self):
        self.gen = self.gen_class(seed=15206, sequence=1729)

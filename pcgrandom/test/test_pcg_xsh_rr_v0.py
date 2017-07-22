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
import unittest

from pcgrandom.pcg_xsh_rr_v0 import PCG_XSH_RR_V0
from pcgrandom.test.test_pcg_common import TestPCGCommon


class Test_PCG_XSH_RR_V0(TestPCGCommon, unittest.TestCase):
    gen_class = PCG_XSH_RR_V0

    def setUp(self):
        self.gen = self.gen_class(seed=15206, sequence=1729)

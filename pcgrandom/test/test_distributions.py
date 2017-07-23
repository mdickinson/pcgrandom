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

import unittest

from pcgrandom import Random


class TestDistributions(unittest.TestCase):
    """Minimal tests for the continuous distributions in the Distributions
    mixin class. Since the code is unaltered from that in the standard library,
    we leave it to the standard library tests to do more effective
    distribution-specific testing.

    """
    def setUp(self):
        self.gen = Random(12345)

    def test_uniform(self):
        self.assertIsInstance(self.gen.uniform(1.0, 2.0), float)

    def test_triangular(self):
        self.assertIsInstance(self.gen.triangular(1.0, 2.0), float)
        self.assertIsInstance(self.gen.triangular(1.0, 2.0, 1.3), float)

        # Exercise corner cases where low == high.
        self.assertEqual(self.gen.triangular(1.3, 1.3), 1.3)
        self.assertEqual(self.gen.triangular(1.3, 1.3, 1.3), 1.3)

        # Corner cases where mid == low or mid == high
        self.assertIsInstance(self.gen.triangular(1.0, 2.0, 2.0), float)
        self.assertIsInstance(self.gen.triangular(1.0, 2.0, 1.0), float)

    def test_normalvariate(self):
        sample = [self.gen.normalvariate(10.0, 5.0) for _ in range(10)]
        for elt in sample:
            self.assertIsInstance(elt, float)

    def test_lognormvariate(self):
        sample = [self.gen.lognormvariate(10.0, 5.0) for _ in range(10)]
        for elt in sample:
            self.assertIsInstance(elt, float)

    def test_expovariate(self):
        sample = [self.gen.expovariate(3.2) for _ in range(10)]
        for elt in sample:
            self.assertIsInstance(elt, float)

    def test_vonmisesvariate(self):
        sample = [self.gen.vonmisesvariate(0.0, 2.0) for _ in range(20)]
        for elt in sample:
            self.assertIsInstance(elt, float)

        # Corner case where kappa is tiny.
        sample = [self.gen.vonmisesvariate(0.0, 2e-10) for _ in range(20)]
        for elt in sample:
            self.assertIsInstance(elt, float)

    def test_gammavariate(self):
        with self.assertRaises(ValueError):
            self.gen.gammavariate(1.0, 0.0)
        with self.assertRaises(ValueError):
            self.gen.gammavariate(0.0, 1.0)

        # The implementation has separate cases for alpha less than,
        # equal to, or greater than 1. Make sure we exercise all three.
        sample = [self.gen.gammavariate(0.7, 1.3) for _ in range(10)]
        for elt in sample:
            self.assertIsInstance(elt, float)
        sample = [self.gen.gammavariate(1.0, 1.3) for _ in range(10)]
        for elt in sample:
            self.assertIsInstance(elt, float)
        sample = [self.gen.gammavariate(1.3, 1.3) for _ in range(10)]
        for elt in sample:
            self.assertIsInstance(elt, float)

    def test_gauss(self):
        sample = [self.gen.gauss(3.7, 1.3) for _ in range(10)]
        for elt in sample:
            self.assertIsInstance(elt, float)

    def test_betavariate(self):
        sample = [self.gen.betavariate(0.7, 1.3) for _ in range(10)]
        for elt in sample:
            self.assertIsInstance(elt, float)

    def test_paretovariate(self):
        sample = [self.gen.paretovariate(0.5) for _ in range(10)]
        for elt in sample:
            self.assertIsInstance(elt, float)

    def test_weibullvariate(self):
        sample = [self.gen.weibullvariate(700.0, 2.5) for _ in range(10)]
        for elt in sample:
            self.assertIsInstance(elt, float)

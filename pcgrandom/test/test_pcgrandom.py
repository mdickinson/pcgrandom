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
Tests for the pcgrandom top-level package.
"""
import types
import unittest

from past.builtins import long

import pcgrandom


class TestPCGRandom(unittest.TestCase):
    def test___all__(self):
        names_in_all = set(pcgrandom.__all__)
        public_names = {
            name for name, obj in pcgrandom.__dict__.items()
            if not name.startswith('_')
            if not isinstance(obj, types.ModuleType)
        }
        self.assertEqual(names_in_all, public_names)

    def test_random_class(self):
        gen = pcgrandom.Random()
        self.assertEqual(gen._core_generator_factory.output_bits, 32)
        # Exercise the generator to make sure nothing bad happens.
        [gen.random() for _ in range(10)]

    def test_pcg_32(self):
        gen = pcgrandom.PCG32()
        self.assertEqual(gen._core_generator_factory.output_bits, 32)
        [gen.random() for _ in range(10)]

    def test_pcg_64(self):
        gen = pcgrandom.PCG64()
        self.assertEqual(gen._core_generator_factory.output_bits, 64)
        [gen.random() for _ in range(10)]

    def test_float_generators(self):
        # Just exercise the float generators to make sure that they're usable.
        # We leave the detailed tests to Python's standard library, since these
        # generators are inherited directly from there.
        deviates = [
            pcgrandom.betavariate(0.3, 0.5),
            pcgrandom.expovariate(2.0),
            pcgrandom.gammavariate(0.3, 0.5),
            pcgrandom.gauss(0.0, 1.0),
            pcgrandom.lognormvariate(3.2, 1.1),
            pcgrandom.normalvariate(3.2, 1.1),
            pcgrandom.paretovariate(2.5),
            pcgrandom.random(),
            pcgrandom.triangular(),
            pcgrandom.uniform(5.0, 6.0),
            pcgrandom.vonmisesvariate(0.5, 2.3),
            pcgrandom.weibullvariate(54.0, 2.3),
        ]
        for deviate in deviates:
            self.assertIsInstance(deviate, float)

    def test_integer_generators(self):
        # As above, just exercise to detect shallow errors. More stringent
        # tests are in the tests for the individual generators.
        deviates = [
            pcgrandom.getrandbits(17),
            pcgrandom.randint(5, 10),
            pcgrandom.randrange(5, 10),
        ]
        for deviate in deviates:
            self.assertIsInstance(deviate, (int, long))

    def test_combinatorial_generators(self):
        # In-depth testing is left to the unit tests for the individual
        # generators.
        self.assertIsInstance(pcgrandom.choice(range(5)), int)
        self.assertIsInstance(pcgrandom.choices(range(5), k=3), list)
        self.assertIsInstance(pcgrandom.sample(range(5), 3), list)
        population = list(range(5))
        pcgrandom.shuffle(population)
        self.assertEqual(set(population), set(range(5)))

    def test_get_and_set_state(self):
        state = pcgrandom.getstate()
        sample1 = pcgrandom.randrange(10**6)
        pcgrandom.setstate(state)
        sample2 = pcgrandom.randrange(10**6)
        self.assertEqual(sample1, sample2)

    def test_jumpahead(self):
        state = pcgrandom.getstate()
        pcgrandom.jumpahead(123456)
        self.assertNotEqual(pcgrandom.getstate(), state)
        pcgrandom.jumpahead(-100000)
        self.assertNotEqual(pcgrandom.getstate(), state)
        pcgrandom.jumpahead(-23456)
        self.assertEqual(pcgrandom.getstate(), state)

    def test_seed(self):
        pcgrandom.seed(6789)
        state = pcgrandom.getstate()
        [pcgrandom.randrange(10**6) for _ in range(150)]
        self.assertNotEqual(pcgrandom.getstate(), state)
        pcgrandom.seed(6789)
        self.assertEqual(pcgrandom.getstate(), state)

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
Tests for seeding helpers.
"""
import unittest

from pcgrandom.seeding import seed_from_object, seed_from_system_entropy


class TestSeeding(unittest.TestCase):
    def test_seed_from_system_entropy_different(self):
        seeds = [seed_from_system_entropy(bits=64) for _ in range(10)]
        for seed in seeds:
            self.assertEqual(seed % 2**64, seed)
        self.assertEqual(len(seeds), len(set(seeds)))

    def test_seed_from_object_large_bits(self):
        with self.assertRaises(ValueError):
            seed_from_object(b"some string or other", 513)
        seed = seed_from_object(b"some string or other", 512)
        self.assertGreater(seed.bit_length(), 500)
        self.assertLessEqual(seed.bit_length(), 512)

    def test_seed_from_object_bad_object_type(self):
        with self.assertRaises(TypeError):
            seed_from_object(3.4, 32)

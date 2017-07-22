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

import json
import pickle
import pkgutil
import unittest

from pcgrandom.test.fingerprint import Sampler, string_to_bytes, list_to_tuple


class TestReproducibility(unittest.TestCase):
    def test_reproducibility(self):
        raw_data = pkgutil.get_data(
            'pcgrandom.test', 'data/generator_fingerprints.json')
        fingerprints = json.loads(raw_data.decode('utf8'))

        for generator_data in fingerprints['generators']:
            # For each pickle, we create the generator from the pickle
            # and then take its fingerprint. First we need to find only
            # those pickles compatible with the current version of Python.
            pickles_by_protocol = {
                pickle['protocol']: pickle['pickle']
                for pickle in generator_data['pickles']
            }
            usable_protocols = (
                set(pickles_by_protocol)
                & set(range(pickle.HIGHEST_PROTOCOL + 1))
            )

            # Need at least one usable pickle, else the test isn't very useful.
            self.assertGreater(len(usable_protocols), 0)

            for protocol in usable_protocols:
                pickled_generator = pickles_by_protocol[protocol]
                generator = pickle.loads(string_to_bytes(pickled_generator))

                # The JSON-serialised state ends up with lists where
                # there were originally tuples. Convert back.
                stored_state = list_to_tuple(generator_data['state'])
                computed_state = generator.getstate()
                self.assertEqual(computed_state, stored_state)

                stored_fingerprint = generator_data['fingerprint']
                computed_fingerprint = Sampler(generator).samples()
                self.assertEqual(computed_fingerprint, stored_fingerprint)

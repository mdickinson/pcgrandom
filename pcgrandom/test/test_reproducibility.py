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

from pcgrandom.test.fingerprint import json_fingerprint, string_to_bytes


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
                computed_data = json_fingerprint(generator)

                self.assertEqual(
                    generator_data['state'],
                    computed_data['state'],
                )
                self.assertEqual(
                    generator_data['fingerprint'],
                    computed_data['fingerprint'],
                )

    def test_doc_reproducibility_example(self):
        # Example used in the README documentation. If for whatever reason
        # this changes, update the README.
        from pcgrandom import PCG_XSH_RR_V0
        gen = PCG_XSH_RR_V0(seed=67182)
        seq = ''.join(gen.choice('0123456789') for _ in range(20))
        self.assertEqual(seq, '15183975423492044867')

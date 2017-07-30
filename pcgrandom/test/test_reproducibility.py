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
import pkgutil
import unittest

from pcgrandom.test.fingerprint import json_fingerprint


def load_fingerprints():
    """Load and parse the saved generator fingerprints. Used by tests in
    TestReproducibility.

    """
    raw_data = pkgutil.get_data(
        'pcgrandom.test', 'data/generator_fingerprints.json')
    return json.loads(raw_data.decode('utf8'))


class TestReproducibility(unittest.TestCase):
    def test_reproducibility(self):
        fingerprints = load_fingerprints()

        for generator_data in fingerprints['generators']:
            constructor = generator_data['constructor']
            computed_data = json_fingerprint(constructor)

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

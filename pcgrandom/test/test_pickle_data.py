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
Test that we can unpickle a generator that was pickled on a possibly
different Python version.
"""
import pickle
import unittest

from pcgrandom.test.write_pickle_data import (
    AllGeneratorsPickles,
    pickle_filenames,
)


class TestUnpickling(unittest.TestCase):
    def test_unpickling(self):
        for version, filename in pickle_filenames().items():
            all_pickle_data = AllGeneratorsPickles.load(filename)
            self.check_pickle_data(version, all_pickle_data)

    def check_pickle_data(self, version, all_pickle_data):
        for generator_data in all_pickle_data.generators:
            expected_state = generator_data.state

            for pickle_data in generator_data.pickles:
                protocol = pickle_data.protocol
                pickled_generator = pickle_data.data
                if protocol > pickle.HIGHEST_PROTOCOL:
                    continue
                self.assertEqual(
                    pickle.loads(pickled_generator).getstate(),
                    expected_state,
                    msg=(
                        "Unpickling failed for version {}, "
                        "protocol {}".format(version, protocol)
                    ),
                )

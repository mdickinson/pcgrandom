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
import os
import shutil
import tempfile
import unittest

from pcgrandom.test.regenerate_reproducibility_data import (
    regenerate_data_main)
from pcgrandom.test.testing_utils import args_in_sys_argv


class TestRegenerateReproducibilityData(unittest.TestCase):
    """
    Yes, this is a test for a test utility.
    """
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_write_data_with_explicit_filename(self):
        filename = os.path.join(self.tempdir, 'fingerprints.json')

        self.assertFalse(os.path.exists(filename))
        with args_in_sys_argv([filename]):
            regenerate_data_main()
        self.assertTrue(os.path.exists(filename))

        # Check that it's a valid JSON file, with the expected top-level
        # structure.
        with open(filename) as f:
            contents = json.load(f)
        self.assertIsInstance(contents, dict)
        self.assertIn('generators', contents)

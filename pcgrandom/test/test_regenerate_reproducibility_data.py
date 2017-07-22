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

import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from pcgrandom.test.regenerate_reproducibility_data import (
    DEFAULT_REPRODUCIBILITY_FILENAME,
    regenerate_data_main,
)


@contextlib.contextmanager
def cwd(dir):
    """
    Temporarily change the current working directory.
    """
    old_cwd = os.getcwd()
    os.chdir(dir)
    try:
        yield
    finally:
        os.chdir(old_cwd)


@contextlib.contextmanager
def args_in_sys_argv(args):
    """
    Temporarily change sys.argv to something of the form [prog_name, args].
    """
    old_sys_argv = sys.argv
    sys.argv = sys.argv[:1] + args
    try:
        yield
    finally:
        sys.argv = old_sys_argv


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
        args = ["-o", filename]

        self.assertFalse(os.path.exists(filename))
        with args_in_sys_argv(args):
            regenerate_data_main()
        self.assertTrue(os.path.exists(filename))

        # Check that it's a valid JSON file, with the expected top-level
        # structure.
        with open(filename) as f:
            contents = json.load(f)
        self.assertIsInstance(contents, dict)
        self.assertIn('generators', contents)

    def test_write_data_no_filename(self):
        filename = os.path.join(self.tempdir, DEFAULT_REPRODUCIBILITY_FILENAME)
        args = []

        self.assertFalse(os.path.exists(filename))
        with args_in_sys_argv(args):
            with cwd(self.tempdir):
                regenerate_data_main()
        self.assertTrue(os.path.exists(filename))

        # Check that it's a valid JSON file, with the expected top-level
        # structure.
        with open(filename) as f:
            contents = json.load(f)
        self.assertIsInstance(contents, dict)
        self.assertIn('generators', contents)

    def test_write_data_with_explicit_filename_subprocess(self):
        filename = os.path.join(self.tempdir, 'fingerprints.json')
        self.assertFalse(os.path.exists(filename))
        subprocess.check_call(['pcg-test-data', '-o', filename])
        self.assertTrue(os.path.exists(filename))

        # Check that it's a valid JSON file, with the expected top-level
        # structure.
        with open(filename) as f:
            contents = json.load(f)
        self.assertIsInstance(contents, dict)
        self.assertIn('generators', contents)

    def test_write_data_no_filename_subprocess(self):
        filename = os.path.join(self.tempdir, DEFAULT_REPRODUCIBILITY_FILENAME)
        self.assertFalse(os.path.exists(filename))
        subprocess.check_call(['pcg-test-data'], cwd=self.tempdir)
        self.assertTrue(os.path.exists(filename))

        # Check that it's a valid JSON file, with the expected top-level
        # structure.
        with open(filename) as f:
            contents = json.load(f)
        self.assertIsInstance(contents, dict)
        self.assertIn('generators', contents)

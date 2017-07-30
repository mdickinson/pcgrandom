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
Script used to regenerate pickle test data.

Requires that all relevant Python versions are present on this machine.
"""
import subprocess

# Dictionary mapping python version id to executable paths on this system.
EXECUTABLES = {
    'python2': 'python2',
    'python3': 'python',
    'pypy2': 'pypy',
    'pypy3': 'pypy3',
}


def main():
    """
    Regenerate pickle test data for all Python versions.
    """
    from pcgrandom.test.write_pickle_data import pickle_filenames

    for python_version, pickle_filename in pickle_filenames().items():
        python_executable = EXECUTABLES[python_version]
        cmd = [
            python_executable,
            '-m', 'pcgrandom.test.write_pickle_data',
            pickle_filename,
        ]
        subprocess.check_call(cmd)


if __name__ == '__main__':
    main()

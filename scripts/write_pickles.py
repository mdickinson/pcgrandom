"""
Script used to regenerate test data.
"""
import os
import pkgutil
import subprocess

from pcgrandom.test.write_pickle_data import json_filenames

# Dictionary mapping python version id to executable paths on this system.
EXECUTABLES = {
    'python2': 'python2',
    'python3': 'python',
    'pypy2': 'pypy',
    'pypy3': 'pypy3',
}


def test_data_directory():
    """
    Locate the test data directory.
    """
    test_package_name = 'pcgrandom.test'
    test_package = pkgutil.get_loader(test_package_name).load_module(
        test_package_name)
    return os.path.join(
        os.path.dirname(test_package.__file__), 'data')


def main():
    """
    Regenerate pickle test data on a particular Python version.
    """
    data_dir = test_data_directory()
    for version_id, json_filename in json_filenames().items():
        python_executable = EXECUTABLES[version_id]
        output_filename = os.path.join(data_dir, json_filename)
        cmd = [
            python_executable,
            '-m', 'pcgrandom.test.write_pickle_data',
            '--output', output_filename,
        ]
        subprocess.check_call(cmd)


if __name__ == '__main__':
    main()

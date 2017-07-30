"""
Script used to regenerate test data.
"""
import os
import pkgutil
import subprocess

# Dictionary mapping python version id to executable paths on this system.
PYTHON_VERSIONS = {
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
    for version_id, python_executable in PYTHON_VERSIONS.items():
        output_filename = os.path.join(
            data_dir, 'pickles-{}.json'.format(version_id))
        cmd = [
            python_executable,
            '-m', 'pcgrandom.test.write_pickle_data',
            '--output', output_filename,
        ]
        subprocess.check_call(cmd)


if __name__ == '__main__':
    main()

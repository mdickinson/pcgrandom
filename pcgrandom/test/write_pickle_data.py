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
Tests that we can recover generators from pickles generated
on different Python versions.
"""
import argparse
import base64
import json
import os
import pickle
import pkgutil
import platform

from pcgrandom import pcg_generators


def bytes_to_string(b):
    """Reversibly convert an arbitrary bytestring into a unicode string, for
    JSON serialization.

    """
    return base64.b64encode(b).decode('ascii')


def string_to_bytes(s):
    """Reverse transformation for bytes_to_string.
    """
    return base64.b64decode(s.encode('ascii'))


def list_to_tuple(l):
    """Recursive list to tuple conversion."""
    if isinstance(l, list):
        return tuple(map(list_to_tuple, l))
    else:
        return l


def test_data_directory():
    """
    Locate the test data directory.
    """
    test_package_name = 'pcgrandom.test'
    test_package = pkgutil.get_loader(test_package_name).load_module(
        test_package_name)
    return os.path.join(
        os.path.dirname(test_package.__file__), 'data')


def pickle_filenames():
    """
    JSON filenames to write to, keyed by Python version.

    Returns
    -------
    Mapping from Python version identifiers to output filenames.
    """
    data_dir = test_data_directory()

    versions = ['python2', 'python3', 'pypy2', 'pypy3']
    return {
        version: os.path.join(data_dir, 'pickles-{}.json'.format(version))
        for version in versions
    }


def available_protocols():
    """
    Available Pickle protocols for this version of Python.
    """
    return range(pickle.HIGHEST_PROTOCOL + 1)


def generators():
    return [
        generator(seed=12345)
        for generator in pcg_generators
    ] + [
        generator(seed=67189, sequence=34)
        for generator in pcg_generators
    ]


def read_pickle_info(filename):
    """
    Read pickle data from a JSON file.

    Returns
    -------
    pickle_data : dict
        Nested dictionary containing pickle data.
    """
    with open(filename) as f:
        all_pickle_data = json.load(f)

    # Convert states back to tuples; decode the pickles.
    for generator_data in all_pickle_data['generators']:
        generator_data['state'] = list_to_tuple(generator_data['state'])

        # Decode the pickles.
        for pickle_data in generator_data['pickles']:
            pickle_data['pickle'] = string_to_bytes(pickle_data['pickle'])

    return all_pickle_data


def write_pickle_info(generators, filename):
    """
    Write pickle information out in JSON form to the given filename.

    The actual pickle bytestrings are base64 encoded, for ease of
    JSON encoding.
    """
    generator_data = []
    for generator in generators:
        state = generator.getstate()

        pickles = []
        for protocol in available_protocols():
            pickled_generator = pickle.dumps(generator, protocol=protocol)
            pickles.append(
                dict(
                    protocol=protocol,
                    pickle=bytes_to_string(pickled_generator),
                )
            )
        generator_data.append(
            dict(
                state=state,
                pickles=pickles,
            )
        )

    # Get platform information.
    platform_info = {
        'architecture': platform.architecture(),
        'platform': platform.platform(),
        'implementation': platform.python_implementation(),
        'version': platform.python_version(),
        'revision': platform.python_revision(),
    }

    file_content = dict(
        generators=generator_data,
        platform=platform_info,
    )

    # XXX Refactor, so that the above logic isn't in the same
    # place as the file writing.
    with open(filename, 'w') as f:
        json.dump(file_content, f, sort_keys=True, indent=4)
        # json.dump doesn't write a trailing newline. Not a big
        # deal, but for a line-based file it's nice to have one.
        f.write("\n")


def write_pickle_data():
    """
    Main script function for writing pickle data.
    """
    parser = argparse.ArgumentParser(
        description="Regenerate pickle data.",
    )
    parser.add_argument(
        "output",
        help="Output path to write the data to (default: %(default)r).",
    )

    args = parser.parse_args()

    write_pickle_info(
        generators=generators(),
        filename=args.output,
    )


if __name__ == '__main__':
    write_pickle_data()

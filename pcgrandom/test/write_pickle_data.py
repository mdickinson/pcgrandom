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


def list_to_tuple(l):
    """Recursive list to tuple conversion."""
    if isinstance(l, list):
        return tuple(map(list_to_tuple, l))
    else:
        return l


def tuple_to_list(l):
    """Recursive tuple to list conversion."""
    if isinstance(l, tuple):
        return list(map(tuple_to_list, l))
    else:
        return l


def current_platform_info():
    return {
        'architecture': platform.architecture(),
        'platform': platform.platform(),
        'implementation': platform.python_implementation(),
        'version': platform.python_version(),
        'revision': platform.python_revision(),
    }


class PickleInfo(object):
    def __init__(self, protocol, data):
        self.protocol = protocol
        self.data = data

    @classmethod
    def from_generator(cls, generator, protocol):
        return cls(
            protocol=protocol,
            data=pickle.dumps(generator, protocol),
        )

    @classmethod
    def from_json_dict(cls, json_dict):
        return cls(
            protocol=json_dict['protocol'],
            data=base64.b64decode(json_dict['pickle'].encode('ascii')),
        )

    def to_json_dict(self):
        return dict(
            pickle=base64.b64encode(self.data).decode('ascii'),
            protocol=self.protocol,
        )


class GeneratorPickles(object):
    def __init__(self, state, pickles):
        self.state = state
        self.pickles = pickles

    @classmethod
    def from_generator(cls, generator):
        pickles = [
            PickleInfo.from_generator(generator, protocol)
            for protocol in range(pickle.HIGHEST_PROTOCOL + 1)
        ]

        return cls(
            state=generator.getstate(),
            pickles=pickles,
        )

    @classmethod
    def from_json_dict(cls, json_dict):
        return cls(
            state=list_to_tuple(json_dict['state']),
            pickles=list(map(PickleInfo.from_json_dict, json_dict['pickles'])),
        )

    def to_json_dict(self):
        return dict(
            state=tuple_to_list(self.state),
            pickles=[
                pickle_data.to_json_dict() for pickle_data in self.pickles
            ],
        )


class AllGeneratorsPickles(object):
    def __init__(self, platform_info, generators):
        self.platform_info = platform_info
        self.generators = generators

    @classmethod
    def from_generators(cls, generators):
        return cls(
            platform_info=current_platform_info(),
            generators=[
                GeneratorPickles.from_generator(generator)
                for generator in generators
            ],
        )

    @classmethod
    def load(cls, filename):
        """
        Read an AllGeneratorsPickles object from a JSON file.
        """
        with open(filename) as f:
            json_dict = json.load(f)
        return cls(
            platform_info=json_dict['platform'],
            generators=[
                GeneratorPickles.from_json_dict(json_generator)
                for json_generator in json_dict['generators']
            ],
        )

    def dump(self, filename):
        """
        Write this object to a file in JSON form.
        """
        file_content = dict(
            generators=[
                generator.to_json_dict()
                for generator in self.generators
            ],
            platform=self.platform_info,
        )
        with open(filename, 'w') as f:
            json.dump(
                file_content, f, sort_keys=True, indent=4,
                separators=(',', ': '),
            )
            # json.dump doesn't write a trailing newline. Not a big
            # deal, but for a line-based file it's nice to have one.
            f.write("\n")


def pickle_filenames():
    """
    JSON filenames to write to, keyed by Python version.

    Returns
    -------
    Mapping from Python version identifiers to output filenames.
    """
    # Locate the test data directory.
    test_package_name = 'pcgrandom.test'
    test_package = pkgutil.get_loader(test_package_name).load_module(
        test_package_name)
    data_dir = os.path.join(os.path.dirname(test_package.__file__), 'data')

    versions = ['python2', 'python3', 'pypy2', 'pypy3']
    return {
        version: os.path.join(data_dir, 'pickles-{}.json'.format(version))
        for version in versions
    }


def generators():
    return [
        generator(seed=12345)
        for generator in pcg_generators
    ] + [
        generator(seed=67189, sequence=34)
        for generator in pcg_generators
    ]


def write_pickle_data():
    """
    Main script function for writing pickle data.
    """
    parser = argparse.ArgumentParser(
        description="Regenerate pickle data.",
    )
    parser.add_argument(
        "output",
        help="Output path to write the generated data to.",
    )
    args = parser.parse_args()
    AllGeneratorsPickles.from_generators(generators()).dump(args.output)


if __name__ == '__main__':  # pragma: no cover
    write_pickle_data()

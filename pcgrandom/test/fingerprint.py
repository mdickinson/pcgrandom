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
Utilities to create the generator_fingerprints.json file.
"""

import contextlib
import json

from pcgrandom import pcg_generators


CARD_SUITS = ['Spades', 'Hearts', 'Diamonds', 'Clubs']
CARD_VALUES = [
    'Ace', 'King', 'Queen', 'Jack', 'Ten', 'Nine', 'Eight', 'Seven',
    'Six', 'Five', 'Four', 'Three', 'Two'
]
CARDS = [
    '{} of {}'.format(value, suit)
    for suit in CARD_SUITS for value in CARD_VALUES
]


# Mapping from version strings to corresponding classes.
generator_class = {
    genclass.VERSION: genclass
    for genclass in pcg_generators
}


def construct_generator(constructor):
    """Construct generator from JSON-serializable construction information.
    """
    localvars = {}
    exec(constructor, localvars)
    return localvars['generator']


@contextlib.contextmanager
def restore_state(generator):
    """
    Restore the generator state on with-block exit.
    """
    state = generator.getstate()
    try:
        yield
    finally:
        generator.setstate(state)


class Fingerprinter(object):
    """
    Generator of "standard" samples, for use in reproducibility tests.
    """

    # List of sample methods that will be used to create the fingerprint.
    sample_methods = [
        'bridge_hand', 'coin_tosses', 'die_rolls', 'floats',
        'shuffle', 'words'
    ]

    def __init__(self, generator):
        self.generator = generator
        self.state = self.generator.getstate()

    def bridge_hand(self):
        return [self.generator.sample(CARDS, 13)]

    def coin_tosses(self):
        return [self.generator.choice(['H', 'T']) for _ in range(100)]

    def die_rolls(self):
        return [self.generator.randint(1, 6) for _ in range(20)]

    def floats(self):
        return [self.generator.random() for _ in range(20)]

    def shuffle(self):
        population = list(range(20))
        self.generator.shuffle(population)
        return population

    def words(self):
        return [self.generator.getrandbits(32) for _ in range(20)]

    def fingerprint(self):
        fingerprint = {}
        for method_name in self.sample_methods:
            method = getattr(self, method_name)
            with restore_state(self.generator):
                fingerprint[method_name] = method()
        return fingerprint


def tuple_to_list(l):
    """Recursive tuple to list conversion."""
    if isinstance(l, tuple):
        return list(map(tuple_to_list, l))
    else:
        return l


def json_fingerprint(constructor):
    """
    Return a JSON-serializable dict with data for the given generator.
    """
    generator = construct_generator(constructor)

    generator_data = {
        'constructor': constructor,
        'fingerprint': Fingerprinter(generator).fingerprint(),
        'state': tuple_to_list(generator.getstate()),
    }
    return generator_data


def write_fingerprints(constructors, filename):
    """
    Write fingerprint data for each given generator to the given file.
    """
    file_content = {
        'generators': [
            json_fingerprint(constructor)
            for constructor in constructors
        ],
    }
    with open(filename, 'w') as f:
        json.dump(
            file_content, f, sort_keys=True, indent=4,
            separators=(',', ': '),
        )
        # json.dump doesn't write a trailing newline. Not a big
        # deal, but for a line-based file it's nice to have one.
        f.write("\n")

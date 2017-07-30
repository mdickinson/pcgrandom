"""
Test that we can unpickle a generator that was pickled on a possibly
different Python version.
"""

# XXX Put python version into pickle data file.

import base64
import json
import pickle
import pkgutil
import unittest

from pcgrandom.test.write_pickle_data import json_filenames


def load_pickle_data(filename):
    """
    Load pickle data from the given file.
    """
    raw_data = pkgutil.get_data('pcgrandom.test', 'data/{}'.format(filename))
    return json.loads(raw_data.decode('utf-8'))


def string_to_bytes(s):
    """Reverse transformation for bytes_to_string.
    """
    return base64.b64decode(s.encode('ascii'))


def tuple_to_list(l):
    """Recursive tuple to list conversion."""
    if isinstance(l, tuple):
        return list(map(tuple_to_list, l))
    else:
        return l


class TestUnpickling(unittest.TestCase):
    def test_unpickling(self):
        for version, filename in json_filenames().items():
            all_pickle_data = load_pickle_data(filename)
            for generator_data in all_pickle_data['generators']:
                state = generator_data['state']
                for pickle_data in generator_data['pickles']:
                    protocol = pickle_data['protocol']
                    pickled_generator = string_to_bytes(pickle_data['pickle'])
                    if protocol > pickle.HIGHEST_PROTOCOL:
                        continue
                    generator = pickle.loads(pickled_generator)
                    self.assertEqual(
                        tuple_to_list(generator.getstate()),
                        state,
                    )

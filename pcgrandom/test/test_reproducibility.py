import base64
import json
import pickle
import pkgutil
import unittest

from pcgrandom.test.fingerprint import Sampler


fingerprints = json.loads(
    pkgutil.get_data('pcgrandom.test', 'data/generator_fingerprints.json')
)


def list_to_tuple(l):
    """Recursive list to tuple conversion."""
    if isinstance(l, list):
        return tuple(map(list_to_tuple, l))
    else:
        return l


def string_to_bytes(s):
    """Reverse transformation for bytes_to_string.
    """
    return base64.b64decode(s.encode('ascii'))


class TestReproducibility(unittest.TestCase):
    def test_reproducibility(self):
        for generator_data in fingerprints['generators']:
            # For each pickle, we create the generator from the pickle
            # and then take its fingerprint. First we need to find only
            # those pickles compatible with the current version of Python.
            pickles_by_protocol = {
                pickle['protocol']: pickle['pickle']
                for pickle in generator_data['pickles']
            }
            usable_protocols = (
                set(pickles_by_protocol)
                & set(range(pickle.HIGHEST_PROTOCOL + 1))
            )

            # Need at least one usable pickle, else the test isn't very useful.
            self.assertGreater(len(usable_protocols), 0)

            for protocol in usable_protocols:
                pickled_generator = pickles_by_protocol[protocol]
                generator = pickle.loads(string_to_bytes(pickled_generator))

                # The JSON-serialised state ends up with lists where
                # there were originally tuples. Convert back.
                stored_state = list_to_tuple(generator_data['state'])
                computed_state = generator.getstate()
                self.assertEqual(computed_state, stored_state)

                stored_fingerprint = generator_data['fingerprint']
                computed_fingerprint = Sampler(generator).samples()
                self.assertEqual(computed_fingerprint, stored_fingerprint)

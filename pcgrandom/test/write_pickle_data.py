"""
Tests that we can recover generators from pickles generated
on different Python versions.
"""
import argparse
import base64
import json
import pickle

from pcgrandom import pcg_generators

DEFAULT_OUTPUT = "pickles_python3.json"


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


def bytes_to_string(b):
    """Reversibly convert an arbitrary bytestring into a unicode string, for
    JSON serialization.

    """
    return base64.b64encode(b).decode('ascii')


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
    file_content = {'generators': generator_data}

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
        "-o", "--output",
        default=DEFAULT_OUTPUT,
        help="Output path to write the data to (default: %(default)r).",
    )

    args = parser.parse_args()

    write_pickle_info(
        generators=generators(),
        filename=args.output,
    )


if __name__ == '__main__':
    write_pickle_data()

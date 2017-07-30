# -*- coding: utf-8 -*-

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

"""Script to regenerate the reproducibility data used by the reproducibility
tests.

"""
import argparse

from pcgrandom.test.fingerprint import write_fingerprints

# Default filename to use for output.
DEFAULT_REPRODUCIBILITY_FILENAME = "generator_fingerprints.json"


# Generators
generator_creators = [
    ('pcgrandom.PCG_XSH_RR_V0', {'seed': 12345}),
    ('pcgrandom.PCG_XSH_RR_V0', {'seed': 12345, 'sequence': 24}),
    ('pcgrandom.PCG_XSH_RR_V0', {'seed': u"noodleloaf"}),

    ('pcgrandom.PCG_XSH_RS_V0', {'seed': 90210}),
    ('pcgrandom.PCG_XSH_RS_V0',
     {'seed': u"Το αεροστρωματόχημά μου είναι γεμάτο χέλια", 'sequence': -7}),

    ('pcgrandom.PCG_XSL_RR_V0', {'seed': 41509}),
    ('pcgrandom.PCG_XSL_RR_V0', {'seed': -3, 'sequence': 2**128 + 37}),
]


def constructors():
    for version, kwargs in generator_creators:
        yield {
            'version': version,
            'kwargs': kwargs,
        }


def regenerate_data_main():
    parser = argparse.ArgumentParser(
        description="Regenerate reproducibility data.",
    )
    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_REPRODUCIBILITY_FILENAME,
        help="Output path to write the data to (default: %(default)r).",
    )

    args = parser.parse_args()

    write_fingerprints(
        constructors=constructors(),
        filename=args.output,
    )

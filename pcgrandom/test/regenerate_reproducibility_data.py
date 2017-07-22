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
from pcgrandom.pcg_xsh_rr_v0 import PCG_XSH_RR_V0
from pcgrandom.pcg_xsl_rr_v0 import PCG_XSL_RR_V0

# Default filename to use for output.
DEFAULT_REPRODUCIBILITY_FILENAME = "generator_fingerprints.json"


def generators():
    """Return the specific generators to be used for reproducibility testing.
    """
    return [
        PCG_XSH_RR_V0(seed=12345),
        PCG_XSL_RR_V0(seed=41509),
    ]


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
        generators=generators(),
        filename=args.output,
    )


if __name__ == '__main__':
    regenerate_data_main()

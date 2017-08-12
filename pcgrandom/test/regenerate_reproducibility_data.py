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
import os
import pkgutil

from pcgrandom.test.fingerprint import write_fingerprints


# Path to data file.
def reproducibility_filename():
    test_package_name = 'pcgrandom.test'
    test_package = pkgutil.get_loader(test_package_name).load_module(
        test_package_name)
    data_dir = os.path.join(os.path.dirname(test_package.__file__), 'data')
    return os.path.join(data_dir, 'generator_fingerprints.json')


# Generators used in reproducibility tests; short versions. Each
# of these strings is expanded into something exec-able.
_short_constructors = """\
pcgrandom.PCG_XSH_RR_V0(seed=12345)
pcgrandom.PCG_XSH_RR_V0(seed=12345, sequence=24)
pcgrandom.PCG_XSH_RR_V0(seed=u"noodleloaf".encode("utf-8"))
pcgrandom.PCG_XSH_RS_V0(seed=90210, sequence=-7)
pcgrandom.PCG_XSH_RS_V0(seed=\
    u"Το αεροστρωματόχημά μου είναι γεμάτο χέλια".encode("utf-8"))
pcgrandom.PCG_XSL_RR_V0(seed=41509)
pcgrandom.PCG_XSL_RR_V0(seed=-3, sequence=2**128 + 37)
pcgrandom.PCG_XSL_RR_V0(seed=b"i am \\x01 a byte \\x00\\xff string")
""".splitlines()


def constructors():
    for short_constructor in _short_constructors:
        yield """\
import pcgrandom
generator = {short_constructor}
""".format(short_constructor=short_constructor)


def regenerate_data_main():
    parser = argparse.ArgumentParser(
        description="Regenerate reproducibility data.",
    )
    parser.add_argument(
        "output",
        help="Output path to write the generated data to.",
    )

    args = parser.parse_args()

    write_fingerprints(
        constructors=constructors(),
        filename=args.output,
    )


if __name__ == '__main__':  # pragma: no cover
    regenerate_data_main()

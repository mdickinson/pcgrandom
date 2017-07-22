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
Code to generate a JSON "fingerprint" for a generator. This is used for
reproducibility testing, as well as checking portability of pickles.
"""
from pcgrandom.test.fingerprint import write_fingerprints
from pcgrandom.pcg_xsh_rr_v0 import PCG_XSH_RR_V0
from pcgrandom.pcg_xsl_rr_v0 import PCG_XSL_RR_V0


if __name__ == '__main__':
    write_fingerprints(
        generators=[
            PCG_XSH_RR_V0(seed=12345),
            PCG_XSL_RR_V0(seed=41509),
        ],
        filename='generator_fingerprints.json',
    )

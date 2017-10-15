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
Drop-in replacement for random.Random based on PCG-XSH-RR from
section 6.3.1 of the PCG paper.
"""

from pcgrandom.core_generators import xsh_rr_64_32
from pcgrandom.pcg_common import PCGCommon


class PCG_XSH_RR_V0(PCGCommon):
    """
    Random-like class based on Melissa O'Neill's PCG family.

    This implements the generator described in section 6.3.1 of the PCG paper,
    PCG-XSH-RR, sitting on a 64-bit LCG from Knuth.
    """
    # Version used to identify this generator in pickles and state tuples.
    VERSION = u"pcgrandom.PCG_XSH_RR_V0"

    # The core generator class.
    core_gen_class = xsh_rr_64_32

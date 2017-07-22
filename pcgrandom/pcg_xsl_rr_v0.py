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

from pcgrandom.pcg_common import PCGCommon as _PCGCommon

# Reference for multiplier: "Tables of linear congruential generators of
# different sizes and good lattice stucture", Pierre L'Ecuyer, Mathematics of
# Computation vol. 68, no. 225, January 1999, pp 249-260.

_UINT64_MASK = 2**64 - 1


def _rotate64(v, r):
    """
    An unsigned 64-bit bitwise "clockwise" rotation of r bits on v.

    If v has more than 64 bits, only the least significant 64 bits
    are used.

    Parameters
    ----------
    v : integer in range 0 <= v < 2**64
        The value to rotate.
    r : integer in the range 0 <= r < 64
        The number of bits to rotate by.

    Returns
    -------
    integer in range 0 <= v < 2**64
        Result of shifting v right by r places, rotating the
        bits that drop off back into the high end of v.
    """
    return (v >> r | v << (64-r)) & _UINT64_MASK


class PCG_XSL_RR_V0(_PCGCommon):
    """
    Random subclass based on Melissa O'Neill's PCG family.

    This implements the generator described in section 6.3.3 of the PCG paper,
    PCG-XSL-RR, sitting on a 128-bit LCG with multiplier from L'Ecuyer.
    """

    VERSION = u"pcgrandom.PCG_XSL_RR_V0"

    _state_bits = 128

    _output_bits = 64

    # Multiplier from Table 4 of L'Ecuyer's paper.
    _default_multiplier = 47026247687942121848144207491837523525

    # A somewhat arbitrary increment, chosen at random.
    _base_increment = 209568312854995847869081903677183368519

    def _get_output(self):
        """Compute output from current state."""
        state = self._state
        output_word = (state ^ (state >> 64)) & _UINT64_MASK
        return _rotate64(output_word, state >> 122)

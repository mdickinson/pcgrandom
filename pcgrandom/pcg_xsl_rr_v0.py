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


def _rotate64(v, r, _multiplier=2**64 + 1, _mask=2**64 - 1):
    """
    Unsigned 64-bit bitwise "clockwise" rotation.

    Extract the least significant 64 bits of *v*, shift them right
    by *r* bits, and move any bits shifted out into the vacated
    most significant bits of *v*.

    Parameters
    ----------
    v : Nonnegative integer.
        The value to rotate. Bits outside the 64 least significant
        bits are discarded before the rotation.
    r : integer in the range 0 <= r < 64
        The number of bits to rotate by.

    Returns
    -------
    integer in range 0 <= v < 2**64
        Result of the rotation.
    """
    return (v & _mask) * _multiplier >> r & _mask


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
        return _rotate64(state ^ (state >> 64), state >> 122)

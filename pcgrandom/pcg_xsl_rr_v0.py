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

from pcgrandom.pcg_common import PCGCommon


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


class PCG_XSL_RR_V0(PCGCommon):
    """
    Random subclass based on Melissa O'Neill's PCG family.

    This implements the generator described in section 6.3.3 of the PCG paper,
    PCG-XSL-RR, sitting on a 128-bit LCG with multiplier from L'Ecuyer.
    """

    VERSION = u"pcgrandom.PCG_XSL_RR_V0"

    _state_bits = 128

    _state_mask = 2**128 - 1

    _output_bits = 64

    # Multiplier from Table 4 of L'Ecuyer's paper.
    _default_multiplier = 47026247687942121848144207491837523525

    # Default increment from the PCG reference implementation.
    _default_increment = 117397592171526113268558934119004209487

    def _get_output(self):
        """Compute output from current state."""
        state = self._state
        return _rotate64(state ^ (state >> 64), state >> 122)

    def _next_output(self):
        """Return next output; advance the underlying LCG.
        """
        self._advance_state()
        output = self._get_output()
        return output

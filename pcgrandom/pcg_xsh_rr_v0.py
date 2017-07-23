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


def _rotate32(v, r, _multiplier=2**32 + 1, _mask=2**32 - 1):
    """
    Unsigned 32-bit bitwise "clockwise" rotation.

    Extract the least significant 32 bits of *v*, shift them right
    by *r* bits, and move any bits shifted out into the vacated
    most significant bits of *v*.

    Parameters
    ----------
    v : Nonnegative integer.
        The value to rotate. Bits outside the 32 least significant
        bits are discarded before the rotation.
    r : integer in the range 0 <= r < 32
        The number of bits to rotate by.

    Returns
    -------
    integer in range 0 <= v < 2**32
        Result of the rotation.
    """
    return (v & _mask) * _multiplier >> r & _mask


class PCG_XSH_RR_V0(_PCGCommon):
    """
    Random subclass based on Melissa O'Neill's PCG family.

    This implements the generator described in section 6.3.1 of the PCG paper,
    PCG-XSH-RR, sitting on a 64-bit LCG from Knuth.
    """

    VERSION = u"pcgrandom.PCG_XSH_RR_V0"

    _state_bits = 64

    _output_bits = 32

    # Multiplier reportedly used by Knuth for the MMIX LCG. Same as the
    # value used in the PCG reference implementation.
    _default_multiplier = 6364136223846793005

    # Increment reportedly used by Knuth for the MMIX LCG. Same as the
    # value used in the PCG reference implementation.
    _default_increment = 1442695040888963407

    def _get_output(self):
        """Compute output from current state."""
        state = self._state
        return _rotate32((state ^ (state >> 18)) >> 27, state >> 59)

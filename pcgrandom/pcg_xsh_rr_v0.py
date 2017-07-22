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

# XXX Make sure states can be transferred across Python versions (including
#     pickled states); how do we deal with the str / bytes mismatch?
# XXX fromstate constructor method? Or function, so that it can select
#     the appropriate class to use.
# XXX References: O'Neill, L'Ecuyer, Knuth MMIX.
# XXX Document reproducibility.
# XXX Document compatibility.
# XXX Support Python 2.6? 3.3?
# XXX Refactor tests: setUp to create generator (then tests that are common
#     to all generators can be moved to a mixin).
# XXX Fix use of __getstate__ and __reduce__.
# XXX Style: make exceptions consistent (capital letter, full stop).
# XXX Decide whether we really need the future dependency.
# XXX Mark the version strings explicitly as Unicode, for Python 2 / Python 3
#     compatibility.
# XXX Rework reproducibility tests: JSON format for the results might work.

from pcgrandom.pcg_common import PCGCommon as _PCGCommon


_UINT32_MASK = 2**32 - 1


def _rotate32(v, r):
    """
    An unsigned 32-bit bitwise "clockwise" rotation of r bits on v.

    If v has more than 32 bits, only the least significant 32 bits
    are used.

    Parameters
    ----------
    v : integer in range 0 <= v < 2**32
        The value to rotate.
    r : integer in the range 0 <= r < 32
        The number of bits to rotate by.

    Returns
    -------
    integer in range 0 <= v < 2**32
        Result of shifting v right by r places, rotating the
        bits that drop off back into the high end of v.
    """
    return (v >> r | v << (32-r)) & _UINT32_MASK


class PCG_XSH_RR_V0(_PCGCommon):
    """
    Random subclass based on Melissa O'Neill's PCG family.

    This implements the generator described in section 6.3.1 of the PCG paper,
    PCG-XSH-RR, sitting on a 64-bit LCG from Knuth.
    """

    VERSION = u"pcgrandom.PCG_XSH_RR_V0"

    _state_bits = 64

    _output_bits = 32

    # Multiplier reportedly used by Knuth for the MMIX LCG.
    _default_multiplier = 6364136223846793005

    # Increment reportedly used by Knuth for the MMIX LCG.
    _base_increment = 1442695040888963407

    def _get_output(self):
        """Compute output from current state."""
        state = self._state
        output_word = ((state ^ (state >> 18)) >> 27) & _UINT32_MASK
        return _rotate32(output_word, state >> 59)

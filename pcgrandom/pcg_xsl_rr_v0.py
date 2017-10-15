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

import operator

from builtins import object  # for proper handling of __next__ in Python 2

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


class xsl_rr_128_64(object):
    """
    Corresponds to the xsl_rr_128_64 family in the C++ implementation.
    """
    # Number of bits expected for the seed value.
    seed_bits = 128

    # Number of bits generated by each call to 'next'.
    output_bits = 64

    # Number of bits in the internal state.
    _state_bits = 128

    # Mask used for internal computations.
    _state_mask = ~(~0 << _state_bits)

    # Multiplier from Table 4 of L'Ecuyer's paper. Same as the value
    # used in the PCG reference implementation.
    _default_multiplier = 47026247687942121848144207491837523525

    # Default increment from the PCG reference implementation.
    _default_increment = 117397592171526113268558934119004209487

    def __init__(self, iseed, sequence=None, multiplier=None):
        if multiplier is None:
            multiplier = self._default_multiplier
        else:
            multiplier = operator.index(multiplier) & self._state_mask
            if multiplier % 4 != 1:
                raise ValueError("LCG multiplier must be of the form 4k+1")

        if sequence is None:
            increment = self._default_increment
        else:
            increment = 2 * operator.index(sequence) + 1 & self._state_mask

        # Choose initial state to match the PCG reference implementation.
        state = increment + iseed & self._state_mask
        state = state * multiplier + increment & self._state_mask

        self._multiplier = multiplier
        self._increment = increment
        self._state = state

    @classmethod
    def from_state(cls, state):
        multiplier, increment, state = state

        self = object.__new__(cls)
        self._multiplier = multiplier
        self._increment = increment
        self._state = state
        return self

    def __iter__(self):
        return self

    def __next__(self):
        """
        Get next output word from the core generator.
        """
        state = self._state
        self._state = state = (
            state * self._multiplier + self._increment) & self._state_mask
        output = _rotate64(state ^ (state >> 64), state >> 122)
        return output

    def advance(self, n):
        a, c = self._multiplier, self._increment
        m = (2**128 - 1)

        # Reduce n modulo the period of the sequence. This turns negative jumps
        # into positive ones.
        n &= m

        # Left-to-right binary powering algorithm.
        an, cn = 1, 0
        for bit in format(n, "b"):
            an, cn = an * an & m, an * cn + cn & m
            if bit == "1":
                an, cn = a * an & m, a * cn + c & m

        self._state = self._state * an + cn & m

    def getstate(self):
        return self._multiplier, self._increment, self._state


class PCG_XSL_RR_V0(PCGCommon):
    """
    Random subclass based on Melissa O'Neill's PCG family.

    This implements the generator described in section 6.3.1 of the PCG paper,
    PCG-XSL-RR, sitting on a 128-bit LCG.
    """
    # Version used to identify this generator in pickles and state tuples.
    VERSION = u"pcgrandom.PCG_XSL_RR_V0"

    # The core generator class.
    core_gen_class = xsl_rr_128_64

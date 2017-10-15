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

from pcgrandom.pcg_common import PCGCommon
from pcgrandom.seeding import seed_from_object, seed_from_system_entropy


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

    def __init__(self, multiplier, increment, state):
        self._multiplier = multiplier
        self._increment = increment
        self._state = state

    @classmethod
    def from_state(cls, state):
        multiplier, increment, state = state
        return cls(multiplier, increment, state)

    @classmethod
    def initial_state(cls, seed, sequence, multiplier):
        if multiplier is None:
            multiplier = cls._default_multiplier
        else:
            multiplier = operator.index(multiplier) & cls._state_mask
            if multiplier % 4 != 1:
                raise ValueError("LCG multiplier must be of the form 4k+1")

        if sequence is None:
            increment = cls._default_increment
        else:
            increment = 2 * operator.index(sequence) + 1 & cls._state_mask

        if seed is None:
            # XXX This part shouldn't be in this class ...
            iseed = seed_from_system_entropy(cls._state_bits)
        else:
            iseed = seed_from_object(seed, cls._state_bits)

        # Choose initial state to match the PCG reference implementation.
        state = increment + iseed & cls._state_mask
        state = state * multiplier + increment & cls._state_mask
        return multiplier, increment, state

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

    VERSION = u"pcgrandom.PCG_XSL_RR_V0"

    core_gen_class = xsl_rr_128_64

    _output_bits = core_gen_class.output_bits

    def __init__(self, seed=None, sequence=None, multiplier=None):
        initial_state = self.core_gen_class.initial_state(
            seed, sequence, multiplier)
        self._core_generator = self.core_gen_class.from_state(initial_state)
        self._set_distribution_state(self._initial_distribution_state())

    def jumpahead(self, n):
        self._core_generator.advance(n)

    def _next_output(self):
        return next(self._core_generator)

    def setstate(self, state):
        """Restore internal state from object returned by getstate()."""

        version, core_state, distribution_state = state
        if version != self.VERSION:
            raise ValueError(
                "State with version {0!r} passed to "
                "setstate() of version {1!r}.".format(version, self.VERSION)
            )
        self._core_generator = self.core_gen_class.from_state(core_state)
        self._set_distribution_state(distribution_state)

    def getstate(self):
        """Return internal state; can be passed to setstate() later."""
        distribution_state = self._get_distribution_state()
        return (
            self.VERSION, self._core_generator.getstate(), distribution_state)

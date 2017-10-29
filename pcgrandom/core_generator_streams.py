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
Output streams for the core PCG generators.
"""
import builtins


def _rotate32(v, r, _multiplier=2**32 + 1, _mask=2**32 - 1):
    """
    Unsigned 32-bit bitwise "clockwise" rotation.

    Extract the least significant 32 bits of *v*, shift them right
    by *r* bits, and move any bits shifted out into the vacated
    most significant bits of *v*.

    Parameters
    ----------
    v : integer
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


def _rotate64(v, r, _multiplier=2**64 + 1, _mask=2**64 - 1):
    """
    Unsigned 64-bit bitwise "clockwise" rotation.

    Extract the least significant 64 bits of *v*, shift them right
    by *r* bits, and move any bits shifted out into the vacated
    most significant bits of *v*.

    Parameters
    ----------
    v : integer
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


class _pcg_stream_base(builtins.object):
    """
    Base class for the various core generators.
    """
    def __init__(self, multiplier, increment, state):
        self._multiplier = multiplier
        self._increment = increment
        self._state = state

    @property
    def state(self):
        """
        Read-only access to the current stream state.
        """
        return self._state

    def __iter__(self):
        """
        Iterator protocol.
        """
        return self

    def __next__(self):
        """
        Iterator protocol: return next output word from the generator.
        """
        if self._output_previous:
            output = self._output()
            self.step()
        else:
            self.step()
            output = self._output()
        return output

    def step(self):
        """
        Advance the underlying LCG a single step.
        """
        a, c, m = self._multiplier, self._increment, self._state_mask
        self._state = self._state * a + c & m

    def advance(self, n):
        """
        Advance the underlying LCG by a given number of steps.
        """
        a, c, m = self._multiplier, self._increment, self._state_mask

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


class xsh_rr_64_32_stream(_pcg_stream_base):
    """
    Corresponds to the xsh_rr_64_32 family in the C++ implementation.
    """
    # Mask used for internal computations.
    _state_mask = ~(~0 << 64)

    # Whether to compute output before advancing state or not.
    _output_previous = True

    def _output(self):
        """
        Function that computes the output from the current state.
        """
        state = self._state
        return _rotate32((state ^ (state >> 18)) >> 27, state >> 59)


class xsh_rs_64_32_stream(_pcg_stream_base):
    """
    Corresponds to the xsh_rs_64_32 family in the C++ implementation.
    """
    # Mask used for internal computations.
    _state_mask = ~(~0 << 64)

    # Whether to compute output before advancing state or not.
    _output_previous = True

    def _output(self):
        """
        Function that computes the output from the current state.
        """
        state = self._state
        return ((state ^ (state >> 22)) >> (22 + (state >> 61))) & (2**32-1)


class xsl_rr_128_64_stream(_pcg_stream_base):
    """
    Corresponds to the xsl_rr_128_64 family in the C++ implementation.
    """
    # Mask used for internal computations.
    _state_mask = ~(~0 << 128)

    # Whether to compute output before advancing state or not.
    _output_previous = False

    def _output(self):
        """
        Function that computes the output from the current state.
        """
        state = self._state
        return _rotate64(state ^ (state >> 64), state >> 122)

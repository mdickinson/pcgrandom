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
The core PCG generators, as Python iterables.
"""
import operator

import builtins
import pkg_resources


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


class _pcg_core(builtins.object):
    """
    Code common to all the PCG core generators.

    Parameters
    ----------
    iseed : integer
        Seed value used to initialise the generator.
    sequence : integer-like, optional
        Sequence selector. This determines the increment of the underlying LCG.
        Any object that supports __index__ may be used here.
    multiplier : integer-like, optional
        Multiplier for the underlying LCG. This must be congruent to 1 modulo
        4. Any object that supports __index__ may be used here.

    """
    def __init__(self, sequence=None, multiplier=None):
        if multiplier is None:
            self._multiplier = self._default_multiplier
        else:
            self._multiplier = operator.index(multiplier) & self._state_mask
        if self._multiplier % 4 != 1:
            raise ValueError("LCG multiplier must be of the form 4k+1")

        if sequence is None:
            self._increment = self._default_increment
        else:
            self._increment = 2*operator.index(sequence) + 1 & self._state_mask

        self._state = 0

    @property
    def state(self):
        """
        Tuple that encapsulates the state of this generator.
        """
        return self.name, self._multiplier, self._increment, self._state

    @classmethod
    def from_state(cls, state):
        """
        Construct generator instance from saved state.
        """
        if state[0] != cls.name:
            raise ValueError(
                "Setting state of generator with name {!r} from "
                "a state tuple with incompatible name {!r} ".format(
                    cls.name, state[0])
            )

        self = object.__new__(cls)
        self._multiplier, self._increment, self._state = state[1:]
        return self

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

    def seed(self, iseed):
        """
        Set the initial state from an integer seed.
        """
        # Matches the PCG reference implementation.
        self._state = 0
        self.step()
        self._state = self._state + iseed & self._state_mask
        self.step()

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


class xsh_rr_64_32(_pcg_core):
    """
    Corresponds to the xsh_rr_64_32 family in the C++ implementation.
    """
    # Identifying name for generator. Used in entry-points and
    # when reconstructing a generator from its state tuple.
    name = u"xsh_rr_64_32"

    # Number of bits expected for the seed value.
    seed_bits = 64

    # Number of bits generated by each call to 'next'.
    output_bits = 32

    # Period of core LCG.
    period = 2**64

    # Mask used for internal computations.
    _state_mask = ~(~0 << 64)

    # Whether to compute output before advancing state or not.
    _output_previous = True

    # Multiplier reportedly used by Knuth for the MMIX LCG. Same as the
    # value used in the PCG reference implementation.
    _default_multiplier = 6364136223846793005

    # Increment reportedly used by Knuth for the MMIX LCG. Same as the
    # value used in the PCG reference implementation.
    _default_increment = 1442695040888963407

    def _output(self):
        """
        Function that computes the output from the current state.
        """
        state = self._state
        return _rotate32((state ^ (state >> 18)) >> 27, state >> 59)


class xsh_rs_64_32(_pcg_core):
    """
    Corresponds to the xsh_rs_64_32 family in the C++ implementation.
    """
    # Identifying name for generator. Used in entry-points and
    # when reconstructing a generator from its state tuple.
    name = u"xsh_rs_64_32"

    # Number of bits expected for the seed value.
    seed_bits = 64

    # Number of bits generated by each call to 'next'.
    output_bits = 32

    # Period of core LCG.
    period = 2**64

    # Mask used for internal computations.
    _state_mask = ~(~0 << 64)

    # Whether to compute output before advancing state or not.
    _output_previous = True

    # Multiplier reportedly used by Knuth for the MMIX LCG. Same as the
    # value used in the PCG reference implementation.
    _default_multiplier = 6364136223846793005

    # Increment reportedly used by Knuth for the MMIX LCG. Same as the
    # value used in the PCG reference implementation.
    _default_increment = 1442695040888963407

    def _output(self):
        """
        Function that computes the output from the current state.
        """
        state = self._state
        return ((state ^ (state >> 22)) >> (22 + (state >> 61))) & (2**32-1)


class xsl_rr_128_64(_pcg_core):
    """
    Corresponds to the xsl_rr_128_64 family in the C++ implementation.
    """
    # Identifying name for generator. Used in entry-points and
    # when reconstructing a generator from its state tuple.
    name = u"xsl_rr_128_64"

    # Number of bits expected for the seed value.
    seed_bits = 128

    # Number of bits generated by each call to 'next'.
    output_bits = 64

    # Period of core LCG.
    period = 2**128

    # Mask used for internal computations.
    _state_mask = ~(~0 << 128)

    # Multiplier from Table 4 of L'Ecuyer's paper. Same as the value
    # used in the PCG reference implementation.
    _default_multiplier = 47026247687942121848144207491837523525

    # Default increment from the PCG reference implementation.
    _default_increment = 117397592171526113268558934119004209487

    # Whether to compute output before advancing state or not.
    _output_previous = False

    def _output(self):
        """
        Function that computes the output from the current state.
        """
        state = self._state
        return _rotate64(state ^ (state >> 64), state >> 122)


def core_generator_from_state(state):
    """
    Reconstruct a core generator from its state tuple.

    Parameters
    ----------
    state : tuple
        Tuple obtained from the state property of a core generator.
    """
    name = state[0]

    entry_points = list(
        pkg_resources.iter_entry_points(
            group='pcgrandom.core_generators',
            name=name,
        )
    )
    if not entry_points:
        raise ValueError("Unable to find generator with name {}".format(name))
    # Log a warning if there's more than one?
    entry_point = entry_points[0]
    generator_class = entry_point.load()
    return generator_class.from_state(state)


class _pcg_factory(object):
    def __init__(self, sequence=None, multiplier=None):
        if multiplier is None:
            self._multiplier = self._default_multiplier
        else:
            self._multiplier = operator.index(multiplier) & self._state_mask
        if self._multiplier % 4 != 1:
            raise ValueError("LCG multiplier must be of the form 4k+1")

        if sequence is None:
            self._increment = self._default_increment
        else:
            self._increment = 2*operator.index(sequence) + 1 & self._state_mask


class xsh_rr_64_32_factory(_pcg_factory):
    # Number of bits expected for the seed value.
    seed_bits = 64

    # Multiplier reportedly used by Knuth for the MMIX LCG. Same as the
    # value used in the PCG reference implementation.
    _default_multiplier = 6364136223846793005

    # Increment reportedly used by Knuth for the MMIX LCG. Same as the
    # value used in the PCG reference implementation.
    _default_increment = 1442695040888963407

    # Mask used for internal computations.
    _state_mask = ~(~0 << 64)

    def __call__(self, seed):
        state = xsh_rr_64_32.name, self._multiplier, self._increment, 0
        gen = xsh_rr_64_32.from_state(state)
        gen.seed(seed)
        return gen


class xsh_rs_64_32_factory(_pcg_factory):
    # Number of bits expected for the seed value.
    seed_bits = 64

    # Multiplier reportedly used by Knuth for the MMIX LCG. Same as the
    # value used in the PCG reference implementation.
    _default_multiplier = 6364136223846793005

    # Increment reportedly used by Knuth for the MMIX LCG. Same as the
    # value used in the PCG reference implementation.
    _default_increment = 1442695040888963407

    # Mask used for internal computations.
    _state_mask = ~(~0 << 64)

    def __call__(self, seed):
        state = xsh_rs_64_32.name, self._multiplier, self._increment, 0
        gen = xsh_rs_64_32.from_state(state)
        gen.seed(seed)
        return gen


class xsl_rr_128_64_factory(_pcg_factory):
    # Number of bits expected for the seed value.
    seed_bits = 128

    # Multiplier from Table 4 of L'Ecuyer's paper. Same as the value
    # used in the PCG reference implementation.
    _default_multiplier = 47026247687942121848144207491837523525

    # Default increment from the PCG reference implementation.
    _default_increment = 117397592171526113268558934119004209487

    # Mask used for internal computations.
    _state_mask = ~(~0 << 128)

    def __call__(self, seed):
        state = xsl_rr_128_64.name, self._multiplier, self._increment, 0
        gen = xsl_rr_128_64.from_state(state)
        gen.seed(seed)
        return gen

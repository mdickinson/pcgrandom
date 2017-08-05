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
Common base class for the various PCG implementations.
"""
from __future__ import division

import hashlib
import operator
import os

# Python 2 compatibility.
from builtins import int as _int, range
from past.builtins import unicode

from pcgrandom.distributions import Distributions


def seed_from_system_entropy(bits):
    """
    Create a new integer seed from whatever entropy we can find.

    Parameters
    ----------
    bits : nonnegative integer
        Number of bits we need.

    Returns
    -------
    seed : integer
        Integer seed in the range 0 <= seed < 2**bits.
    """
    numbytes, excess = -(-bits // 8), -bits % 8
    seed = _int.from_bytes(os.urandom(numbytes), byteorder="big")
    return seed >> excess


def seed_from_object(obj, bits):
    """
    Create a new integer seed from the given Python object, in
    a reproducible manner.

    Parameters
    ----------
    obj : object
        The object to use to create the seed.
    bits : nonnegative integer.
        Number of bits needed for the seed. This function can produce
        a maximum of 512 bits from a Unicode or string object.

    Returns
    -------
    seed : integer
        Integer seed in the range 0 <= seed < 2**bits.
    """
    # From an integer-like.
    try:
        obj_as_integer = operator.index(obj)
    except TypeError:
        pass
    else:
        seed_mask = ~(~0 << bits)
        seed = obj_as_integer & seed_mask
        return seed

    # For a Unicode or byte string.
    if isinstance(obj, unicode):
        obj = obj.encode('utf-8')

    if isinstance(obj, bytes):
        obj_hash = hashlib.sha512(obj).digest()
        numbytes, excess = -(-bits // 8), -bits % 8

        if numbytes > len(obj_hash):
            raise ValueError(
                "Cannot provide more than {} bits of seed.".format(
                    8 * len(obj_hash)))

        seed = _int.from_bytes(obj_hash[:numbytes], byteorder="big") >> excess
        return seed

    raise TypeError(
        "Unable to create seed from object of type {}. "
        "Please use an integer, bytestring or Unicode string.".format(
            type(obj))
    )


class PCGCommon(Distributions):
    """
    Common base class for the PCG random generators.
    """
    def __init__(self, seed=None, sequence=None, multiplier=None):
        if multiplier is None:
            multiplier = self._default_multiplier
        multiplier = operator.index(multiplier) & self._state_mask

        if sequence is None:
            increment = self._default_increment
        else:
            sequence = operator.index(sequence) & self._state_mask
            increment = 2 * sequence + 1 & self._state_mask

        # The multiplier must be congruent to 1 modulo 4 to achieve
        # full period. (Hull-Dobell theorem.)
        if multiplier % 4 != 1:
            raise ValueError("LCG multiplier must be of the form 4k+1.")

        self._multiplier = multiplier
        self._increment = increment
        self.seed(seed)

    def __getstate__(self):
        return self.getstate()

    def __setstate__(self, state):
        self.setstate(state)

    def seed(self, seed=None):
        """Initialize internal state from hashable object.
        """
        if seed is None:
            integer_seed = seed_from_system_entropy(self._state_bits)
        else:
            integer_seed = seed_from_object(seed, self._state_bits)

        self._set_state_from_seed(integer_seed)
        self.gauss_next = None

    def getstate(self):
        """Return internal state; can be passed to setstate() later."""
        parameters = self._multiplier, self._increment
        return self.VERSION, parameters, self._state, self.gauss_next

    def setstate(self, state):
        """Restore internal state from object returned by getstate()."""
        version = state[0]
        if version != self.VERSION:
            raise ValueError(
                "State with version {0!r} passed to "
                "setstate() of version {1!r}.".format(version, self.VERSION)
            )

        parameters, state, gauss_next = state[1:]
        self.gauss_next = gauss_next
        self._state = state
        self._multiplier, self._increment = parameters

    def getrandbits(self, k):
        """Generate an integer in the range [0, 2**k).

        Parameters
        ----------
        k : nonnegative integer

        """
        k = operator.index(k)
        if k < 0:
            raise ValueError("Number of bits should be nonnegative.")

        output_bits = self._output_bits

        numwords, excess_bits = -(-k // output_bits), -k % output_bits
        acc = 0
        for _ in range(numwords):
            acc = acc << output_bits | self._next_output()
        # int call converts small longs to ints on Python 2.
        return int(acc >> excess_bits)

    def random(self):
        """Get the next random number in the range [0.0, 1.0)."""
        return self.getrandbits(53)/9007199254740992

    def _randbelow(self, n):
        """Return a random integer in range(n)."""
        output_bits = self._output_bits
        # Invariant: x is uniformly distributed in range(h).
        x, h = 0, 1
        while True:
            q, r = divmod(h, n)
            if r <= x:
                # int call converts small longs to ints on Python 2.
                return int((x - r) // q)
            x, h = x << output_bits | self._next_output(), r << output_bits

    def _advance_state(self):
        """Advance the underlying LCG a single step."""
        self._state = (
            self._state * self._multiplier + self._increment
            & self._state_mask
        )

    def _set_state_from_seed(self, seed):
        """Initialize generator from a given seed.

        Parameters
        ----------
        seed : int
            An integer seed to use to prime the generator.
        """
        seed &= self._state_mask

        self._state = 0
        self._next_output()
        self._state = (self._state + seed) & self._state_mask
        self._next_output()

    def jumpahead(self, n):
        """Jump ahead or back in the sequence of random numbers."""

        a, c, m = self._multiplier, self._increment, self._state_mask

        # Reduce n modulo the period of the sequence. Note that this
        # turns negative jumps into positive ones.
        n &= m

        # Left-to-right binary powering algorithm.
        an, cn = 1, 0
        for bit in format(n, "b"):
            an, cn = an * an & m, an * cn + cn & m
            if bit == "1":
                an, cn = a * an & m, a * cn + c & m

        self._state = self._state * an + cn & m

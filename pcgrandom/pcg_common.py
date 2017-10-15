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

import operator

# Python 2 compatibility.
from builtins import range

from pcgrandom.distributions import Distributions
from pcgrandom.seeding import seed_from_object, seed_from_system_entropy


class PCGCommon(Distributions):
    """
    Common base class for the PCG random generators.
    """
    def __init__(self, seed=None, sequence=None, multiplier=None):
        initial_state = self.core_gen_class.initial_state(
            seed, sequence, multiplier)
        self._core_generator = self.core_gen_class.from_state(initial_state)
        self._set_distribution_state(self._initial_distribution_state())

    def seed(self, seed=None, sequence=None, multiplier=None):
        """(Re)initialize internal state from integer or string object."""
        self.__init__(seed, sequence, multiplier)

    def jumpahead(self, n):
        """Jump ahead or back in the sequence of random numbers."""
        self._core_generator.advance(n)

    # The underlying linear congruential generator.

    def _get_core_state(self):
        """
        Get the state for the core generator.
        """
        return self._multiplier, self._increment, self._state

    def _set_core_state(self, state):
        """
        Set the state for the core generator.
        """
        self._multiplier, self._increment, self._state = state

    def _step_state(self):
        """Advance the underlying LCG a single step."""
        self._state = (
            self._state * self._multiplier + self._increment
            & self._state_mask
        )

    def _advance_state(self, n):
        """Advance the underlying LCG a given number of steps."""

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

    # XXX Remove this function? What do we need it for?

    def _next_output(self):
        """Return next output and advance the underlying LCG."""
        return next(self._core_generator)

    # State management and pickling.

    def getstate(self):
        """Return internal state; can be passed to setstate() later."""
        distribution_state = self._get_distribution_state()
        return (
            self.VERSION, self._core_generator.getstate(), distribution_state)

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

    def __getstate__(self):
        return self.getstate()

    def __setstate__(self, state):
        self.setstate(state)

    # Core sampling functions.

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

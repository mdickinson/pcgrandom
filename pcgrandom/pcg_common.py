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
from pcgrandom.seeding import seed_from_object


class PCGCommon(Distributions):
    """
    Common base class for the PCG random generators.

    Parameters
    ----------
    core_generator : object
        Object providing the core generator. Supports the iterator
        protocol, along with various other methods.
    seed : integer-like or bytes-like, optional
        Python object to use to seed the generator. May be an integer-like
        (something supporting the __index__ method), or bytes-like (anything
        supporting the buffer protocol). If not given, the generator is seeded
        from system entropy.
    """
    def __init__(self, core_generator, seed=None):
        self._core_generator = core_generator
        self.seed(seed)

    def seed(self, seed=None):
        """(Re)initialize internal state from integer or string object."""
        iseed = seed_from_object(seed, self._core_generator.seed_bits)
        self._core_generator.seed(iseed)
        self._set_distribution_state(self._initial_distribution_state())

    def jumpahead(self, n):
        """Jump ahead or back in the sequence of random numbers."""
        self._core_generator.advance(n)

    # State management.

    def getstate(self):
        """Return internal state; can be passed to setstate() later."""
        core_state = self._core_generator.get_state()
        distribution_state = self._get_distribution_state()
        return self._core_generator.VERSION, core_state, distribution_state

    def setstate(self, state):
        """Restore internal state from object returned by getstate()."""
        version, core_state, distribution_state = state
        if version != self._core_generator.VERSION:
            raise ValueError(
                "State with version {0!r} passed to "
                "setstate() of version {1!r}.".format(
                    version, self._core_generator.VERSION)
            )
        self._core_generator.set_state(core_state)
        self._set_distribution_state(distribution_state)

    # Core sampling functions.

    def _randbelow(self, n):
        """Return a random integer in range(n)."""
        output_bits = self._core_generator.output_bits
        # Invariant: x is uniformly distributed in range(h).
        x, h = 0, 1
        while True:
            q, r = divmod(h, n)
            if r <= x:
                # int call converts small longs to ints on Python 2.
                return int((x - r) // q)
            output = next(self._core_generator)
            x, h = x << output_bits | output, r << output_bits

    def getrandbits(self, k):
        """Generate an integer in the range [0, 2**k).

        Parameters
        ----------
        k : nonnegative integer

        """
        k = operator.index(k)
        if k < 0:
            raise ValueError("Number of bits should be nonnegative.")

        output_bits = self._core_generator.output_bits

        numwords, excess_bits = -(-k // output_bits), -k % output_bits
        acc = 0
        for _ in range(numwords):
            output = next(self._core_generator)
            acc = acc << output_bits | output
        # int call converts small longs to ints on Python 2.
        return int(acc >> excess_bits)

    def random(self):
        """Get the next random number in the range [0.0, 1.0)."""
        return self.getrandbits(53)/9007199254740992

"""
Common base class for the various PCG implementations.
"""
from __future__ import division

import bisect as _bisect
import collections as _collections
import operator as _operator
import os as _os
import random as _random

from builtins import int as _int, range as _range


class PCGCommon(_random.Random):
    """
    Common base class for the PCG random generators.
    """
    def __init__(self, seed=None, sequence=0):
        self._state_mask = ~(-1 << self._state_bits)
        sequence = _operator.index(sequence) & self._state_mask
        self._increment = (
            2 * sequence + self._base_increment
            & self._state_mask
        )
        self.seed(seed)

    def seed(self, seed=None):
        """Initialize internal state from hashable object.
        """
        # XXX Compatibility note: unlike the base Random generator, we don't
        # permit seeding from an arbitrary hashable object, since that makes it
        # harder to guarantee reproducibility in the case that the hash
        # changes.  See also http://bugs.python.org/issue27706.
        if seed is None:
            nbytes = self._state_bits // 8
            seed = _int.from_bytes(_os.urandom(nbytes), byteorder='little')
        else:
            seed = _operator.index(seed)

        self._set_state_from_seed(seed)
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
                "state with version {0!r} passed to "
                "setstate() of version {1!r}".format(version, self.VERSION)
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
        # XXX Compatibility note: k=0 is accepted.

        k = _operator.index(k)
        if k < 0:
            raise ValueError("Number of bits should be nonnegative.")

        output_bits = self._output_bits

        numwords, excess_bits = -(-k // output_bits), -k % output_bits
        acc = 0
        for _ in _range(numwords):
            acc = acc << output_bits | self._next_word()
        return acc >> excess_bits

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
                return (x - r) // q
            x, h = x << output_bits | self._next_word(), r << output_bits

    def randrange(self, start, stop=None, step=None):
        """Choose a random item from range(start, stop[, step]).

        """
        # Reimplemented from the base class to ensure reproducibility
        # across Python versions. The code below is adapted from that
        # in Python 3.6.

        # XXX Compatibility: randrange accepts numpy ints.
        # XXX Compatibility: randrange does not accept floats;
        #     an attempt to pass a float (integral or not) raises
        #     TypeError. (For Random, it raises ValueError for non-integral
        #     floats and is accepted for integral floats.) Similarly,
        #     Decimal objects aren't supported.

        istart = _operator.index(start)
        if stop is None:
            if istart > 0:
                return self._randbelow(istart)
            else:
                raise ValueError(
                    "empty range for randrange({0})".format(istart))

        istop = _operator.index(stop)
        width = istop - istart
        if step is None:
            if width > 0:
                return istart + self._randbelow(width)
            else:
                raise ValueError(
                    "empty range for randrange({0}, {1})".format(
                        istart, istop))

        istep = _operator.index(step)
        if istep == 0:
            raise ValueError("zero step for randrange()")
        n = -(-width // istep)
        if n > 0:
            return istart + istep * self._randbelow(n)
        else:
            raise ValueError(
                "empty range for randrange({0}, {1}, {2})".format(
                    istart, istop, istep))

    def _advance_state(self):
        """Advance the underlying LCG a single step."""
        self._state = (
            self._state * self._multiplier + self._increment
            & self._state_mask
        )

    def _next_word(self):
        """Return next output; advance the underlying LCG.
        """
        output = self._get_output()
        self._advance_state()
        return output

    def _set_state_from_seed(self, seed):
        """Initialize generator from a given seed.

        Parameters
        ----------
        seed : int
            An integer seed to use to prime the generator.
        """
        seed &= self._state_mask

        self._state = 0
        self._next_word()
        self._state = (self._state + seed) & self._state_mask
        self._next_word()

    def jumpahead(self, n):
        """Jump ahead or back in the sequence of random numbers."""

        a, c, m = self._multiplier, self._increment, self._state_mask

        # Reduce n modulo the period of the sequence. Note that this
        # turns negative jumps into positive ones.
        n &= m

        # Left-to-right binary powering algorithm.
        an, cn = 1, 0
        for bit in format(n, 'b'):
            an, cn = an * an & m, an * cn + cn & m
            if bit == '1':
                an, cn = a * an & m, a * cn + c & m

        self._state = self._state * an + cn & m

    # sequence methods

    def choice(self, seq):
        """Choose a random element from a non-empty sequence."""
        n = len(seq)
        if n == 0:
            raise IndexError("Cannot choose from an empty sequence")
        return seq[self._randbelow(n)]

    def shuffle(self, x):
        """Shuffle list x in place, and return None."""
        # XXX Compatibility note: shuffle does not support the
        # second 'random' argument.

        n = len(x)
        for i in reversed(_range(n)):
            j = i + self._randbelow(n - i)
            if j > i:
                x[i], x[j] = x[j], x[i]

    def sample(self, population, k):
        """Chooses k unique random elements from a population sequence or set.

        Returns a new list containing elements from the population while
        leaving the original population unchanged.  The resulting list is
        in selection order so that all sub-slices will also be valid random
        samples.  This allows raffle winners (the sample) to be partitioned
        into grand prize and second place winners (the subslices).

        Members of the population need not be hashable or unique.  If the
        population contains repeats, then each occurrence is a possible
        selection in the sample.

        To choose a sample in a range of integers, use range as an argument.
        This is especially fast and space efficient for sampling from a
        large population:   sample(range(10000000), 60)
        """
        if isinstance(population, _collections.Set):
            population = tuple(population)
        if not isinstance(population, _collections.Sequence):
            raise TypeError(
                "Population must be a sequence or set.  "
                "For dicts, use list(d).")

        n = len(population)
        if not 0 <= k <= n:
            raise ValueError("Sample larger than population, or negative.")

        # Algorithm based on one attributed to Robert Floyd, and appearing in
        # "More Programming Pearls", by Jon Bentley.  See also the post to
        # python-list dated May 28th 2010, entitled "A Friday Python
        # Programming Pearl: random sampling".
        d = {}
        for i in reversed(_range(k)):
            j = i + self._randbelow(n - i)
            if j in d:
                d[i] = d[j]
            d[j] = i

        result = [None] * k
        for j, i in d.items():
            result[i] = population[j]
        return result

    def choices(self, population, weights=None, cum_weights=None, k=1):
        """Return k-sized list of population elements chosen with replacement.

        If the relative weights or cumulative weights are not specified,
        the selections are made with equal probability.

        """
        # XXX Compatibility note: cum_weights can be passed by position, but
        # please don't. This is only for Python 2 support.
        # XXX Compatibility note: if the sum of the weights is zero, a
        # ValueError is raised rather than an IndexError.
        # XXX Compatibility note: an IndexError is raised for an empty
        # population, even if k=0.

        # Code modified to remove the possibility of IndexError due to double
        # rounding or subnormal weights. See http://bugs.python.org/issue24567

        if cum_weights is None:
            if weights is None:
                if len(population) == 0:
                    raise IndexError("Cannot choose from an empty population")
                return [self.choice(population) for _ in _range(k)]
            cum_weights, acc = [], 0
            for weight in weights:
                acc += weight
                cum_weights.append(acc)
        elif weights is not None:
            raise TypeError(
                "Cannot specify both weights and cumulative weights")

        if len(population) == 0:
            raise IndexError("Cannot choose from an empty population")
        if len(cum_weights) != len(population):
            raise ValueError(
                "The number of weights does not match the population")
        total = cum_weights[-1]
        if total == 0:
            raise ValueError(
                "The total weight must be strictly positive.")
        bisectors = [weight / total for weight in cum_weights]

        # Note: a priori, the bisect call's return value could be
        # len(population), which would cause an IndexError in the population
        # lookup. However, that shouldn't happen: self.random() is strictly
        # less than 1.0, and bisectors[-1] == 1.0, so the result of the bisect
        # call should always be strictly smaller than len(population).
        return [
            population[_bisect.bisect(bisectors, self.random())]
            for _ in range(k)
        ]

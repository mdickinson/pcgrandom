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
Mixin class providing various distributions.
"""
# The methods in this class are copied almost verbatim from Python's random
# module.
from __future__ import division

import bisect
import collections
from math import acos, cos, e, exp, log, pi, sin, sqrt
import operator

from builtins import range


NV_MAGICCONST = 4 * exp(-0.5)/sqrt(2.0)
TWOPI = 2.0*pi
LOG4 = log(4.0)
SG_MAGICCONST = 1.0 + log(4.5)


class Distributions(object):
    """
    Mixin class to be used with a PRNG, providing various distributions.

    The target class for this mixin should provide the core generator
    methods ``random`` and ``_randbelow``. The class also depends
    on the state in self.gauss_next.
    """
    # Integer distributions

    def randrange(self, start, stop=None, step=None):
        """Choose a random item from range(start, stop[, step]).

        """
        # Reimplemented from the base class to ensure reproducibility
        # across Python versions. The code below is adapted from that
        # in Python 3.6.
        istart = operator.index(start)
        if stop is None:
            if istart > 0:
                return self._randbelow(istart)
            else:
                raise ValueError(
                    "Empty range for randrange({0}).".format(istart))

        istop = operator.index(stop)
        width = istop - istart
        if step is None:
            if width > 0:
                return istart + self._randbelow(width)
            else:
                raise ValueError(
                    "Empty range for randrange({0}, {1}).".format(
                        istart, istop))

        istep = operator.index(step)
        if istep == 0:
            raise ValueError("Zero step for randrange().")
        n = -(-width // istep)
        if n > 0:
            return istart + istep * self._randbelow(n)
        else:
            raise ValueError(
                "Empty range for randrange({0}, {1}, {2}).".format(
                    istart, istop, istep))

    def randint(self, a, b):
        """Return random integer in range [a, b], including both end points.
        """
        istart = operator.index(a)
        width = operator.index(b) - istart + 1
        if width > 0:
            return istart + self._randbelow(width)
        else:
            raise ValueError(
                "Empty range for randint({0}, {1}).".format(a, b))

    # Shuffling and selection

    def choice(self, seq):
        """Choose a random element from a non-empty sequence."""
        n = len(seq)
        if n == 0:
            raise IndexError("Cannot choose from an empty sequence.")
        return seq[self._randbelow(n)]

    def shuffle(self, x):
        """Shuffle list x in place, and return None."""
        n = len(x)
        for i in reversed(range(n)):
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
        if isinstance(population, collections.Set):
            population = tuple(population)
        if not isinstance(population, collections.Sequence):
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
        for i in reversed(range(k)):
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

        The ``cum_weights`` and ``k`` arguments should be considered
        keyword-only. Regrettably, this can't be enforced in Python
        2-compatible code.
        """
        # Code modified to remove the possibility of IndexError due to double
        # rounding or subnormal weights. See http://bugs.python.org/issue24567
        if cum_weights is None:
            if weights is None:
                n = len(population)
                if n == 0:
                    raise IndexError("Cannot choose from an empty population.")
                return [population[self._randbelow(n)] for _ in range(k)]
            cum_weights, acc = [], 0
            for weight in weights:
                acc += weight
                cum_weights.append(acc)
        elif weights is not None:
            raise TypeError(
                "Cannot specify both weights and cumulative weights.")

        if len(population) == 0:
            raise IndexError("Cannot choose from an empty population.")
        if len(cum_weights) != len(population):
            raise ValueError(
                "The number of weights does not match the population.")
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
            population[bisect.bisect(bisectors, self.random())]
            for _ in range(k)
        ]

    # Continuous distributions

    def uniform(self, a, b):
        """Random number in the range [a, b) or [a, b] depending on rounding.
        """
        return a + (b-a) * self.random()

    def triangular(self, low=0.0, high=1.0, mode=None):
        """Triangular distribution.

        Continuous distribution bounded by given lower and upper limits,
        and having a given mode value in-between.

        http://en.wikipedia.org/wiki/Triangular_distribution

        """
        u = self.random()
        try:
            c = 0.5 if mode is None else (mode - low) / (high - low)
        except ZeroDivisionError:
            return low
        if u > c:
            u = 1.0 - u
            c = 1.0 - c
            low, high = high, low
        return low + (high - low) * (u * c) ** 0.5

    def normalvariate(self, mu, sigma):
        """Normal distribution.

        mu is the mean, and sigma is the standard deviation.

        """
        # mu = mean, sigma = standard deviation

        # Uses Kinderman and Monahan method. Reference: Kinderman,
        # A.J. and Monahan, J.F., "Computer generation of random
        # variables using the ratio of uniform deviates", ACM Trans
        # Math Software, 3, (1977), pp257-260.

        random = self.random
        while 1:
            u1 = random()
            u2 = 1.0 - random()
            z = NV_MAGICCONST*(u1-0.5)/u2
            zz = z*z/4.0
            if zz <= -log(u2):
                break
        return mu + z*sigma

    def lognormvariate(self, mu, sigma):
        """Log normal distribution.

        If you take the natural logarithm of this distribution, you'll get a
        normal distribution with mean mu and standard deviation sigma.
        mu can have any value, and sigma must be greater than zero.

        """
        return exp(self.normalvariate(mu, sigma))

    def expovariate(self, lambd):
        """Exponential distribution.

        lambd is 1.0 divided by the desired mean.  It should be
        nonzero.  (The parameter would be called "lambda", but that is
        a reserved word in Python.)  Returned values range from 0 to
        positive infinity if lambd is positive, and from negative
        infinity to 0 if lambd is negative.

        """
        # lambd: rate lambd = 1/mean
        # ('lambda' is a Python reserved word)

        # we use 1-random() instead of random() to preclude the
        # possibility of taking the log of zero.
        return -log(1.0 - self.random())/lambd

    def vonmisesvariate(self, mu, kappa):
        """Circular data distribution.

        mu is the mean angle, expressed in radians between 0 and 2*pi, and
        kappa is the concentration parameter, which must be greater than or
        equal to zero.  If kappa is equal to zero, this distribution reduces
        to a uniform random angle over the range 0 to 2*pi.

        """
        # mu:    mean angle (in radians between 0 and 2*pi)
        # kappa: concentration parameter kappa (>= 0)
        # if kappa = 0 generate uniform random angle

        # Based upon an algorithm published in: Fisher, N.I.,
        # "Statistical Analysis of Circular Data", Cambridge
        # University Press, 1993.

        # Thanks to Magnus Kessler for a correction to the
        # implementation of step 4.

        random = self.random
        if kappa <= 1e-6:
            return TWOPI * random()

        s = 0.5 / kappa
        r = s + sqrt(1.0 + s * s)

        while 1:
            u1 = random()
            z = cos(pi * u1)

            d = z / (r + z)
            u2 = random()
            if u2 < 1.0 - d * d or u2 <= (1.0 - d) * exp(d):
                break

        q = 1.0 / r
        f = (q + z) / (1.0 + q * z)
        u3 = random()
        if u3 > 0.5:
            theta = (mu + acos(f)) % TWOPI
        else:
            theta = (mu - acos(f)) % TWOPI

        return theta

    def gammavariate(self, alpha, beta):
        """Gamma distribution.  Not the gamma function!

        Conditions on the parameters are alpha > 0 and beta > 0.

        The probability distribution function is:

                    x ** (alpha - 1) * math.exp(-x / beta)
          pdf(x) =  --------------------------------------
                      math.gamma(alpha) * beta ** alpha

        """

        # alpha > 0, beta > 0, mean is alpha*beta, variance is alpha*beta**2

        # Warning: a few older sources define the gamma distribution in terms
        # of alpha > -1.0
        if alpha <= 0.0 or beta <= 0.0:
            raise ValueError('gammavariate: alpha and beta must be > 0.0')

        random = self.random
        if alpha > 1.0:

            # Uses R.C.H. Cheng, "The generation of Gamma
            # variables with non-integral shape parameters",
            # Applied Statistics, (1977), 26, No. 1, p71-74

            ainv = sqrt(2.0 * alpha - 1.0)
            bbb = alpha - LOG4
            ccc = alpha + ainv

            while 1:
                u1 = random()
                if not 1e-7 < u1 < .9999999:
                    continue
                u2 = 1.0 - random()
                v = log(u1/(1.0-u1))/ainv
                x = alpha*exp(v)
                z = u1*u1*u2
                r = bbb+ccc*v-x
                if r + SG_MAGICCONST - 4.5*z >= 0.0 or r >= log(z):
                    return x * beta

        elif alpha == 1.0:
            # expovariate(1/beta)
            return -log(1.0 - random()) * beta

        else:   # alpha is between 0 and 1 (exclusive)

            # Uses ALGORITHM GS of Statistical Computing - Kennedy & Gentle

            while 1:
                u = random()
                b = (e + alpha)/e
                p = b*u
                if p <= 1.0:
                    x = p ** (1.0/alpha)
                else:
                    x = -log((b-p)/alpha)
                u1 = random()
                if p > 1.0:
                    if u1 <= x ** (alpha - 1.0):
                        break
                elif u1 <= exp(-x):
                    break
            return x * beta

    def gauss(self, mu, sigma):
        """Gaussian distribution.

        mu is the mean, and sigma is the standard deviation.  This is
        slightly faster than the normalvariate() function.

        Not thread-safe without a lock around calls.

        """

        # When x and y are two variables from [0, 1), uniformly
        # distributed, then
        #
        #    cos(2*pi*x)*sqrt(-2*log(1-y))
        #    sin(2*pi*x)*sqrt(-2*log(1-y))
        #
        # are two *independent* variables with normal distribution
        # (mu = 0, sigma = 1).
        # (Lambert Meertens)
        # (corrected version; bug discovered by Mike Miller, fixed by LM)

        # Multithreading note: When two threads call this function
        # simultaneously, it is possible that they will receive the
        # same return value.  The window is very small though.  To
        # avoid this, you have to use a lock around all calls.  (I
        # didn't want to slow this down in the serial case by using a
        # lock here.)

        random = self.random
        z = self.gauss_next
        self.gauss_next = None
        if z is None:
            x2pi = random() * TWOPI
            g2rad = sqrt(-2.0 * log(1.0 - random()))
            z = cos(x2pi) * g2rad
            self.gauss_next = sin(x2pi) * g2rad

        return mu + z*sigma

    def betavariate(self, alpha, beta):
        """Beta distribution.

        Conditions on the parameters are alpha > 0 and beta > 0.
        Returned values range between 0 and 1.

        """

        # This version due to Janne Sinkkonen, and matches all the std
        # texts (e.g., Knuth Vol 2 Ed 3 pg 134 "the beta distribution").
        y = self.gammavariate(alpha, 1.0)
        if y == 0:
            return 0.0
        else:
            return y / (y + self.gammavariate(beta, 1.0))

    def paretovariate(self, alpha):
        """Pareto distribution.  alpha is the shape parameter."""
        # Jain, pg. 495

        u = 1.0 - self.random()
        return 1.0 / u ** (1.0/alpha)

    def weibullvariate(self, alpha, beta):
        """Weibull distribution.

        alpha is the scale parameter and beta is the shape parameter.

        """
        # Jain, pg. 499; bug fix courtesy Bill Arms

        u = 1.0 - self.random()
        return alpha * (-log(u)) ** (1.0/beta)

|build-status| |coverage|

The **pcgrandom** package provides a drop-in replacement for Python's default
random number generator based on the PCG family of PRNGs described by Melissa
O'Neill.

Features
--------
- Provides a collection of different generators with varying characteristics
  from the PCG family.
- API compatible with the standard library ``random`` module.
- Strong reproducibility guarantee across platforms, Python versions and
  ``pcgrandom`` releases.
- Support for multiple independent streams of random numbers.
- Support for advancing the underlying generator by a given number of steps
  (``jumpahead``).


API compatibility
-----------------
In the simplest case, the package can be used as a drop-in replacement for
``random.Random``: just replace all your ``random`` imports with imports from
``pcgrandom``. For example::

    >>> from pcgrandom import Random
    >>> gen = Random(seed=54321)
    >>> [gen.randrange(100) for _ in range(10)]
    [72, 24, 66, 75, 3, 93, 84, 82, 91, 54]
    >>> gen.normalvariate(10.0, 1.5)
    10.671673435755453
    >>> gen.random()
    0.49096851300833144

As with the ``random`` module, a ``Random`` instance is created at import time,
and its methods made immediately available in ``pcgrandom``::

    >>> from pcgrandom import random, randint
    >>> random()
    0.8538476833982533
    >>> randint(1, 6)  # roll a die
    5


Available generators
--------------------
A number of generators from the PCG family are available.

- ``PCG_XSH_RR_V0`` is a generator with 32-bit output and a 64-bit state.
- ``PCG_XSH_RS_V0`` is another generator with 32-bit output and 64-bit state.
  It has slightly different characteristics from ``PCG_XSH_RR_V0``: improved
  performance, but weaker statistical guarantees.
- ``PCG_XSL_RR_V0`` has 64-bit output and 128-bit state.

Each of these generators has the same API as ``random.Random``, and can be
imported directly from the ``pcgrandom`` module::

    >>> from pcgrandom import PCG_XSH_RR_V0
    >>> gen = PCG_XSH_RR_V0(seed=67182)
    >>> ''.join(gen.choice('0123456789') for _ in range(20))
    '15183975423492044867'


Reproducibility guarantees
--------------------------
If you try the example immediately above, you'll get *exactly* the same output
string: ``'15183975423492044867'``, regardless of your platform, Python
version, or ``pcgrandom`` package version.

For a given concrete generator class (one of the classes listed above), an
explicitly-seeded generator is *guaranteed* to give the exactly same sequence
of outputs, when given exactly the same sequence of calls to any of the
``getrandbits``, ``randint``, ``randrange``, ``choice``, ``sample`` or
``shuffle`` methods. This guarantee applies across platforms, supported Python
versions, and ``pcgrandom`` releases.

The ``random`` and ``choices`` methods are subject to slightly weaker
guarantees: for ``random``, results are guaranteed to be equal to within
numerical tolerance (though in practice, on typical machines supporting IEEE
754 floating-point arithmetic, it's reasonable to expect results to be
identical). For ``choices``, something similar applies: floating-point error
may very occasionally result in one choice being made on a particular platform,
while a neighboring choice is made on a different platform. Again, in practice,
it's unlikely that such differences will occur, but the use of floating-point
means that this situation can't be ruled out. Both ``random`` and ``choices``
are guaranteed to advance the underlying generator by exactly the same amount
across platforms, so even if a ``random()`` result differs on two machines,
subsequent calls to ``randrange``, ``shuffle``, and so on, are still guaranteed
to give identical results.

Warning: this reproducibility guarantee no longer holds if any use is made of
sampling methods not explicitly mentioned above. For example, the
``normalvariate`` method uses a rejection method, with a rejection condition
based on a computation that uses the system math library. As such, it's
possible for different machines to make different numbers of calls to the
underlying PRNG, leaving the generators out of sync with each other: in that
situation, not only would the ``normalvariate`` results differ, but subsequent
calls to ``randrange`` and friends could also give completely different
results.

Note also that this guarantee does *not* apply to the ``pcgrandom.Random``
class or to the convenience classes ``pcgrandom.PCG32`` and
``pcgrandom.PCG64``. These classes may be updated in future versions to point
to fixed, updated or new core generators. If reproducibility is important to
you, always instantiate your generator using one of the concrete
classes. Conversely, ``pcgrandom.Random`` should always point to the current
"best" generator, and ``pcgrandom.PCG32`` and ``pcgrandom.PCG64`` give the best
generators with 32-bit and 64-bit output, respectively.

If it becomes necessary to make changes to any of the generators in a manner
that affects the output streams, a new class (for example ``PCG_XSH_RR_V1``)
incorporating those changes will be added to the library, and ``Random``,
``PCG32`` and/or ``PCG64`` will be updated to point to the new class where
appropriate. The old class will be left unchanged. In this way, reproducibility
can be assured.

Multiple streams
----------------

The PCG generators support a second argument ``sequence``, which allows
selecting one of many independent random streams. (Internally, different
``sequence`` values lead to different increments being used in the underlying
linear congruential generator.) Here's an example::

    >>> from pcgrandom import Random
    >>> gen1 = Random(seed=12345, sequence=1)
    >>> gen2 = Random(seed=12345, sequence=2)
    >>> [gen1.randrange(10) for _ in range(10)]
    [6, 7, 0, 2, 2, 2, 1, 8, 4, 3]
    >>> [gen2.randrange(10) for _ in range(10)]
    [4, 5, 2, 4, 3, 0, 7, 6, 1, 2]


Compatibility notes
-------------------

There are some minor differences between the standard library ``Random`` class
and the classes provided by ``pcgrandom``. Here we summarise the differences.

- While the ``Random`` class permits seeding from an arbitrary hashable object,
  the ``pcgrandom`` classes may only be seeded from integers. Allowing
  arbitrary hashable objects makes it harder to guarantee reproducibility if
  Python's hashing algorithm changes. See https://bugs.python.org/issue27706
  for an example of issues caused by this in the past. We may allow seeding
  from strings at some point in the future.

- The ``getrandbits`` method accepts an input of ``0``, returning ``0``
  (the unique integer in the range ``[0, 2**0)``). In ``random.Random``,
  ``getrandbits(0)`` raises ``ValueError``.

- The ``randrange`` and ``randint`` methods do not accept floats: an
  attempt to pass a float for the ``start``, ``stop`` or ``step`` will
  give a ``TypeError``.

- The ``shuffle`` method does not support the second ``random`` argument.

- The ``choices`` method exception handling differs in some corner cases:
  ``choices`` will raise ``ValueError`` if the sum of the given weights is
  zero. (The standard library version gives a somewhat accidental
  ``IndexError`` in this situation.) It always raises ``IndexError`` for an
  empty population, even if ``k = 0`` (the standard library version only raises
  if ``k > 0``). Our ``choices`` implementation also avoids the possibility of
  ``IndexError`` from double rounding or subnormal weights: see
  https://bugs.python.org/issue24567.

- Using ``from pcgrandom import *`` imports a handful of extra names that
  aren't imported by ``from random import *``, notably ``jumpahead``,
  ``PCG32``, ``PCG64``, and the names of the concrete generator classes. Thus
  there's a small risk of overwriting existing names when using this form of
  import.


.. |build-status| image:: https://travis-ci.org/mdickinson/pcgrandom.svg?branch=master
   :target: https://travis-ci.org/mdickinson/pcgrandom
   :alt: Travis CI status
.. |coverage| image:: http://codecov.io/github/mdickinson/pcgrandom/coverage.svg?branch=master
   :target: http://codecov.io/github/mdickinson/pcgrandom
   :alt: Coverage statistics from codecov.io

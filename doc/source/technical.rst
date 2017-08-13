Efficient sampling without resampling
=====================================

The ``sample`` algorithm in the ``pcgrandom`` package is different from that in
the Python standard library. The algorithm is based on one attributed to Robert
Floyd, and appearing in "More Programming Pearls" by Jon Bentley. Here we
explain how the algorithm works.

For reference, here's the essence of the Python code we use. It's slightly
simplified: instead of sampling from an arbitrary population, we sample from
``range(n)``, and some of the error checks and type conversions are omitted. ::

    def sample(n, k):
        """Generate a length-k subsample of range(n)."""

        position = {}
        for i in reversed(range(k)):
            element = randrange(i, n)
            if element in position:
                position[i] = position[element]
            position[element] = i

        sample = [None] * k
        for element, index in position.items():
            sample[index] = element

        return sample

Note that the order of the sample is considered significant, so
for example ``[1, 7, 2]`` and ``[2, 1, 7]`` are considered distinct length-3
subsamples of ``range(10)``, and the code above will produce each of these
with equal likelihood. Here's an example usage::

    >>> sample(7, 4)
    [2, 0, 1, 4]
    >>> sample(7, 4)
    [6, 1, 2, 3]


Generating samples incrementally
--------------------------------

Here's the key idea involved in the ``sample`` algorithm. Given a sample of
length ``k`` from ``range(n)``, represented as a Python ``list``, say, we can
augment that sample to produce a sample of length ``k+1`` from ``range(n+1)``
as follows:

1. Choose an integer ``i`` from ``range(n+1)`` at random.
2. If ``i`` is already in the sample, replace that sample entry with ``n``.
3. Append ``i`` to the sample.

In code::

    def augment_sample(n, sample):
        """Given a sample from range(n), augment that sample to produce
        a new sample of length len(sample)+1 from range(n+1).
        """
        i = randrange(n+1)
        if i in sample:
            sample[sample.index(i)] = n
        sample.append(i)

What's notable here is that there's no need for any kind of ``while`` loop to
do resampling: no matter what ``i`` we get, we can always use it to build our
augmented sample.

To illustrate the above, suppose we have a sample ``[6, 1, 2]`` from
``range(7)``. To augment this to a length-4 sample from ``range(8)``, we first
choose an ``i`` at random in the range ``0 <= i < 8``. Suppose that choice
gives us ``i = 5``.  Then since ``5`` is not already in the sample, we simply
append it to get a new sample ``[6, 1, 2, 5]``.

On the other hand, suppose that we end up with ``i = 1``. Since ``1``
is already present in the sample, we first replace it with ``7``, getting
``[6, 7, 2]``. Only *then* do we append the choice to the sample, getting
``[6, 7, 2, 1]``.

The reason this works is that each length-``k+1`` subsample of ``range(n+1)``
is produced *in exactly one way* by the above procedure. The easiest way to see
this is to show that it's possible to construct the inverse procedure: given
any length ``k+1`` subsample ``t`` of ``range(n+1)``, we can find a
length-``k`` subsample ``s`` of ``range(n)`` and a choice ``i`` from
``randrange(n+1)``, such that ``s`` and ``i`` produce ``t``. The inverse
procedure results from simply unwinding the original procedure, so it looks
like this:

1. Remove the last element of ``t``; call it ``i``.
2. If ``n`` appears anywhere in ``t`` (after step 1), replace it with ``i``.

In other words, if we write ``S(n, k)`` for the set of length-``k`` (ordered)
samples from ``range(n)``, our augmentation procedure establishes a bijection::

    S(n, k) × range(n+1)  ⟷  S(n+1, k+1)

Iterating this, we can create a sample of length ``k`` from
``range(n)`` by starting with the empty list (thought of as a sample of length
``0`` from ``range(n-k)``), and augmenting that sample ``k`` times using
the ``augment_sample`` procedure::

    def sample_incrementally(n, k):
        """Generate subsample of range(n) of length k."""
        sample = []
        for j in range(n-k, n):
            augment_sample(j, sample)
        return sample

Assuming a perfect core PRNG, all samples will be produced with equal
likelihood.

Making it efficient
-------------------

Those linear-time ``index`` method calls in ``augment_sample`` kill the
efficiency of ``sample_incrementally`` as ``k`` becomes large. For example,
on my machine, taking a 5000-element sample from ``range(10000)`` takes around
a quarter of a second::

    In [2]: %timeit sample_incrementally(10000, 5000)
    256 ms ± 3.49 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

For comparison, the actual code we use ends up taking a fraction of that time::

    In [3]: %timeit sample(10000, 5000)
    7.3 ms ± 78.5 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)

For a new potential element ``i`` of our sample, we need to be able to
check efficiently whether ``i`` is already in the sample, and if so,
what position it occupies. The obvious solution is to maintain a dictionary
``position`` whose keys are the elements of the sample, and whose values
are the positions occupied by those elements. And with that ``position``
dictionary, the actual sample list is redundant.

Here's what the ``augment_sample`` function looks like when we replace
the sample with a position dictionary::

    def augment_position(n, position):
        """Given a sample from range(n) represented by a dict ``position`` that
        maps each sample element to its index in the sample, augment that
        sample to obtain a sample of length len(position)+1 from range(n+1).
        """

        k = len(position)
        element = randrange(n+1)
        if element in position:
            position[n] = position[element]
        position[element] = k

The ``sample_incrementally`` function is much the same as before, except that
now we need a final step to unravel the ``position`` dictionary to retrieve the
sample it represents in list form. ::

    def sample_incrementally_faster(n, k):
        """More efficient version of sample_incrementally."""

        position = {}
        for j in range(n-k, n):
            augment_position(j, position)

        # Reverse the 'position' dict to get the final sample.
        sample = [None] * k
        for element, index in position.items():
            sample[index] = element
        return sample

Here's a timing::

    In [4]: %timeit sample_incrementally_faster(10000, 5000)
    7.84 ms ± 107 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)

Final steps
-----------

By inlining the ``augment_position`` function, we end up with something close
to the final code::

    def sample_almost_final(n, k):
      """Generate a subsample of range(n) of length k."""

      position = {}
      for j in range(n - k, n):
          element = randrange(j + 1)
          if element in position:
              position[j] = position[element]
          position[element] = j - (n - k)

      # Reverse the 'position' dict to get the final sample.
      sample = [None] * k
      for element, index in position.items():
          sample[index] = element
      return sample

The code becomes marginally simpler if we reverse everything: we start with an
empty sample from ``range(k, n)``, augment that to a sample of length ``1``
from ``range(k-1, n)``, then to a sample of length ``2`` from ``range(k-2,
n)``, and so on all the way down to a length-``k`` sample from ``range(n)``.
We also reverse the order that the sample is filled, from position ``k-1`` down
to position ``0`` rather than the other way around. With those changes, we
end up with the version of the code first posted::

    def sample(n, k):
        """Generate a subsample of range(n) of length k."""

        position = {}
        for i in reversed(range(k)):
            element = randrange(i, n)
            if element in position:
                position[i] = position[element]
            position[element] = i

        sample = [None] * k
        for element, index in position.items():
            sample[index] = element

        return sample

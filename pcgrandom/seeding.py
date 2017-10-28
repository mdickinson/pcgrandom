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
Helper functions for providing integer seeds.
"""

import hashlib
import operator
import os

# Python 2 compatibility: make int.from_bytes available.
from builtins import int


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
    nnumbytes, excess = divmod(-bits, 8)
    seed = int.from_bytes(os.urandom(-nnumbytes), byteorder="big")
    return seed >> excess


def seed_from_integer_like(obj, bits):
    """
    Create an integer seed from an object that supports __index__.

    Parameters
    ----------
    obj : integer-like
        The object to use to create the seed.
    bits : nonnegative integer.
        Number of bits needed for the seed. This function can produce
        a maximum of 512 bits from a Unicode or string object.

    Returns
    -------
    seed : integer
        Integer seed in the range 0 <= seed < 2**bits.

    Raises
    ------
    TypeError
        If the given object cannot be interpreted as an integer.
    """
    return operator.index(obj) & ~(~0 << bits)


def seed_from_bytes_like(obj, bits):
    """
    Create an integer seed from an object that supports the buffer protocol.

    Parameters
    ----------
    obj : integer-like
        The object to use to create the seed.
    bits : nonnegative integer.
        Number of bits needed for the seed. This function can produce
        a maximum of 512 bits from a Unicode or string object.

    Returns
    -------
    seed : integer
        Integer seed in the range 0 <= seed < 2**bits.

    Raises
    ------
    TypeError
        If the given object cannot be interpreted as an integer.
    ValueError
        If more than 512 bits are requested.
    """
    digest = hashlib.sha512(obj).digest()

    nnumbytes, excess = divmod(-bits, 8)
    if len(digest) + nnumbytes < 0:
        maxbits = 8 * len(digest)
        raise ValueError(
            "Cannot provide more than {} bits of seed.".format(maxbits))

    return int.from_bytes(digest[:-nnumbytes], byteorder="big") >> excess


def seed_from_object(obj, bits):

    """
    Create a new integer seed from the given Python object, in
    a reproducible manner. Currently accepts only integer-like
    objects and objects supporting the buffer protocol.

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
    # From None.
    if obj is None:
        return seed_from_system_entropy(bits)

    # From an integer-like object: value is used as-is, after reduction modulo
    # the appropriate power of 2.
    try:
        return seed_from_integer_like(obj, bits)
    except TypeError:
        pass

    # From something that supports the buffer protocol. Seed is based on
    # truncating the sha512 secure hash of the object.
    try:
        return seed_from_bytes_like(obj, bits)
    except TypeError:
        pass

    raise TypeError(
        "Unable to create seed from object of type {}. "
        "Please use an integer or a bytestring.".format(type(obj))
    )

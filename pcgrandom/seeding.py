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
    numbytes, excess = -(-bits // 8), -bits % 8
    seed = int.from_bytes(os.urandom(numbytes), byteorder="big")
    return seed >> excess


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
    # From an integer-like object: value is used as-is, after reduction modulo
    # the appropriate power of 2.
    try:
        obj_as_integer = operator.index(obj)
    except TypeError:
        pass
    else:
        return obj_as_integer & ~(~0 << bits)

    # From something that supports the buffer protocol. Seed is based on
    # truncating the sha512 secure hash of the object.
    try:
        obj_hash = hashlib.sha512(obj)
    except TypeError:
        pass
    else:
        digest = obj_hash.digest()
        numbytes, excess = -(-bits // 8), -bits % 8

        if numbytes > len(digest):
            raise ValueError(
                "Cannot provide more than {} bits of seed.".format(
                    8 * len(digest)))

        return int.from_bytes(digest[:numbytes], byteorder="big") >> excess

    raise TypeError(
        "Unable to create seed from object of type {}. "
        "Please use an integer or a bytestring.".format(
            type(obj))
    )

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
Convenience all-in-one construction functions.
"""
from pcgrandom.core_generators import (
    xsh_rr_64_32,
    xsh_rs_64_32,
    xsl_rr_128_64,
)
from pcgrandom.random import Random


def PCG_XSH_RR_V0(seed=None, sequence=None, multiplier=None):
    """
    Return a Random-like instance based on the PCG-XSH-RR generator.

    PCG-XSH-RR is described in section 6.3.1 of the PCG paper. It's
    based on a 64-bit linear congruential generator.

    Parameters
    ----------
    seed : object, optional
        integer-like or bytes-like object used to seed the core generator.
    sequence : integer, optional
        integer in the range [0, 2**63), specifying the core sequence.
        This determines the increment used in the underlying linear
        congruential generator.
    multiplier : integer, optional
        integer in the range [0, 2**64) giving the multiplier used in
        the LCG. The default value for this is carefully chosen and
        well-tested. Other values may give poor-quality generators;
        change this value at your own risk!

    Returns
    -------
    generator : Random
        Random-like object based on the specified PCG class.
    """
    return Random(
        seed=seed,
        core_generator=xsh_rr_64_32(sequence, multiplier),
    )


def PCG_XSH_RS_V0(seed=None, sequence=None, multiplier=None):
    """
    Return a Random-like instance based on the PCG-XSH-RS generator.

    PCG-XSH-RS is described in section 6.3.1 of the PCG paper. It's
    based on a 64-bit linear congruential generator.

    Parameters
    ----------
    seed : object, optional
        integer-like or bytes-like object used to seed the core generator.
    sequence : integer, optional
        integer in the range [0, 2**63), specifying the core sequence.
        This determines the increment used in the underlying linear
        congruential generator.
    multiplier : integer, optional
        integer in the range [0, 2**64) giving the multiplier used in
        the LCG. The default value for this is carefully chosen and
        well-tested. Other values may give poor-quality generators;
        change this value at your own risk!

    Returns
    -------
    generator : Random
        Random-like object based on the specified PCG class.
    """
    return Random(
        seed=seed,
        core_generator=xsh_rs_64_32(sequence, multiplier),
    )


def PCG_XSL_RR_V0(seed=None, sequence=None, multiplier=None):
    """
    Return a Random-like instance based on the PCG-XSL-RR generator.

    PCG-XSL-RR is described in section 6.3.1 of the PCG paper. It's
    based on a 128-bit linear congruential generator.

    Parameters
    ----------
    seed : object, optional
        integer-like or bytes-like object used to seed the core generator.
    sequence : integer, optional
        integer in the range [0, 2**127), specifying the core sequence.
        This determines the increment used in the underlying linear
        congruential generator.
    multiplier : integer, optional
        integer in the range [0, 2**128) giving the multiplier used in
        the LCG. The default value for this is carefully chosen and
        well-tested. Other values may give poor-quality generators;
        change this value at your own risk!

    Returns
    -------
    generator : Random
        Random-like object based on the specified PCG class.
    """
    return Random(
        seed=seed,
        core_generator=xsl_rr_128_64(sequence, multiplier),
    )

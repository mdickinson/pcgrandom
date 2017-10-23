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

from pcgrandom.constructors import (
    PCG_XSH_RR_V0,
    PCG_XSH_RS_V0,
    PCG_XSL_RR_V0,
)
from pcgrandom.random import Random


__all__ = [
    # Convenience functions for creating Random instances
    # with particular core generators.
    "PCG_XSH_RR_V0", "PCG_XSH_RS_V0", "PCG_XSL_RR_V0",

    # Generator synonyms.
    "PCG32", "PCG64", "Random",

    # List of all generators (not including synonyms).
    "pcg_generators",

    # Methods related to the internal state.
    "getstate", "jumpahead", "seed", "setstate",

    # Methods of the auto-created instance: integer generators.
    "getrandbits", "randint", "randrange",

    # Methods of the auto-created instance: combinatorial.
    "choice", "choices", "sample", "shuffle",

    # Methods of the auto-created instance: float generators.
    "betavariate", "expovariate", "gammavariate", "gauss", "lognormvariate",
    "normalvariate", "paretovariate", "random", "triangular", "uniform",
    "vonmisesvariate", "weibullvariate",
]

# List of all available generators; mostly used in testing.
pcg_generators = [PCG_XSH_RR_V0, PCG_XSH_RS_V0, PCG_XSL_RR_V0]

# Allow users to do 'from pcgrandom import Random', to mimic standard library
# 'random' module. Note that this may change with releases, so if
# reproducibility is important, users should import and use the specific
# generator.  We also provide synonyms for common generators. Again, these may
# be updated over time to point to later versions of the same generators, or
# possibly even to different generators. In situations where reproducibility
# matters, avoid the synonyms and use the explicit generator name.
PCG32 = PCG_XSH_RR_V0
PCG64 = PCG_XSL_RR_V0

# List of all available generators. Used mostly in testing.
pcg_generators = [
    PCG_XSH_RR_V0,
    PCG_XSH_RS_V0,
    PCG_XSL_RR_V0,
]

# Create one instance, seeded from urandom, and export its methods
# as module-level functions.  The functions share state across all uses
# (both in the user's code and in the Python libraries), but that's fine
# for most programs and is easier for the casual user than making them
# instantiate their own Random() instance.

_inst = Random()

seed = _inst.seed
getstate = _inst.getstate
setstate = _inst.setstate
jumpahead = _inst.jumpahead

getrandbits = _inst.getrandbits
randint = _inst.randint
randrange = _inst.randrange

choice = _inst.choice
choices = _inst.choices
sample = _inst.sample
shuffle = _inst.shuffle

betavariate = _inst.betavariate
expovariate = _inst.expovariate
gammavariate = _inst.gammavariate
gauss = _inst.gauss
lognormvariate = _inst.lognormvariate
normalvariate = _inst.normalvariate
paretovariate = _inst.paretovariate
random = _inst.random
triangular = _inst.triangular
uniform = _inst.uniform
vonmisesvariate = _inst.vonmisesvariate
weibullvariate = _inst.weibullvariate

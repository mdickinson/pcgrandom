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

from pcgrandom.pcg_common import PCGCommon


class PCG_XSH_RS_V0(PCGCommon):
    """
    Random subclass based on Melissa O'Neill's PCG family.

    This implements the generator described in section 6.3.2 of the PCG paper,
    PCG-XSH-RS, sitting on a 64-bit LCG from Knuth.
    """

    VERSION = u"pcgrandom.PCG_XSH_RS_V0"

    _state_bits = 64

    _state_mask = 2**64 - 1

    _output_bits = 32

    # Multiplier reportedly used by Knuth for the MMIX LCG.
    _default_multiplier = 6364136223846793005

    # Increment reportedly used by Knuth for the MMIX LCG.
    _default_increment = 1442695040888963407

    def _get_output(self, _mask=2**32-1):
        """Compute output from current state."""
        state = self._state
        return ((state ^ (state >> 22)) >> (22 + (state >> 61))) & _mask

    def _next_output(self):
        """Return next output; advance the underlying LCG.
        """
        output = self._get_output()
        self._advance_state()
        return output

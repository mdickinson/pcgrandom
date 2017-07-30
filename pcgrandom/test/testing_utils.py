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

import contextlib
import sys


@contextlib.contextmanager
def args_in_sys_argv(args):
    """
    Temporarily change sys.argv to something of the form [prog_name, args].
    """
    old_sys_argv = sys.argv
    sys.argv = sys.argv[:1] + args
    try:
        yield
    finally:
        sys.argv = old_sys_argv

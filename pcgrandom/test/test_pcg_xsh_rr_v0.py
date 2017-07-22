"""
Tests for the PCG_XSH_RR_V0 generator.
"""
import unittest

from pcgrandom.pcg_xsh_rr_v0 import PCG_XSH_RR_V0
from pcgrandom.test.test_common import TestCommon


class Test_PCG_XSH_RR_V0(TestCommon, unittest.TestCase):
    gen_class = PCG_XSH_RR_V0

    def setUp(self):
        self.gen = self.gen_class(seed=15206, sequence=1729)

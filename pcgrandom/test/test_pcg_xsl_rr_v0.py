"""
Tests for the PCG_XSL_RR_V0 generator.
"""
import unittest

from pcgrandom.pcg_xsl_rr_v0 import PCG_XSL_RR_V0
from pcgrandom.test.test_common import TestCommon


class Test_PCG_XSL_RR_V0(TestCommon, unittest.TestCase):
    gen_class = PCG_XSL_RR_V0

    def setUp(self):
        self.gen = self.gen_class(seed=15206, sequence=1729)

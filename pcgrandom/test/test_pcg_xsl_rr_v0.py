"""
Tests for the PCG_XSL_RR_V0 generator.
"""
from __future__ import division

import unittest

from pcgrandom.pcg_xsl_rr_v0 import PCG_XSL_RR_V0
from pcgrandom.test.test_common import TestCommon


# Sequences used for detecting reproducibility regressions.
seq0_seed12345_die_rolls = [
    2, 2, 1, 6, 4, 2, 1, 5, 2, 3, 5, 5, 2, 1, 6, 5, 6, 4, 2, 2]
seq0_seed12345_uniforms = [
    float.fromhex('0x1.914d30cdc8438p-3'),
    float.fromhex('0x1.95559ac4dfa84p-3'),
    float.fromhex('0x1.f3612f1f265c8p-4'),
    float.fromhex('0x1.c87c795ddc073p-1'),
    float.fromhex('0x1.055e2a2568177p-1'),
    float.fromhex('0x1.12b02c291be50p-2'),
    float.fromhex('0x1.3272ecbc61f98p-3'),
    float.fromhex('0x1.6efb350d9ea00p-1'),
    float.fromhex('0x1.11320fb1baed4p-2'),
    float.fromhex('0x1.a1142b39a5370p-2'),
]
seq0_seed12345_choices = [
    'S4', 'S4', 'S8', 'C7', 'DA', 'HA', 'S7', 'D3',
    'HA', 'H6', 'D2', 'CQ', 'S2']
seq0_seed12345_sample = [
    'ST', 'D4', 'C8', 'D6', 'DJ', 'H7', 'H9', 'HT',
    'D9', 'C5', 'CJ', 'C4', 'HQ'
]
seq0_seed12345_shuffle = [
    11, 10, 1, 8, 6, 19, 18, 3, 5, 4,
    13, 12, 16, 0, 9, 7, 2, 15, 14, 17,
]


class Test_PCG_XSL_RR_V0(TestCommon, unittest.TestCase):
    gen_class = PCG_XSL_RR_V0

    def setUp(self):
        self.gen = self.gen_class(seed=15206, sequence=1729)

    def test_reproducibility(self):
        gen = PCG_XSL_RR_V0(seed=12345, sequence=0)
        die_rolls = [gen.randint(1, 6) for _ in range(20)]
        self.assertEqual(
            die_rolls,
            seq0_seed12345_die_rolls,
        )

        # Assumes IEEE 754 binary64 floats. For other formats, we'd only expect
        # to get approximate equality here. If this ever actually breaks on
        # anyone's machine, please report to me and I'll fix it.
        gen = PCG_XSL_RR_V0(seed=12345, sequence=0)
        uniforms = [gen.random() for _ in range(10)]
        self.assertEqual(uniforms, seq0_seed12345_uniforms)

        gen = PCG_XSL_RR_V0(seed=12345, sequence=0)
        suits = 'SHDC'
        values = 'AKQJT98765432'
        cards = [suit+value for suit in suits for value in values]

        # Selection with repetition.
        choices = [gen.choice(cards) for _ in range(13)]
        self.assertEqual(choices, seq0_seed12345_choices)

        # Sampling
        sample = gen.sample(cards, 13)
        self.assertEqual(sample, seq0_seed12345_sample)

        # Shuffling
        population = list(range(20))
        gen.shuffle(population)
        self.assertEqual(population, seq0_seed12345_shuffle)

"""
Tests for the PCG_XSL_RR_V0 generator.
"""
from __future__ import division

import unittest

from pcgrandom.pcg_xsl_rr_v0 import PCG_XSL_RR_V0
from pcgrandom.test.test_common import TestCommon


# Sequences used for detecting reproducibility regressions.
seq0_seed12345_die_rolls = [
    1, 2, 4, 4, 1, 4, 2, 2, 6, 1, 6, 2, 4, 6, 6, 5, 1, 1, 2, 6]
seq0_seed12345_uniforms = [
    float.fromhex('0x1.36feb111851b8p-3'),
    float.fromhex('0x1.d0eab4d2dacd0p-3'),
    float.fromhex('0x1.3153584d8fc39p-1'),
    float.fromhex('0x1.2839f1285a962p-1'),
    float.fromhex('0x1.dd8596e786ab0p-5'),
    float.fromhex('0x1.295b84d5041f7p-1'),
    float.fromhex('0x1.86227587a6c34p-3'),
    float.fromhex('0x1.5ac08820e8fc8p-3'),
    float.fromhex('0x1.bbdbd5409790bp-1'),
    float.fromhex('0x1.1b964efcf0d0cp-3'),
]
seq0_seed12345_choices = [
    'S7', 'S3', 'D9', 'DT', 'SJ', 'DT', 'S5', 'S6',
    'C8', 'S7', 'C9', 'HK', 'DQ'
]
seq0_seed12345_sample = [
    'C8', 'S5', 'D6', 'DK', 'CK', 'S9', 'C2', 'HJ',
    'SK', 'S7', 'D2', 'C6', 'C5',
]
seq0_seed12345_shuffle = [
    19, 1, 9, 5, 18, 2, 15, 8, 6, 3,
    4, 0, 14, 10, 12, 11, 13, 16, 17, 7,
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

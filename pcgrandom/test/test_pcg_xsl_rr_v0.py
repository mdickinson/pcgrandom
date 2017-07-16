"""
Tests for the PCG_XSL_RR_V0 generator.
"""
from __future__ import division

import math
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

    def setUp(self):
        self.gen = PCG_XSL_RR_V0(seed=15206, sequence=1729)

    def test_creation_without_seed(self):
        gen1 = PCG_XSL_RR_V0()
        gen2 = PCG_XSL_RR_V0()

        sample1 = [gen1.random() for _ in range(10)]
        sample2 = [gen2.random() for _ in range(10)]

        # Possible in theory for these two samples to be identical; vanishingly
        # unlikely in practice.
        self.assertNotEqual(sample1, sample2)

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

    def test_sequence_default(self):
        gen1 = PCG_XSL_RR_V0(seed=12345, sequence=0)
        gen2 = PCG_XSL_RR_V0(seed=12345)
        self.assertEqual(gen1.getstate(), gen2.getstate())

    def test_independent_sequences(self):
        # Crude statistical test for lack of correlation. If X and Y are
        # independent and uniform on [0, 1], then (X - 0.5) * (Y - 0.5) has
        # mean 0 and standard deviation 1/12. By the central limit theorem, we
        # expect the average V of N such independent values to be roughly
        # normally distributed with mean 0 and standard deviation 1 /
        # (12*sqrt(N)). So we expect |V| to be at most 1 / (4*sqrt(N)) with
        # over 99% probability.
        gen1 = PCG_XSL_RR_V0(seed=12345, sequence=0)
        gen2 = PCG_XSL_RR_V0(seed=12345, sequence=1)
        N = 10000
        xs = [gen1.random() for _ in range(N)]
        ys = [gen2.random() for _ in range(N)]
        v = sum((x - 0.5) * (y - 0.5) for x, y in zip(xs, ys)) / N
        # Check we're within 3 standard deviations of the mean.
        self.assertLess(abs(v), 0.25/math.sqrt(N))

    def test_no_shared_state(self):
        # Get samples first from gen1, then from gen2.
        gen1 = PCG_XSL_RR_V0(seed=12345, sequence=0)
        gen2 = PCG_XSL_RR_V0(seed=12345, sequence=1)
        sample1_1 = [gen1.random() for _ in range(10)]
        sample2_1 = [gen2.random() for _ in range(10)]

        # Now in the opposite order: from gen2, then from gen1.
        gen1 = PCG_XSL_RR_V0(seed=12345, sequence=0)
        gen2 = PCG_XSL_RR_V0(seed=12345, sequence=1)
        sample2_2 = [gen2.random() for _ in range(10)]
        sample1_2 = [gen1.random() for _ in range(10)]

        # Now interleaved.
        gen1 = PCG_XSL_RR_V0(seed=12345, sequence=0)
        gen2 = PCG_XSL_RR_V0(seed=12345, sequence=1)
        sample1_3 = []
        sample2_3 = []
        for _ in range(10):
            sample1_3.append(gen1.random())
            sample2_3.append(gen2.random())

        # Results should be the same in all cases.
        self.assertEqual(sample1_1, sample1_2)
        self.assertEqual(sample1_1, sample1_3)
        self.assertEqual(sample2_1, sample2_2)
        self.assertEqual(sample2_1, sample2_3)

    def test_restore_state_from_different_generator(self):
        gen = PCG_XSL_RR_V0(seed=15206, sequence=27)
        state = gen.getstate()

        bad_version = 'pcgrandom.PCG_XSL_RR_V1'
        bad_state = (bad_version,) + state[1:]
        with self.assertRaises(ValueError):
            gen.setstate(bad_state)

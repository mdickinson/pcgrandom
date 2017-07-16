"""
Tests for the PCG_XSH_RR_V0 generator.
"""
from __future__ import division

import math
import unittest

from pcgrandom.pcg_xsh_rr_v0 import PCG_XSH_RR_V0
from pcgrandom.test.test_common import TestCommon


# Sequences used for detecting reproducibility regressions.
seq0_seed12345_die_rolls = [
    2, 5, 5, 4, 1, 6, 4, 4, 2, 5, 2, 6, 6, 2, 3, 1, 2, 6, 2, 6]
seq0_seed12345_uniforms = [
    float.fromhex('0x1.5086103ef2a40p-2'),
    float.fromhex('0x1.90a33cef220a7p-1'),
    float.fromhex('0x1.2be0bbe709ca8p-3'),
    float.fromhex('0x1.21bded2b2a972p-1'),
    float.fromhex('0x1.0a20e3b6ce7f8p-2'),
    float.fromhex('0x1.5307c0cf5db08p-2'),
    float.fromhex('0x1.cdd6de4c7c725p-1'),
    float.fromhex('0x1.65d8359c989eap-2'),
    float.fromhex('0x1.ea43f297b8b18p-3'),
    float.fromhex('0x1.0be283eba30c0p-2'),
]
seq0_seed12345_choices = [
    'HT', 'D2', 'CK', 'DJ', 'S7', 'C8', 'DJ', 'DT',
    'HA', 'D4', 'HT', 'CT', 'C7',
]
seq0_seed12345_sample = [
    'HT', 'C3', 'C8', 'DA', 'CA', 'D6', 'C6', 'H9',
    'SK', 'H8', 'HJ', 'H2', 'H6',
]
seq0_seed12345_shuffle = [
    5, 19, 1, 14, 10, 8, 11, 15, 18, 12,
    3, 7, 4, 2, 17, 0, 13, 6, 9, 16,
]


class Test_PCG_XSH_RR_V0(TestCommon, unittest.TestCase):
    def setUp(self):
        self.gen = PCG_XSH_RR_V0(seed=15206, sequence=1729)

    def test_creation_without_seed(self):
        gen1 = PCG_XSH_RR_V0()
        gen2 = PCG_XSH_RR_V0()

        sample1 = [gen1.random() for _ in range(10)]
        sample2 = [gen2.random() for _ in range(10)]

        # Possible in theory for these two samples to be identical; vanishingly
        # unlikely in practice.
        self.assertNotEqual(sample1, sample2)

    def test_reproducibility(self):
        gen = PCG_XSH_RR_V0(seed=12345, sequence=0)
        die_rolls = [gen.randint(1, 6) for _ in range(20)]
        self.assertEqual(
            die_rolls,
            seq0_seed12345_die_rolls,
        )

        # Assumes IEEE 754 binary64 floats. For other formats, we'd only expect
        # to get approximate equality here. If this ever actually breaks on
        # anyone's machine, please report to me and I'll fix it.
        gen = PCG_XSH_RR_V0(seed=12345, sequence=0)
        uniforms = [gen.random() for _ in range(10)]
        self.assertEqual(uniforms, seq0_seed12345_uniforms)

        gen = PCG_XSH_RR_V0(seed=12345, sequence=0)
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
        gen1 = PCG_XSH_RR_V0(seed=12345, sequence=0)
        gen2 = PCG_XSH_RR_V0(seed=12345)
        self.assertEqual(gen1.getstate(), gen2.getstate())

    def test_independent_sequences(self):
        # Crude statistical test for lack of correlation. If X and Y are
        # independent and uniform on [0, 1], then (X - 0.5) * (Y - 0.5) has
        # mean 0 and standard deviation 1/12. By the central limit theorem, we
        # expect the average V of N such independent values to be roughly
        # normally distributed with mean 0 and standard deviation 1 /
        # (12*sqrt(N)). So we expect |V| to be at most 1 / (4*sqrt(N)) with
        # over 99% probability.
        gen1 = PCG_XSH_RR_V0(seed=12345, sequence=0)
        gen2 = PCG_XSH_RR_V0(seed=12345, sequence=1)
        N = 10000
        xs = [gen1.random() for _ in range(N)]
        ys = [gen2.random() for _ in range(N)]
        v = sum((x - 0.5) * (y - 0.5) for x, y in zip(xs, ys)) / N
        # Check we're within 3 standard deviations of the mean.
        self.assertLess(abs(v), 0.25/math.sqrt(N))

    def test_no_shared_state(self):
        # Get samples first from gen1, then from gen2.
        gen1 = PCG_XSH_RR_V0(seed=12345, sequence=0)
        gen2 = PCG_XSH_RR_V0(seed=12345, sequence=1)
        sample1_1 = [gen1.random() for _ in range(10)]
        sample2_1 = [gen2.random() for _ in range(10)]

        # Now in the opposite order: from gen2, then from gen1.
        gen1 = PCG_XSH_RR_V0(seed=12345, sequence=0)
        gen2 = PCG_XSH_RR_V0(seed=12345, sequence=1)
        sample2_2 = [gen2.random() for _ in range(10)]
        sample1_2 = [gen1.random() for _ in range(10)]

        # Now interleaved.
        gen1 = PCG_XSH_RR_V0(seed=12345, sequence=0)
        gen2 = PCG_XSH_RR_V0(seed=12345, sequence=1)
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
        gen = PCG_XSH_RR_V0(seed=15206, sequence=27)
        state = gen.getstate()

        bad_version = 'pcgrandom.PCG_XSH_RR_V1'
        bad_state = (bad_version,) + state[1:]
        with self.assertRaises(ValueError):
            gen.setstate(bad_state)

import numpy as np
import unittest

import codescanner_analysis.utils.file_to_array as fta


class FileToArrayTest(unittest.TestCase):

    def setUp(self):
        self._file_size = 15
        self._regions_0 = [[1, 3], [5, 6], [8, 10]]
        self._regions_1 = [[1, 3], [4, 5]]

    def test_analog_minus(self):
        self._regions_1 = [[1, 3], [4, 5]]
        B_regions = fta.Analog(self._regions_0, self._file_size)
        B_result = fta.Analog(self._regions_1, self._file_size, '-', B_regions)

        regions_r = fta.toDigital(B_result)
        expected_r = [[5, 6], [8, 10]]

        assert np.array_equal(expected_r, regions_r)

    def test_analog_minus_unsorted(self):
        regions_0 = [[5, 6], [1, 3], [8, 10]]
        regions_1 = [[4, 5], [1, 3]]
        B_regions = fta.Analog(regions_0, self._file_size)
        B_result = fta.Analog(regions_1, self._file_size, '-', B_regions)

        regions_r = fta.toDigital(B_result)
        expected_r = [[5, 6], [8, 10]]

        assert np.array_equal(expected_r, regions_r)

    def test_analog_add(self):
        B_regions = fta.Analog(self._regions_0, self._file_size)
        B_result = fta.Analog(self._regions_1, self._file_size, '+', B_regions)

        regions_r = fta.toDigital(B_result)
        expected_r = [[1, 3], [4, 6], [8, 10]]

        assert np.array_equal(expected_r, regions_r)

    def test_analog_mul(self):
        B_regions = fta.Analog(self._regions_0, self._file_size)
        B_result = fta.Analog(self._regions_1, self._file_size, '*', B_regions)

        regions_r = fta.toDigital(B_result)
        expected_r = [[1, 3]]

        assert np.array_equal(expected_r, regions_r)

    def test_analog_mul_extended(self):
        regions_00 = [[0, 3], [5, 6], [8, self._file_size]]
        regions_01 = [[1, 3], [4, 6]]
        expexted_01 = [[1, 3], [5, 6]]
        regions_02 = [[9, self._file_size], [0, 2]]
        expexted_02 = [[0, 2], [9, self._file_size]]

        B_regions = fta.Analog(regions_00, self._file_size)
        B_result_01 = fta.Analog(regions_01, self._file_size, '*', B_regions)

        B_regions = fta.Analog(regions_00, self._file_size)
        B_result_02 = fta.Analog(regions_02, self._file_size, '*', B_regions)

        regions_r_01 = fta.toDigital(B_result_01)
        regions_r_02 = fta.toDigital(B_result_02)

        assert np.array_equal(expexted_01, regions_r_01)
        assert np.array_equal(expexted_02, regions_r_02)

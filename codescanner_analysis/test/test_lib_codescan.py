import unittest
import os

import pytest

from codescanner_analysis import libcodescanpy as codescan


class LibCodescanTest(unittest.TestCase):

    def setUp(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        test_file_dir = os.path.join(root_dir, 'test', 'data')
        self.test_file = os.path.join(test_file_dir, 'testfile')
        codescan.init()

    def test_no_file(self):
        with pytest.raises(OSError):
            codescan.scan('nofile', 0, 0)

    def test_run_dict(self):
        test_file = self.test_file

        result = codescan.scan(test_file, 0, 0)

        expected_coderegions = [{'from': 4096, 'to': 7680, 'bitness': 64, 'endianess': 1, 'architecture': 'Intel'}]

        assert result['Code'] == expected_coderegions
        assert len(result['Ascii']) == 3
        assert len(result['Code']) == 1
        assert len(result['Zero']) == 2
        assert len(result['HighEntropy']) == 1
        assert len(result['Data']) == 11
        assert 'PackedCode' not in result

    def test_run_list(self):
        test_file = self.test_file

        result = codescan.scan(test_file, 0, 0, r_type=codescan.RESULT_LIST)

        expected_coderegions = [[4096, 7680, 'Intel', 64, 1]]

        assert result['Code'] == expected_coderegions
        assert len(result['Ascii']) == 3
        assert len(result['Code']) == 1
        assert len(result['Zero']) == 2
        assert len(result['HighEntropy']) == 1
        assert len(result['Data']) == 11
        assert 'PackedCode' not in result

    def test_run_list_with_offsets(self):
        test_file = self.test_file

        result = codescan.scan(test_file, 0x100, 0x400, r_type=codescan.RESULT_LIST)

        expected_data = [[0x100, 0x400]]

        # print()
        # print("result")
        # print(result)

        assert result['Data'] == expected_data
        assert len(result['Data']) == 1

import os
import pytest
import unittest

from codescanner_analysis.codescanner_analysis import CodescannerAnalysisData
from codescanner_analysis.extended_analysis import make_decision


class FileHeaderParserTest(unittest.TestCase):

    def test_missing_size_parameters(self):
        sizes = {}

        with pytest.raises(RuntimeError):
            make_decision(sizes, None)

        sizes = None

        with pytest.raises(RuntimeError):
            make_decision(sizes, None)

        sizes = {'FileSize': 0}

        with pytest.raises(RuntimeError):
            make_decision(sizes, None)

    def test_output(self):
        test_binary_src = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'testfile')
        cad = CodescannerAnalysisData(test_binary_src)

        result = cad.decision

        assert result is not None

import os
import unittest

from codescanner_analysis import CodescannerAnalysisData
from codescanner_analysis import PlotBase


class PlotBaseTest(unittest.TestCase):

    def setUp(self):
        self._test_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
        self._test_binary_src = os.path.join(self._test_file_dir, 'testfile')

    def test_update_code_spec_label(self):
        cad = CodescannerAnalysisData(self._test_binary_src)
        p = PlotBase(self._test_binary_src, cad.regions)
        p.update_code_spec_label(cad.architecture.get('Full'))

        assert p._area_specs[0].label == cad.architecture.get('Full')

    def test_update_code_spec_label_with_no_architecture_found(self):
        cad = CodescannerAnalysisData(self._test_binary_src)
        p = PlotBase(self._test_binary_src, cad.regions)
        old_label = p._area_specs[0].label
        p.update_code_spec_label(None)

        assert p._area_specs[0].label == old_label

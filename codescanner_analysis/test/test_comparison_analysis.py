import os
from tempfile import TemporaryDirectory

import pytest
import tempfile
import unittest

from codescanner_analysis.comparison_analysis import ComparisonAnalysis


class ComparisonAnalysisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
        cls.test_binary_src = os.path.join(cls.test_file_dir, 'testfile')

    def test_not_existing_file(self):
        with pytest.raises(IOError):
            ComparisonAnalysis('abc')

    def test_parse_code_sections(self):
        ca = ComparisonAnalysis(self.test_binary_src)
        result = ca.x_regions

        expected = {'.plt.got': [[4416, 4424]], '.fini': [[7204, 7213]], '.init': [[4016, 4042]],
                    '.plt': [[4048, 4416]], '.text': [[4432, 7202]]}

        assert result == expected

    def test_parse_code_sections_with_obj_dump(self):
        ca = ComparisonAnalysis(self.test_binary_src)
        result = ca.parse_x_regions_with_objdump()

        expected = {'.plt.got': [[4416, 4424]], '.fini': [[7204, 7213]], '.init': [[4016, 4042]],
                    '.plt': [[4048, 4416]], '.text': [[4432, 7202]]}

        assert expected == result

    def test_parse_code_sections_with_header_parser(self):
        ca = ComparisonAnalysis(self.test_binary_src)
        result = ca._parse_x_regions_with_header_parser()

        expected = {'.plt.got': [[4416, 4424]], '.fini': [[7204, 7213]], '.init': [[4016, 4042]],
                    '.plt': [[4048, 4416]], '.text': [[4432, 7202]]}

        assert result == expected

    def test_wrong_plot_parameters(self):
        ca = ComparisonAnalysis(self.test_binary_src)

        with pytest.raises(RuntimeError):
            ca.plot_to_file("")

    def test_empty_dicts_plotting(self):
        ca = ComparisonAnalysis(self.test_binary_src)

        saved_cs_regions = ca.cs_regions
        saved_x_regions = ca.x_regions

        ca.cs_regions = None

        with pytest.raises(RuntimeError):
            ca.plot_to_file("filename.png")

        ca.x_regions = None

        with pytest.raises(RuntimeError):
            ca.plot_to_file("filename.png")

        ca.cs_regions = saved_cs_regions

        with pytest.raises(RuntimeError):
            ca.plot_to_file("filename.png")

        ca.cs_regions = None
        ca.x_regions = saved_x_regions

        with pytest.raises(RuntimeError):
            ca.plot_to_file("filename.png")

    def test_no_header_found_plotting(self):
        with TemporaryDirectory() as temp_dir:
            plot_src = os.path.join(temp_dir, 'ComparisonAnalysisTest-test_no_header_found_plotting.png')

            ca = ComparisonAnalysis(self.test_binary_src)
            ca.x_regions = {}

            ca.plot_to_file(plot_src)

            assert os.path.isfile(plot_src)

    def test_plot_to_file(self):
        with TemporaryDirectory() as temp_dir:
            plot_png = os.path.join(temp_dir, 'ComparisonAnalysisTest-test_plot_to_file.png')

            # code labels with underscore
            ca = ComparisonAnalysis(self.test_binary_src)
            ca.plot_to_file(plot_png)

            assert os.path.isfile(plot_png)

    def test_are_code_regions_in_file(self):
        ca = ComparisonAnalysis(self.test_binary_src)

        assert ca.are_code_regions_in_file()

        file_size = os.path.getsize(self.test_binary_src)
        ca.x_regions['.text'].append([file_size - 500, file_size + 500])

        assert not ca.are_code_regions_in_file()

    def test_search_alien_code_with_out_of_bounds_x_regions(self):
        file_size = os.path.getsize(self.test_binary_src)
        ca = ComparisonAnalysis(self.test_binary_src)
        ca.x_regions = {'.ini': [[file_size - 100, file_size + 100]]}

        ca._search_alien_code()

        assert not ca.cs_regions.get("AlienCode")

    def test_search_alien_code(self):
        ca = ComparisonAnalysis(self.test_binary_src)

        ca._search_alien_code()

        assert ca.cs_regions.get("AlienCode")

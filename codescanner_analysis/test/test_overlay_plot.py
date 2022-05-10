import os
import unittest
from tempfile import TemporaryDirectory

from codescanner_analysis import ComparisonAnalysis
from codescanner_analysis import OverlayPlot


class OverlayPlotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._test_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
        cls._test_binary_src = os.path.join(cls._test_file_dir, 'testfile')

    def test_plotter_init(self):
        regions = {}
        x_regions = {
            '.init': [[1016, 1542]],
            '.plt': [[2048, 2416]],
            '.plt.got': [[3016, 3424]],
            '.text': [[4432, 6002]],
            '.fini': [[7004, 7513]],
        }

        plotter = OverlayPlot(self._test_binary_src, regions, x_regions)
        result_ids = []
        for a in plotter._x_area_specs:
            result_ids.append(a[1])

        expected_ids = ['.text', '.plt.got', '.init', '.plt', '.fini']

        assert sorted(result_ids) == sorted(expected_ids)

    def test_plot_to_file(self):
        with TemporaryDirectory() as temp_dir:
            plot_png = os.path.join(temp_dir, 'OverlayPointPlotTest-test_plot_to_file.png')

            ca = ComparisonAnalysis(self._test_binary_src)
            cs_regions = ca.cs_regions
            x_regions = ca.x_regions

            plotter = OverlayPlot(self._test_binary_src, cs_regions, x_regions)
            plotter.plot_to_file(plot_png, 100)

            assert os.path.isfile(plot_png)

    def test_plot_to_file_with_extending_x_regions(self):
        with TemporaryDirectory() as temp_dir:
            plot_png = os.path.join(temp_dir, 'OverlayPointPlotTest-test_plot_to_file_with_extending_x_regions.png')

            ca = ComparisonAnalysis(self._test_binary_src)
            cs_regions = ca._parse_regions_with_code_scanner()

            file_size = os.path.getsize(self._test_binary_src)

            x_regions = {
                '.plt': [(2048, 2416)],
                '.text': [(file_size - 500, file_size + 500), (file_size + 2500, file_size + 3000)],
                '.init': [(file_size + 750, file_size + 1000)],
            }
            plotter = OverlayPlot(self._test_binary_src, cs_regions, x_regions)
            plotter.plot_to_file(plot_png, 100)

            assert os.path.isfile(plot_png)

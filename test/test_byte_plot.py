# -*- coding: utf-8 -*-

import os
import tempfile
import unittest
from collections import defaultdict
from collections import namedtuple

import pytest
from _pytest.monkeypatch import MonkeyPatch

from byte_plot import BytePlot
from plot_base import PlotBase
from test import helper


class BytePlotTest(unittest.TestCase):

    def setUp(self):
        self._test_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
        self._test_binary_src = os.path.join(self._test_file_dir, 'testfile')
        self._test_medium_binary_src = os.path.join(self._test_file_dir, 'testfile-med')
        self._greatest_test_region_value = 15
        self._create_test_regions()
        self._create_specs()
        self._byte_plot = BytePlot(self._test_binary_src, self._test_regions)
        self._byte_plot._file_size = self._greatest_test_region_value

    def _create_test_regions(self):
        self._test_regions = defaultdict(list)
        self._test_regions['A'] = [(1, 2), (5, 6), (8, 9)]
        self._test_regions['B'] = [(2, 3), (6, 8), (12, self._greatest_test_region_value)]
        self._test_regions['C'] = [(3, 5), (9, 12)]

    def _create_specs(self):
        self.AreaSpec = namedtuple('AreaSpec', ['id', 'label', 'dot_color', 'line_color'])
        self._specs = [
            self.AreaSpec(id='A', label='Region A', dot_color='c', line_color='#0022cc'),
            self.AreaSpec(id='B', label='Region B', dot_color='#00533f', line_color='#007760'),
            self.AreaSpec(id='C', label='Region C', dot_color='#e04000', line_color='#601000'),
        ]

    def test_not_existing_file_call(self):
        monkeypatch = MonkeyPatch()
        monkeypatch.setattr('os.path.isfile', lambda _: False)

        with pytest.raises(IOError):
            BytePlot(self._test_binary_src, self._test_regions)

        monkeypatch.undo()

    def test_build_filename(self):
        ip = BytePlot(self._test_binary_src, self._test_regions)

        self._assert_filename(ip, 'noextensionfile', 'noextensionfile.png')
        self._assert_filename(ip, 'multiple.extension.file', 'multiple.extension_file.png')
        self._assert_filename(ip, 'oneextension.file', 'oneextension_file.png')

    def _assert_filename(self, ip, file, expected):
        ip._short_filename = file
        file_name = ip._build_filename(self._test_file_dir)
        assert file_name == os.path.join(self._test_file_dir, expected)

    def test_plot_to_buffer_with_numpy_exception(self):
        monkeypatch = MonkeyPatch()
        monkeypatch.setattr('numpy.fromfile', lambda filepath, dtype: None)

        regions = self._extract_test_binary_regions()
        byte_plot = BytePlot(self._test_binary_src, regions)

        with pytest.raises(RuntimeError):
            byte_plot.plot_to_buffer(100)

        monkeypatch.undo()

    def test_plot_dense_area_file(self):
        '''
        To visually test the output, this method may be run with calling the _write_image method.
        Otherwise it only tests if the bytes would create a png file.
        '''
        temp_dir = tempfile.gettempdir()
        size = int(1024 * 10)
        test_regions = helper.create_dense_regions(size)

        bin_src = os.path.join(temp_dir, 'IPT-test_plot_dense_area_file.bin')
        helper.create_random_file(bin_src, size)

        byte_plot = BytePlot(bin_src, test_regions)
        byte_plot._area_specs = self._specs
        byte_plot._file_size = size
        byte_plot.PAD_AREA_ID = 'A'

        image_bytes = byte_plot.plot_to_buffer(100)
        # img_src = self._get_image_src(self._test_file_dir, 'tcm_test_plot_dense_area_file.png')
        # color_map._write_image(image_bytes, img_src)

        assert image_bytes.startswith(helper.MAGIC_PNG_BYTES)

        os.remove(bin_src)

    def test_plot_small_file(self):
        temp_dir = tempfile.gettempdir()
        bin_src = os.path.join(temp_dir, 'IPT-test_plot_small_file.bin')

        helper.create_random_file(bin_src, 0x200)

        r = helper.extract_regions(bin_src)

        assert 'Data' in r

        os.remove(bin_src)

    def test_plotting_test_file_is_png(self):
        '''
        To visually test the output, this method may be run with calling the _write_image method.
        Otherwise it only tests if the bytes would create a png file.
        '''
        regions = self._extract_test_binary_regions()

        byte_plot = BytePlot(self._test_binary_src, regions)
        image_bytes = byte_plot.plot_to_buffer(100)

        assert image_bytes.startswith(helper.MAGIC_PNG_BYTES)

    def test_plot_to_file(self):
        dpi = 100
        temp_dir = tempfile.gettempdir()
        # temp_dir = self._test_file_dir
        img_path = os.path.join(temp_dir, 'IPT-tptf.png')
        expected_size = (dpi * BytePlot.FIG_SIZE[0], dpi * BytePlot.FIG_SIZE[1])

        regions = self._extract_test_binary_regions()
        cm = BytePlot(self._test_binary_src, regions)
        cm.plot_to_file(str(img_path), dpi)

        assert os.path.isfile(img_path)
        helper.assert_image_size(expected_size, str(img_path))
        os.remove(img_path)

    def test_plot_to_dynamic_size_random_file(self):
        dpi = 72
        height = 0x1000
        temp_dir = tempfile.gettempdir()
        # temp_dir = self._test_file_dir

        bin_0_src = os.path.join(temp_dir, 'CMT-tptdsrf-0.bin')
        bin_1_src = os.path.join(temp_dir, 'CMT-tptdsrf-1.bin')

        img_0_path = os.path.join(temp_dir, 'IPT-tptdsrf-0.png')
        img_1_path = os.path.join(temp_dir, 'IPT-tptdsrf-1.png')

        file_0_size = 0x2000
        file_1_size = 0x4000

        expected_0_size = (int(dpi * file_0_size / PlotBase.DEFAULT_DPI), int(dpi * height / PlotBase.DEFAULT_DPI))
        expected_1_size = (int(dpi * file_1_size / PlotBase.DEFAULT_DPI), int(dpi * height / PlotBase.DEFAULT_DPI))

        helper.create_random_file(bin_0_src, file_0_size)
        helper.create_random_file(bin_1_src, file_1_size)
        r_0 = helper.extract_regions(bin_0_src)
        r_1 = helper.extract_regions(bin_1_src)

        cm_0 = BytePlot(bin_0_src, r_0)
        cm_1 = BytePlot(bin_1_src, r_1)

        cm_0.plot_to_dynamic_size_file(str(img_0_path), dpi, file_0_size, height)
        cm_1.plot_to_dynamic_size_file(str(img_1_path), dpi, file_1_size, height)

        assert os.path.isfile(img_0_path)
        assert os.path.isfile(img_1_path)
        helper.assert_image_size(expected_0_size, str(img_0_path))
        helper.assert_image_size(expected_1_size, str(img_1_path))
        os.remove(img_0_path)
        os.remove(img_1_path)
        os.remove(bin_0_src)
        os.remove(bin_1_src)

    def test_plot_to_dynamic_ratio_random_file(self):
        dpi = 100
        file_0_size = os.path.getsize(self._test_binary_src)
        height = 18382.7
        ratio = ((file_0_size / float(height)) * 9, 9)
        width = dpi * ratio[0]
        height = dpi * ratio[1]
        temp_dir = tempfile.gettempdir()
        # temp_dir = self._test_file_dir
        img_0_path = os.path.join(temp_dir, 'IPT-tptrrf-0.png')
        img_1_path = os.path.join(temp_dir, 'IPT-tptrrf-1.png')
        expected_0_size = (int(width), int(height))

        # print('file_0_size: %d' % file_0_size)
        # print('ratio: %f, %f' % (ratio[0], ratio[1]))
        # print('width: %f' % width)
        # print('height: %f' % height)

        bin_0_src = self._test_binary_src
        r_0 = helper.extract_regions(bin_0_src)

        cm_0 = BytePlot(bin_0_src, r_0)

        cm_0.plot_to_file(str(img_0_path), dpi, ratio)
        cm_0.plot_to_file(str(img_1_path), dpi)

        assert os.path.isfile(img_0_path)
        helper.assert_image_size(expected_0_size, str(img_0_path))
        os.remove(img_0_path)
        os.remove(img_1_path)

    def test_plot_to_dynamic_size_real_file(self):
        dpi = 72
        file_0_size = os.path.getsize(self._test_binary_src)
        width = file_0_size / 20
        height = 800
        temp_dir = tempfile.gettempdir()
        # temp_dir = self._test_file_dir
        img_0_path = os.path.join(temp_dir, 'IPT-tptdsrf-0.png')
        img_1_path = os.path.join(temp_dir, 'IPT-tptdsrf-1.png')
        expected_0_size = (int(width), height)

        bin_0_src = self._test_binary_src
        r_0 = helper.extract_regions(bin_0_src)

        cm_0 = BytePlot(bin_0_src, r_0)

        cm_0.plot_to_dynamic_size_file(str(img_0_path), dpi, width, height)
        cm_0.plot_to_file(str(img_1_path), dpi)

        assert os.path.isfile(img_0_path)
        helper.assert_image_size(expected_0_size, str(img_0_path))
        os.remove(img_0_path)
        os.remove(img_1_path)

    def test_plot_to_dynamic_size_real_file_dif_sizes(self):
        dpi = 100
        height = 800
        temp_dir = tempfile.gettempdir()
        # temp_dir = self._test_file_dir
        bin_0_src = self._test_binary_src
        bin_1_src = self._test_medium_binary_src
        img_0_path = os.path.join(temp_dir, 'IPT-tptdsrfds-test.png')
        img_1_path = os.path.join(temp_dir, 'IPT-tptdsrfds-test-med.png')
        file_0_size = os.path.getsize(bin_0_src) / 75
        file_1_size = os.path.getsize(bin_1_src) / 75
        expected_0_size = (int(dpi * file_0_size / PlotBase.DEFAULT_DPI), int(dpi * height / PlotBase.DEFAULT_DPI))
        expected_1_size = (int(dpi * file_1_size / PlotBase.DEFAULT_DPI), int(dpi * height / PlotBase.DEFAULT_DPI))

        r_0 = helper.extract_regions(bin_0_src)
        r_1 = helper.extract_regions(bin_1_src)

        cm_0 = BytePlot(bin_0_src, r_0)
        cm_1 = BytePlot(bin_1_src, r_1)

        cm_0.plot_to_dynamic_size_file(str(img_0_path), dpi, file_0_size, height)
        cm_1.plot_to_dynamic_size_file(str(img_1_path), dpi, file_1_size, height)

        assert os.path.isfile(img_0_path)
        assert os.path.isfile(img_1_path)
        helper.assert_image_size(expected_0_size, str(img_0_path))
        helper.assert_image_size(expected_1_size, str(img_1_path))
        os.remove(img_0_path)
        os.remove(img_1_path)

    def test_different_dpis(self):
        dpi_list = [16, 32, 64, 128, 256, 512]
        regions = self._extract_test_binary_regions()
        byte_plot = BytePlot(self._test_binary_src, regions)
        temp_dir = tempfile.gettempdir()

        for i, dpi in enumerate(dpi_list):
            img_src = self._get_image_src(temp_dir, 'IPT-byte_plot_test_file-' + str(dpi) + '.png')
            expected_size = (BytePlot.FIG_SIZE[0] * dpi, BytePlot.FIG_SIZE[1] * dpi)
            byte_plot.plot_to_file(img_src, dpi)
            helper.assert_image_size(expected_size, img_src)
            os.remove(img_src)

    def _extract_test_binary_regions(self):
        return helper.extract_regions(self._test_binary_src)

    def _get_image_src(self, src_dir, name):
        return str(os.path.join(src_dir, name))

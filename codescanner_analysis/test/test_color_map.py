# -*- coding: utf-8 -*-
import os
import pytest
import tempfile
import unittest
from _pytest.monkeypatch import MonkeyPatch
from collections import defaultdict
from collections import namedtuple

from codescanner_analysis.codescan_interface import CodescanInterface
from codescanner_analysis import ColorMap
from codescanner_analysis import PlotBase
from codescanner_analysis.test import helper


class ColorMapTest(unittest.TestCase):

    def setUp(self):
        self.test_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
        self.test_binary_src = os.path.join(self.test_file_dir, 'testfile')
        self.test_medium_binary_src = os.path.join(self.test_file_dir, 'testfile-med')
        self.greatest_test_region_value = 15
        self.create_test_regions()
        self.create_specs()
        self.color_map = ColorMap(self.test_binary_src, self._test_regions)
        self.color_map._file_size = self.greatest_test_region_value

    def create_test_regions(self):
        self._test_regions = defaultdict(list)
        self._test_regions['A'] = [(1, 2), (5, 6), (8, 9)]
        self._test_regions['B'] = [(2, 3), (6, 8), (12, self.greatest_test_region_value)]
        self._test_regions['C'] = [(3, 5), (9, 12)]

    def create_specs(self):
        self.AreaSpec = namedtuple('AreaSpec', ['id', 'label', 'dot_color', 'line_color'])
        self._specs = [
            self.AreaSpec(id='A', label='Region A', dot_color='c', line_color='#0022cc'),
            self.AreaSpec(id='B', label='Region B', dot_color='#00533f', line_color='#007760'),
            self.AreaSpec(id='C', label='Region C', dot_color='#e04000', line_color='#601000'),
            self.AreaSpec(id='D', label='Region D', dot_color='#e04000', line_color='#601000'),
        ]

    def test_not_existing_file_call(self):
        monkeypatch = MonkeyPatch()
        monkeypatch.setattr('os.path.isfile', lambda _: False)

        with pytest.raises(IOError):
            ColorMap(self.test_binary_src, self._test_regions)

        monkeypatch.undo()

    def test_convert_dict_to_list_of_areas(self):
        expected = [
            ((1, 2), 'A'),
            ((2, 3), 'B'),
            ((3, 5), 'C'),
            ((5, 6), 'A'),
            ((6, 8), 'B'),
            ((8, 9), 'A'),
            ((9, 12), 'C'),
            ((12, self.greatest_test_region_value), 'B'),
        ]

        areas = self.color_map._convert_dict_to_list_of_areas()

        assert areas == expected

    def test_create_cmap(self):
        self.color_map._area_specs = self._specs
        areas = self.color_map._convert_dict_to_list_of_areas()
        cmap = self.color_map._create_color_map(areas)

        expected = [self._specs[0].dot_color,
                    self._specs[1].dot_color,
                    self._specs[2].dot_color,
                    self._specs[0].dot_color,
                    self._specs[1].dot_color,
                    self._specs[0].dot_color,
                    self._specs[2].dot_color,
                    self._specs[1].dot_color,
                    ]

        assert cmap.colors == expected

    def test_create_bounds(self):
        areas = self.color_map._convert_dict_to_list_of_areas()
        bounds = self.color_map._create_bounds(areas)

        expected = [1, 2, 3, 5, 6, 8, 9, 12, 15]

        assert bounds == expected

    def test_create_ticks(self):
        self.color_map._file_size = 0x1000
        ticks = self.color_map._create_ticks()

        expected = [0, 0x200, 0x400, 0x600, 0x800, 0xa00, 0xc00, 0xe00, 0x1000]

        assert ticks == expected

    def test_area_list_is_padded(self):
        area_list = [((1, 2), 'Code'), ((5, 10), 'Code')]
        area_list = self.color_map._pad_area_list(area_list)

        expected = [((0, 1), 'Data'), ((1, 2), 'Code'), ((2, 5), 'Data'), ((5, 10), 'Code'), ((10, 15), 'Data')]

        assert area_list == expected

    def test_area_list_is_not_padded(self):
        area_list = self.color_map._convert_dict_to_list_of_areas()
        last_el_before_padding = area_list[len(area_list) - 1]

        area_list = self.color_map._pad_area_list(area_list)
        last_el_after_padding = area_list[len(area_list) - 1]

        assert last_el_before_padding == last_el_after_padding

    def test_spec_is_in_dictionary(self):
        test_spec = self.AreaSpec(id='ddddddE', label='Region E', dot_color='#e04000', line_color='#601000')

        assert self.color_map._spec_is_in_regions(self._specs[0].id)
        assert self.color_map._spec_is_in_regions(self._specs[1].id)
        assert self.color_map._spec_is_in_regions(self._specs[2].id)
        assert not self.color_map._spec_is_in_regions(self._specs[3].id)
        assert not self.color_map._spec_is_in_regions(test_spec.id)

    def test_plot_big_dense_area_file(self):
        '''
        To visually test the output, this method may be run with calling the _write_image method.
        Otherwise it only tests if the bytes would create a png file.
        '''
        temp_dir = tempfile.gettempdir()
        size = int(1024 * 1024 * 1000)
        test_regions = helper.create_dense_regions(size)

        bin_src = os.path.join(temp_dir, 'CMT-tpbdaf.bin')
        helper.create_random_file(bin_src, size)

        color_map = self._init_color_map(bin_src, test_regions)
        image_bytes = color_map.plot_to_buffer(100)
        # img_src = self._get_image_src(self._test_file_dir, 'tcm_test_plot_dense_area_file.png')
        # color_map._write_image(image_bytes, img_src)

        assert image_bytes.startswith(helper.MAGIC_PNG_BYTES)

        os.remove(bin_src)

    def test_plotting_empty_dict(self):
        bin_src = self.test_binary_src

        temp_dir = tempfile.gettempdir()
        bar_src = os.path.join(temp_dir, 'CMT-tped-bar.png')

        test_regions = defaultdict(list)

        color_map = self._init_color_map(bin_src, test_regions)
        image_bytes = color_map.plot_to_buffer(100)
        color_map.plot_to_file(bar_src, 100)

        assert image_bytes is ''
        assert not os.path.isfile(bar_src)

    def _init_color_map(self, bin_src, test_regions):
        color_map = ColorMap(bin_src, test_regions)
        color_map._area_specs = self._specs
        color_map._file_size = os.path.getsize(bin_src)
        color_map.PAD_AREA_ID = 'A'

        return color_map

    def test_plotting_test_file_is_png(self):
        '''
        To visually test the output, this method may be run with calling the _write_image method.
        Otherwise it only tests if the bytes would create a png file.
        '''
        regions = self._extract_test_binary_regions()

        color_map = ColorMap(self.test_binary_src, regions)
        image_bytes = color_map.plot_to_buffer(100)

        # img_src = self._get_image_src(self._test_file_dir, 'tcm_test_plotting_test_file_is_png.png')
        # color_map._write_image(image_bytes, img_src)

        assert image_bytes.startswith(helper.MAGIC_PNG_BYTES)

    def test_plot_to_file(self):
        dpi = 100
        temp_dir = tempfile.gettempdir()
        # temp_dir = self.test_file_dir
        img_path = os.path.join(temp_dir, 'CMT-tptf.png')

        expected_size = (int(dpi * ColorMap.FIG_SIZE[0]), int(dpi * ColorMap.FIG_SIZE[1]))

        regions = self._extract_test_binary_regions()
        cm = ColorMap(self.test_binary_src, regions)
        cm.plot_to_file(str(img_path), dpi)

        assert os.path.isfile(img_path)
        helper.assert_image_size(expected_size, str(img_path))

        os.remove(img_path)

    def test_plot_to_dynamic_size_random_file(self):
        dpi = 72
        file_0_size = 0x2000
        file_1_size = 0x4000
        file_2_size = os.path.getsize(self.test_binary_src)
        height = 1000

        temp_dir = tempfile.gettempdir()
        # temp_dir = self.test_file_dir

        img_0_path = os.path.join(temp_dir, 'CMT-tptdsf-0.png')
        img_1_path = os.path.join(temp_dir, 'CMT-tptdsf-1.png')
        img_2_path = os.path.join(temp_dir, 'CMT-tptdsf-2.png')

        expected_0_size = (int(dpi * file_0_size / PlotBase.DEFAULT_DPI), int(dpi * height / PlotBase.DEFAULT_DPI))
        expected_1_size = (int(dpi * file_1_size / PlotBase.DEFAULT_DPI), int(dpi * height / PlotBase.DEFAULT_DPI))
        expected_2_size = (int(dpi * file_2_size / PlotBase.DEFAULT_DPI), int(dpi * height / PlotBase.DEFAULT_DPI))

        bin_0_src = os.path.join(temp_dir, 'CMT-tptdsf-0.bin')
        bin_1_src = os.path.join(temp_dir, 'CMT-tptdsf-1.bin')
        bin_2_src = self.test_binary_src
        helper.create_random_file(bin_0_src, file_0_size)
        helper.create_random_file(bin_1_src, file_1_size)
        r_0 = helper.extract_regions(bin_0_src)
        r_1 = helper.extract_regions(bin_1_src)
        r_2 = helper.extract_regions(bin_2_src)

        cm_0 = ColorMap(bin_0_src, r_0)
        cm_1 = ColorMap(bin_1_src, r_1)
        cm_2 = ColorMap(bin_2_src, r_2)

        cm_0.plot_to_dynamic_size_file(str(img_0_path), dpi, file_0_size, height)
        cm_1.plot_to_dynamic_size_file(str(img_1_path), dpi, file_1_size, height)
        cm_2.plot_to_dynamic_size_file(str(img_2_path), dpi, file_2_size, height)

        assert os.path.isfile(img_0_path)
        assert os.path.isfile(img_1_path)
        assert os.path.isfile(img_2_path)
        helper.assert_image_size(expected_0_size, str(img_0_path))
        helper.assert_image_size(expected_1_size, str(img_1_path))
        helper.assert_image_size(expected_2_size, str(img_2_path))
        os.remove(img_0_path)
        os.remove(img_1_path)
        os.remove(img_2_path)
        os.remove(bin_0_src)
        os.remove(bin_1_src)

    def test_plot_to_dynamic_size_real_file(self):
        dpi = 72
        height = 800
        temp_dir = tempfile.gettempdir()
        # temp_dir = self.test_file_dir
        bin_0_src = self.test_binary_src
        bin_1_src = self.test_medium_binary_src
        img_0_path = os.path.join(temp_dir, 'CMT-tptdsf2-small.png')
        img_1_path = os.path.join(temp_dir, 'CMT-tptdsf2-medium.png')
        file_0_size = os.path.getsize(bin_0_src) / 50
        file_1_size = os.path.getsize(bin_1_src) / 50
        expected_0_size = (int(dpi * file_0_size / PlotBase.DEFAULT_DPI), int(dpi * height / PlotBase.DEFAULT_DPI))
        expected_1_size = (int(dpi * file_1_size / PlotBase.DEFAULT_DPI), int(dpi * height / PlotBase.DEFAULT_DPI))

        r_0 = helper.extract_regions(bin_0_src)
        r_1 = helper.extract_regions(bin_1_src)

        cm_0 = ColorMap(bin_0_src, r_0)
        cm_1 = ColorMap(bin_1_src, r_1)

        cm_0.plot_to_dynamic_size_file(str(img_0_path), dpi, file_0_size, height)
        cm_1.plot_to_dynamic_size_file(str(img_1_path), dpi, file_1_size, height)

        assert os.path.isfile(img_0_path)
        assert os.path.isfile(img_1_path)
        helper.assert_image_size(expected_0_size, str(img_0_path))
        helper.assert_image_size(expected_1_size, str(img_1_path))
        os.remove(img_0_path)
        os.remove(img_1_path)

    def test_different_dpis(self):
        dpi_list = [16, 32, 64, 128, 256, 512, 1024]
        regions = self._extract_test_binary_regions()
        cm = ColorMap(self.test_binary_src, regions)
        temp_dir = tempfile.gettempdir()

        for i, dpi in enumerate(dpi_list):
            img_src = self._get_image_src(temp_dir, 'color_map_test_file-' + str(dpi) + '.png')
            expected_size = (ColorMap.FIG_SIZE[0] * dpi, ColorMap.FIG_SIZE[1] * dpi)
            cm.plot_to_file(img_src, dpi)
            helper.assert_image_size(expected_size, img_src)
            os.remove(img_src)

    def _extract_test_binary_regions(self):
        codescanner = CodescanInterface()
        r = codescanner.run(self.test_binary_src)
        return codescanner.sanitize_regions(r)

    def _get_image_src(self, src_dir, name):
        return os.path.join(src_dir, name)

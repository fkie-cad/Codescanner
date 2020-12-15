import os
import pytest
import tempfile
import unittest

from codescanner_analysis import CodescannerAnalysisData
from byte_plot import BytePlot
from color_map import ColorMap
from plot_base import PlotBase
from test import helper


class CodescannerAnalysisDataTest(unittest.TestCase):

    def setUp(self):
        self.test_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
        self.test_file = os.path.join(self.test_file_dir, 'testfile')
        self.test_medium_binary_src = os.path.join(self.test_file_dir, 'testfile-med')

    def test_not_existing_file_call(self):
        with pytest.raises(IOError):
            CodescannerAnalysisData('not.existi.ng')

    def test_codescanner_error(self):
        file_size = os.path.getsize(self.test_file)
        _ = CodescannerAnalysisData(self.test_file, 0, file_size)

    def test_sanitize_offsets(self):
        cad = CodescannerAnalysisData(self.test_file)
        start, end = cad._sanitize_offset_numbers(10, 20)
        assert 10 == start
        assert 20 == end

        start, end = cad._sanitize_offset_numbers('10', '20')
        assert 10 == start
        assert 20 == end

        with pytest.raises(ValueError):
            cad._sanitize_offset_numbers('abc', 20)

        with pytest.raises(ValueError):
            cad._sanitize_offset_numbers(10, '0xabc')

        with pytest.raises(ValueError):
            cad._sanitize_offset_numbers(10, 0)

        with pytest.raises(ValueError):
            cad._sanitize_offset_numbers(-10, 0)

        with pytest.raises(ValueError):
            file_size = os.path.getsize(self.test_file)
            cad._sanitize_offset_numbers(file_size, file_size + 1)

    def test_necessary_fields_exist(self):
        cad = CodescannerAnalysisData(self.test_file)
        result_regions = sorted(cad.regions)
        result_sizes = sorted(cad.sizes)
        expected_regions = ['Ascii', 'Code', 'Data', 'HighEntropy', 'Zero']
        expected_sizes = ['Ascii', 'Code', 'Data', 'FileSize', 'HighEntropy', 'Zero']
        expected_filesize = os.path.getsize(self.test_file)

        assert expected_regions == result_regions
        assert expected_sizes == result_sizes
        assert expected_filesize == cad.sizes['FileSize']
        assert 'ELF' == cad.file_header

    # def test_plot_small_file(self):
    #     temp_dir = tempfile.gettempdir()
    #     bin_src = os.path.join(temp_dir, 'test_plot_small_file.bin')
    #     bar_src = os.path.join(temp_dir, 'test_plot_small_file.bar.png')
    #     img_src = os.path.join(temp_dir, 'test_plot_small_file.img.png')
    #
    #     helper.create_random_file(bin_src, 0x100)
    #
    #     cad = CodescannerAnalysisData(bin_src)
    #     bar_bytes = cad.plot_to_buffer(100, True)
    #     pic_bytes = cad.plot_to_buffer(100, False)
    #     cad.plot_to_file(bar_src, 100, True)
    #     cad.plot_to_file(img_src, 100, False)
    #
    #     assert bar_bytes == ''
    #     assert pic_bytes.startswith(helper.MAGIC_PNG_BYTES)
    #     assert not os.path.isfile(bar_src)
    #     assert os.path.isfile(img_src)
    #
    #     os.remove(bin_src)
    #     os.remove(img_src)

    def test_plot_high_entropy_file(self):
        temp_dir = tempfile.gettempdir()
        # temp_dir = self.test_file_dir
        bin_src = os.path.join(temp_dir, 'CodescannerAnalysisDataTest-test_plot_high_entropy_file.bin')
        bp_src = os.path.join(temp_dir, 'CodescannerAnalysisDataTest-test_plot_high_entropy_file.pic.png')
        bar_src = os.path.join(temp_dir, 'CodescannerAnalysisDataTest-test_plot_high_entropy_file.bar.png')

        helper.create_random_file(bin_src, 0x800)

        cad = CodescannerAnalysisData(bin_src)
        cad.regions['HighEntropy'] = [(0, 3584)]

        bar_bytes = cad.plot_to_buffer(100, cad.COLOR_MAP)
        bp_bytes = cad.plot_to_buffer(100, cad.BYTE_PLOT)
        cad.plot_to_file(bar_src, 100, cad.COLOR_MAP)
        cad.plot_to_file(bp_src, 100, cad.BYTE_PLOT)

        assert bar_bytes.startswith(helper.MAGIC_PNG_BYTES)
        assert bp_bytes.startswith(helper.MAGIC_PNG_BYTES)
        assert os.path.isfile(bar_src)
        assert os.path.isfile(bp_src)

        os.remove(bin_src)
        os.remove(bar_src)
        os.remove(bp_src)

    def test_plot_to_buffer_color_map(self):
        '''
        To visually test the output, this method may be run with calling the _write_image method.
        Otherwise it only tests if the bytes would create a png file.
        '''
        cad = CodescannerAnalysisData(self.test_file)
        pic_bytes = cad.plot_to_buffer(100, cad.COLOR_MAP)
        # test_img = self._get_image_src(self._test_file_dir, 'ccsat_test_plot_to_buffer_color_bar.png')
        # cad.write_image(pic_bytes, test_img)

        assert pic_bytes.startswith(helper.MAGIC_PNG_BYTES)

    def test_plot_to_buffer_byte_plot(self):
        '''
        To visually test the output, this method may be run with calling the _write_image method.
        Otherwise it only tests if the bytes would create a png file.
        '''
        cad = CodescannerAnalysisData(self.test_file)
        pic_bytes = cad.plot_to_buffer(100, cad.BYTE_PLOT)

        assert pic_bytes.startswith(helper.MAGIC_PNG_BYTES)

    def test_plot_to_buffer_dynamic_size_image(self):
        '''
        To visually test the output, this method may be run with calling the _write_image method.
        Otherwise it only tests if the bytes would create a png file.
        '''
        dpi = 72
        ratio = 50
        file_0_size = os.path.getsize(self.test_file)
        file_1_size = os.path.getsize(self.test_medium_binary_src)
        width_0 = file_0_size / ratio
        width_1 = file_1_size / ratio
        height = 800
        # temp_dir = tempfile.gettempdir()
        # temp_dir = self._test_file_dir
        # img_0_path = os.path.join(temp_dir, 'CAT-tptbds-test-small.png')
        # img_1_path = os.path.join(temp_dir, 'CAT-tptbds-test-med.png')

        # expected_0_size = (int(dpi * width_0 / PlotBase.DEFAULT_DPI), int(dpi * height / PlotBase.DEFAULT_DPI))
        # expected_1_size = (int(dpi * width_1 / PlotBase.DEFAULT_DPI), int(dpi * height / PlotBase.DEFAULT_DPI))

        cad = CodescannerAnalysisData(self.test_file)
        buffer0 = cad.plot_to_dynamic_size_buffer(dpi, width_0, height)

        cad = CodescannerAnalysisData(self.test_medium_binary_src)
        buffer1 = cad.plot_to_dynamic_size_buffer(dpi, width_1, height)

        # self._write_image(buffer0, str(img_0_path))
        # self._write_image(buffer1, str(img_1_path))

        assert buffer0.startswith(helper.MAGIC_PNG_BYTES)
        assert buffer1.startswith(helper.MAGIC_PNG_BYTES)

        # assert os.path.isfile(img_0_path)
        # assert os.path.isfile(img_1_path)

    def _write_image(self, image_bytes, file_name):
        f = open(file_name, 'wb')
        f.write(image_bytes)
        f.close()

    def test_plot_to_file_color_map_plot(self):
        dpi = 100
        temp_dir = tempfile.gettempdir()
        # temp_dir = self.test_file_dir
        img_path = os.path.join(temp_dir, 'CodescannerAnalysisDataTest-test_plot_to_file_color_map_plot.png')
        expected_size = (dpi * ColorMap.FIG_SIZE[0], dpi * ColorMap.FIG_SIZE[1])

        cad = CodescannerAnalysisData(self.test_file)
        cad.plot_to_file(str(img_path), dpi, cad.COLOR_MAP)

        assert os.path.isfile(img_path)
        helper.assert_image_size(expected_size, str(img_path))

        os.remove(img_path)

    def test_plot_to_file_byte_plot(self):
        dpi = 100
        temp_dir = tempfile.gettempdir()
        # temp_dir = self.test_file_dir
        img_path = os.path.join(temp_dir, 'CodescannerAnalysisDataTest-test_plot_to_file_byte_plot.png')
        expected_size = (dpi * BytePlot.FIG_SIZE[0], dpi * BytePlot.FIG_SIZE[1])
        p_file = self.test_file

        cad = CodescannerAnalysisData(p_file)
        cad.plot_to_file(str(img_path), dpi, cad.BYTE_PLOT)

        assert os.path.isfile(img_path)
        helper.assert_image_size(expected_size, str(img_path))

        os.remove(img_path)

    def test_plot_to_file_byte_plot_big_file(self):
        dpi = 100
        temp_dir = tempfile.gettempdir()
        # temp_dir = self.test_file_dir
        img_path = os.path.join(temp_dir, 'CodescannerAnalysisDataTest-test_plot_to_file_byte_plot_big_file.png')
        expected_size = (dpi * BytePlot.FIG_SIZE[0], dpi * BytePlot.FIG_SIZE[1])
        big_file = temp_dir+"big.bin"
        helper.create_random_file(big_file, (10 * 1024 * 1024))  # 10 mb

        cad = CodescannerAnalysisData(big_file)
        cad.plot_to_file(str(img_path), dpi, cad.BYTE_PLOT)

        assert os.path.isfile(img_path)
        helper.assert_image_size(expected_size, str(img_path))

        os.remove(big_file)
        os.remove(img_path)

    def test_plot_to_buffer_dynamic_size_error(self):
        cad = CodescannerAnalysisData(self.test_file)

        self.assertRaises(ValueError, cad.plot_to_dynamic_size_buffer, 0, 1, cad.BYTE_PLOT)
        self.assertRaises(ValueError, cad.plot_to_dynamic_size_buffer, 1, 0, cad.BYTE_PLOT)
        self.assertRaises(ValueError, cad.plot_to_dynamic_size_buffer, 1, 1, cad.BYTE_PLOT)

    def test_plot_to_file_dynamic_size(self):
        dpi = 72
        ratio = 50
        file_0_size = os.path.getsize(self.test_file)
        file_1_size = os.path.getsize(self.test_medium_binary_src)
        width_0 = file_0_size / ratio
        width_1 = file_1_size / ratio
        height = 800
        temp_dir = tempfile.gettempdir()
        # temp_dir = self.test_file_dir
        img_0_path = os.path.join(temp_dir, 'CAT-tptfds-test-small.png')
        img_1_path = os.path.join(temp_dir, 'CAT-tptfds-test-med.png')

        expected_0_size = (int(dpi * width_0 / PlotBase.DEFAULT_DPI), int(dpi * height / PlotBase.DEFAULT_DPI))
        expected_1_size = (int(dpi * width_1 / PlotBase.DEFAULT_DPI), int(dpi * height / PlotBase.DEFAULT_DPI))

        cad = CodescannerAnalysisData(self.test_file)
        cad.plot_to_dynamic_size_file(str(img_0_path), dpi, width_0, height)

        cad = CodescannerAnalysisData(self.test_medium_binary_src)
        cad.plot_to_dynamic_size_file(str(img_1_path), dpi, width_1, height)

        assert os.path.isfile(img_0_path)
        assert os.path.isfile(img_1_path)

        # print("expected_0_size: %s" % str(expected_0_size))
        # print("expected_1_size: %s" % str(expected_1_size))

        helper.assert_image_size(expected_0_size, str(img_0_path))
        helper.assert_image_size(expected_1_size, str(img_1_path))

        os.remove(img_0_path)
        os.remove(img_1_path)

    def test_tilde_file_src_path(self):
        '''
        Should cover all possible paths where the user supplied source is used,
        since file_src is expanded in the constructor.
        '''
        file_name = 'what/ever.exe'
        file_src = '~/' + file_name

        home = os.path.expanduser("~")
        expected = os.path.join(home, file_name)

        try:
            CodescannerAnalysisData(file_src)
        except IOError as e:
            assert str(e) == 'IOError: Source file does not exist: ' + expected

    def test_not_supported_file_plot(self):
        dpi = 100
        temp_dir = tempfile.gettempdir()
        unsupported = os.path.join(temp_dir, 'CodescannerAnalysisDataTest-est_not_supported_file_plot_in.png')

        cad = CodescannerAnalysisData(self.test_file)
        cad.plot_to_file(str(unsupported), dpi, True)

        # img_path2 = self._get_image_src(self._test_file_dir, 'test_not_supported_file_plot.png')
        img_path2 = os.path.join(temp_dir, 'CodescannerAnalysisDataTest-test_not_supported_file_plot_out.png')
        cad = CodescannerAnalysisData(unsupported)
        cad.plot_to_file(img_path2, dpi, True)
        pic_bytes = cad.plot_to_buffer(dpi, True)

        assert pic_bytes.startswith(helper.MAGIC_PNG_BYTES)

        os.remove(unsupported)
        os.remove(img_path2)

    def test_plot_with_offsets(self):
        dpi = 100
        temp_dir = tempfile.gettempdir()
        # temp_dir = self._test_file_dir
        img_path = os.path.join(temp_dir, 'CodescannerAnalysisDataTest-test_plot_with_offsets-dot.png')
        bar_path = os.path.join(temp_dir, 'CodescannerAnalysisDataTest-test_plot_with_offsets-bar.png')

        start = 144640
        end = 184320

        cad = CodescannerAnalysisData(self._test_binary_src, start, end)
        cad.plot_to_file(str(img_path), dpi, cad.BYTE_PLOT)
        cad.plot_to_file(str(bar_path), dpi, cad.COLOR_MAP)

        assert os.path.isfile(img_path)
        assert os.path.isfile(bar_path)

        os.remove(img_path)
        os.remove(bar_path)

    def _get_image_src(self, src_dir, name):
        return os.path.join(src_dir, name)

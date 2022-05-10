# -*- coding: utf-8 -*-
import copy
import io
import os
import time
import warnings
from collections import namedtuple

import matplotlib

import codescanner_analysis.utils.file_utils as file_utils
from codescanner_analysis.codescan_interface import CodescanInterface

matplotlib.use('agg')

from matplotlib.pyplot import clf
from pylab import savefig, close


class PlotBase(object):
    # less than 2¹⁶ in each direction = 0x10000 * 0x10000 = 0x100000000
    MAX_PLOT_AXIS_SIZE = 0x10000
    DEFAULT_DPI = 72
    MIN_DPI = 10

    AreaSpec = namedtuple('AreaSpec', ['id', 'label', 'dot_color', 'line_color'])
    AREAS = [
        AreaSpec(id='Code', label='Code', dot_color='#00bfbf', line_color='#0022cc'),
        AreaSpec(id='AlienCode', label='Alien Code', dot_color='#00533f', line_color='#007760'),
        AreaSpec(id='Ascii', label='Ascii/Strings', dot_color='#e04000', line_color='#601000'),
        AreaSpec(id='HighEntropy', label='High-Entropy', dot_color='#3d0089', line_color='k'),
        AreaSpec(id='Zero', label='Padding/Zero', dot_color='#c0c0c0', line_color='#5d5d5d'),
        AreaSpec(id='Data', label='Generic Data', dot_color='#bfbf00', line_color='#323300'),
    ]

    def __init__(self, file_name, regions):
        self._set_file_attributes(file_name)
        self._regions = copy.deepcopy(regions)
        self._area_specs = PlotBase.AREAS
        self._offsets = (0, 0)

    def __del__(self):
        self._regions = None
        self._area_specs = None
        self._offsets = None

    def _set_file_attributes(self, file_name):
        file_name = file_utils.sanitize_file_name(file_name)
        self._file_size = os.path.getsize(file_name)
        self._short_filename = os.path.basename(file_name)

    def update_code_spec_label(self, code_regions):
        '''
        Update code spec label to actual architecture(s).
        '''
        if not code_regions or len(code_regions) == 0 or len(code_regions[0]) < 5:
            return

        architectures = set()
        for r in code_regions:
            arch = CodescanInterface.get_architecture(r)
            if arch["Full"]:
                architectures.add(arch["Full"])

        architectures = list(sorted(architectures))
        label = ""
        size = len(architectures)
        for i in range(size):
            label = label + architectures[i] + ", "
        if len(label) > 3:
            label = label[0:len(label)-2]
        self._update_spec_label(0, label)

    def update_alien_code_spec_label(self, architecture):
        '''
        Update alien code spec label to an actual architecture.
        '''
        self._update_spec_label(1, architecture)

    def _update_spec_label(self, idx, value):
        if value is None:
            return

        self._area_specs[idx] = self._area_specs[idx]._replace(label=value)

    def plot_to_file(self, file_name, dpi, fig_size=None):
        '''
        Plot to a file.

        :param file_name: the image file name
        :param dpi: the desired dpi resolution
        :param fig_size: fig_size ratio
        :return:
        '''
        file_name = file_utils.sanitize_file_name(file_name, False)

        b = self.plot_to_buffer(dpi, fig_size)
        if b != '':
            self._write_image(b, file_name)

    def plot_to_dynamic_size_file(self, file_name, dpi, width, height):
        '''
        Plot to a file with dynamic width and height

        :param file_name: the image file name
        :param dpi: the desired dpi resolution
        :param width: the desired width
        :param height: the desired height
        :return:
        '''

        file_name = file_utils.sanitize_file_name(file_name, False)

        b = self.plot_to_dynamic_size_buffer(dpi, width, height)
        if b != '':
            self._write_image(b, file_name)

    def _determine_resolution(self, filesize):
        tik = filesize
        resolution = 0x100
        if filesize > 0x100:
            while tik > 50:
                tik = filesize / resolution
                resolution += 0x100

        return resolution

    def _save_plot_to_buffer(self, plot, dpi):
        warnings.filterwarnings('ignore', module='matplotlib')
        output_buffer = io.BytesIO()
        savefig(output_buffer, dpi=dpi, format='png')

        raw_output = output_buffer.getvalue()
        output_buffer.close()

        clf()
        close(plot)

        time.sleep(0.5)

        return raw_output

    def _write_image(self, image_bytes, file_name):
        '''
        Write raw image bytes to a file.

        :param image_bytes: the image bytes
        :param file_name: the full file path of the resulting image
        '''
        f = open(file_name, 'wb')
        f.write(image_bytes)
        f.close()

# -*- coding: utf-8 -*-
import os

import matplotlib
import numpy

from codescanner_analysis.codescan_interface import CodescanInterface

matplotlib.use('agg')

from matplotlib.pyplot import legend
from matplotlib.ticker import MultipleLocator, FuncFormatter
from pylab import xticks, figure, sca

from codescanner_analysis.plot_base import PlotBase

# This is the minimum for which it makes sense to analyze or plot a file.
# No way to have an X-axis for a couple of bytes only. Applies to both colormap and byteplots.
MIN_FILE_SIZE = 0x100


class BytePlot(PlotBase):
    FIG_SIZE = (16, 8)
    filesize = 0

    def __init__(self, file_name, regions):
        super(BytePlot, self).__init__(file_name, regions)
        self.ms = 1
        self.filesize = os.path.getsize(file_name)

    def __del__(self):
        pass

    def plot_to_buffer(self, dpi, fig_size=None):
        '''
        Plot image with fixed (16:8) size to buffer.
        :param dpi: the disired dpi
        :param fig_size: the size ratio of the figure. Will be multiplied with dpi, to get the real size.
        :return:
        '''
        if (self.filesize < MIN_FILE_SIZE):
            raise IOError("File is too small to even have a proper x-axis!")

        if dpi < PlotBase.MIN_DPI:
            raise ValueError("DPI must be at mimimum %d!" % PlotBase.MIN_DPI)

        if fig_size is None:
            fig_size = self.FIG_SIZE

        return self._plot_to_buffer(dpi, fig_size)

    def plot_to_dynamic_size_buffer(self, dpi, width, height):
        '''
        Plot image with desired widht and height to buffer.
        A dpi of 72 will plot a file with the expected with and height.

        :param dpi: The desired dpi.
        :param width: The desired width.
        :param height: The desired heigth.
        :return:
        '''

        if self.filesize < MIN_FILE_SIZE:
            raise IOError("File is too small to even have a proper x-axis!")

        if dpi < PlotBase.MIN_DPI:
            raise ValueError("DPI must be at mimimum %d!" % PlotBase.MIN_DPI)
        if width == 0:
            raise ValueError("Width must not be zero!")
        if height == 0:
            raise ValueError("Height must not be zero!")

        # a small dpi crashes font calculation
        # that's why dpi should not be 1 and width is divided by it
        width = width / float(PlotBase.DEFAULT_DPI)
        height = height / float(PlotBase.DEFAULT_DPI)

        fig_size = (width, height)

        # if width * height * dpi > PIL.Image.MAX_IMAGE_PIXELS:
        #     raise ValueError("Image size to big!")
        # if width * dpi > PlotBase.MAX_PLOT_AXIS_SIZE:
        #     raise ValueError("Width to big!")
        # if height * dpi > PlotBase.MAX_PLOT_AXIS_SIZE:
        #     raise ValueError("Height to big!")

        return self._plot_to_buffer(dpi, fig_size)

    def _plot_to_buffer(self, dpi, fig_size):

        if (self.filesize < MIN_FILE_SIZE):
            raise IOError("File is too small to even have a proper x-axis!")

        byte_array = self._get_byte_array()
        byte_indices = numpy.arange(0, byte_array.size, dtype=numpy.uint32)

        # marker size depends on height of fig
        # prevents visually unpleasant gabs between dots, if fig is stretched in height more than the sum of normal dot size
        # unused: somehow overwrites markerfacecolor if markersize is set in plot
        # self.ms = self.height / 1.8
        self.ms = 72. / dpi

        plot = figure(figsize=fig_size)
        subplot = plot.add_subplot(111)  # (Add bottom image)
        # subplot.axis('off')
        self._generate_plot(byte_array, byte_indices, subplot)
        plot.tight_layout()

        legend(loc='upper right')

        return self._save_plot_to_buffer(plot, dpi)

    def _get_byte_array(self):
        byte_array = numpy.fromfile(self._file_name, dtype=numpy.uint8)
        if byte_array is None:
            raise RuntimeError('Source file seems to be empty: {}'.format(self._file_name))

        if self._offsets[1] != 0:
            byte_array = byte_array[self._offsets[0]:self._offsets[1]]

        return byte_array

    def _generate_plot(self, byte_array, byte_indices, subplot):
        self._prepare_axes(subplot)

        subplot.plot(byte_indices, byte_array, '.', markerfacecolor='y', markeredgecolor='#323300')
        for spec in self._area_specs:
            self._plot_byte_regions(subplot, byte_array, byte_indices, spec)

        if self._regions.get("Code"):
            for cr in self._regions.get("Code"):
                self._plot_cr_label(subplot, cr)

        self._add_labels(subplot)

    def _prepare_axes(self, ax):
        resolution = self._determine_resolution(self._file_size)

        major_locator_x = MultipleLocator(resolution)
        major_locator_y = MultipleLocator(0x10)  # mark every 0x10 bytes

        major_formatter_x = FuncFormatter(lambda x, _: '0x%X' % int(x + self._offsets[0]))
        major_formatter_y = FuncFormatter(lambda x, _: '0x%X' % int(x))

        ax.axis([0, self._file_size, 0, 0x100])

        ax.xaxis.set_major_locator(major_locator_x)
        ax.xaxis.set_major_formatter(major_formatter_x)

        ax.yaxis.set_major_locator(major_locator_y)
        ax.yaxis.set_major_formatter(major_formatter_y)

    def _plot_byte_regions(self, ax, raw_bytes, byte_indices, area_spec):

        if area_spec.id not in self._regions: return

        sca(ax)

        set_label = True
        for region in self._regions[area_spec.id]:
            start = region[0]
            end = region[1]

            points = byte_indices[byte_indices >= start]
            points = points[points < end]

            x_axis = byte_indices[points]  # Offsets of points
            y_axis = raw_bytes[points]  # Associated values

            if set_label:
                ax.plot(x_axis, y_axis, '.', markerfacecolor=area_spec.dot_color, markeredgecolor=area_spec.line_color,
                        label=area_spec.label
                        # , markersize=self.ms  # somehow overwrites markerfacecolor
                        )
                set_label = False
            else:
                ax.plot(x_axis, y_axis, '.', markerfacecolor=area_spec.dot_color, markeredgecolor=area_spec.line_color,
                        # markersize=self.ms  # somehow overwrites markerfacecolor
                        )
            ax.axvline(x=start, ymin=0, ymax=255, linewidth=1.0, color=area_spec.line_color)
            ax.axvline(x=end, ymin=0, ymax=255, linewidth=1.0, color=area_spec.line_color)

    def _plot_cr_label(self, ax, cr):
        spec = self._area_specs[0]
        x = cr[0]
        y = 2
        label = CodescanInterface.get_architecture(cr)["Full"]

        ax.text(x, y, label, fontsize=10, color='#000000',
                bbox=dict(facecolor=spec.dot_color, alpha=0.75, pad=1, linewidth=0,
                          edgecolor='b'))

    def _add_labels(self, subplot):
        subplot.set_xlabel('Byte location')
        subplot.set_ylabel('Byte value')
        subplot.set_title('{} ({} kB)'.format(self._short_filename, round(1.0 * (self._file_size / 1024))))
        xticks(rotation=315)

    def _build_filename(self, resultdir):
        '''
        Usage???
        :param resultdir:
        :return:
        '''
        fi_splitext = os.path.splitext(self._short_filename)

        if fi_splitext[1]:
            filename_template = '{}_{}'.format(fi_splitext[0], fi_splitext[1][1:])  # dot-extension
        else:
            filename_template = fi_splitext[0]  # Elf-Binaries without dot-extension

        return os.path.join(resultdir, '{}.png'.format(filename_template))

    def _set_file_attributes(self, file_name):
        super(BytePlot, self)._set_file_attributes(file_name)

        self._file_name = os.path.expanduser(file_name)

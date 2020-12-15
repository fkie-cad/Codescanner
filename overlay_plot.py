# -*- coding: utf-8 -*-
import matplotlib
import numpy
import os
from collections import namedtuple, defaultdict
from matplotlib import patches

matplotlib.use('agg')

from matplotlib.pyplot import legend
from matplotlib.ticker import MultipleLocator, FuncFormatter
from pylab import xticks, figure, GridSpec
from byte_plot import BytePlot


class OverlayPlot(BytePlot):
    XAreaSpec = namedtuple('AreaSpec', ['id', 'label', 'color', 'box_color', 'alpha'])
    x_spec = XAreaSpec(id='exec', label='', color='#ff0000', box_color='#ffcccc', alpha=0.5)
    text_spec = XAreaSpec(id='.text', label='.text', color='#ff0000', box_color='#ffcccc', alpha=0.75)

    FIG_SIZE = (16, 8)

    def __init__(self, file_name, cs_regions, x_regions):
        '''
        Plot codescan parsed cs_regions and underlay the plot with headerParser parsed executable x_regions.

        :param file_name: the binary file's name
        :param cs_regions: the codescanner regions
        :param x_regions: the headerParser regions
        '''
        super(OverlayPlot, self).__init__(file_name, cs_regions)
        self._x_regions = x_regions
        self._x_area_specs = []
        self._fill_up_x_area_specs()
        self._extending_x_regions = defaultdict(list)
        self._sanitize_x_regions(file_name)

    def __del__(self):
        self._x_regions = None
        self._x_area_specs = None
        self._extending_x_regions = None

    def _fill_up_x_area_specs(self):
        '''
        Fill up the _x_area_specs array with x_region types.
        '''
        self._x_area_specs.append(self.text_spec)
        for key in self._x_regions:
            if key != ".text":
                spec = self.x_spec._replace(id=key, label=key)
                self._x_area_specs.append(spec)

    def _sanitize_x_regions(self, file_name):
        '''
        Delete x_regions, greater than the file size and put them into a separate dictionary.
        '''
        file_size = os.path.getsize(file_name)
        delete_keys = []
        for key in self._x_regions:
            delete_ids = []
            for i in range(len(self._x_regions[key])):
                r = self._x_regions[key][i]
                if r[1] > file_size:
                    self._extending_x_regions[key].append(r)
                if r[0] > file_size:
                    delete_ids.append(i)

            for d in delete_ids:
                del self._x_regions[key][d]

            if len(self._x_regions[key]) == 0:
                delete_keys.append(key)

        for key in delete_keys:
            del self._x_regions[key]

    def plot_to_buffer(self, dpi, fig_size=None):
        if fig_size is None:
            fig_size = self.FIG_SIZE

        return self._plot_to_buffer(dpi, fig_size)

    def _plot_to_buffer(self, dpi, fig_size):
        byte_array = self._get_byte_array()
        byte_indices = numpy.arange(0, byte_array.size, dtype=numpy.uint32)

        byte_plot_row_span = self._calculate_byte_plot_row_span()

        plot = figure(figsize=fig_size)
        grid = GridSpec(3, 1, hspace=0.3, wspace=0.0)

        byte_plot = plot.add_subplot(grid[0:byte_plot_row_span, :])
        self._generate_plot(byte_array, byte_indices, byte_plot)

        legend(loc='upper right')

        if byte_plot_row_span == 2:
            extending_x_plot = plot.add_subplot(grid[2:3, :])
            self._generate_extended_plot(extending_x_plot)

            legend(loc='upper right')

        plot.subplots_adjust(left=0.05, right=0.98, top=0.95, bottom=0.11, hspace=0.0)

        return self._save_plot_to_buffer(plot, dpi)

    def _calculate_byte_plot_row_span(self):
        if self._extending_x_regions:
            return 2
        return 3

    def _generate_plot(self, byte_array, byte_indices, subplot):
        self._prepare_axes(subplot)

        subplot.plot(byte_indices, byte_array, '.', markerfacecolor='y', markeredgecolor='#323300')
        for spec in self._area_specs:
            self._plot_byte_regions(subplot, byte_array, byte_indices, spec)

        i = 0
        for spec in self._x_area_specs:
            i = self._plot_x_regions(subplot, spec, i, self._x_regions)

        self._add_labels(subplot)

    def _generate_extended_plot(self, subplot):
        self._prepare_extended_axes(subplot)

        i = 0
        for spec in self._x_area_specs:
            i = self._plot_x_regions(subplot, spec, i, self._extending_x_regions)

        self._add_extended_labels(subplot)

    def _prepare_extended_axes(self, ax):
        maximum, minimum = self._get_extended_borders()
        resolution = self._determine_resolution(self._file_size)

        majorLocatorx = MultipleLocator(resolution)
        majorLocatory = MultipleLocator(0x10)  # mark every 0x10 bytes

        majorFormatter = FuncFormatter(lambda x, _: '0x%X' % int(x))

        ax.axis([minimum, self._file_size + minimum, 0, 0x100])
        # ax.axis([minimum, maximum, 0, 0x100])

        ax.xaxis.set_major_locator(majorLocatorx)
        ax.xaxis.set_major_formatter(majorFormatter)

        ax.yaxis.set_major_locator(majorLocatory)
        ax.yaxis.set_major_formatter(majorFormatter)

    def _get_extended_borders(self):
        minimum = float("inf")
        maximum = 0
        for k in self._extending_x_regions:
            for r in self._extending_x_regions[k]:
                if r[0] < minimum:
                    minimum = r[0]
                if r[1] > maximum:
                    maximum = r[1]
        return maximum, minimum

    def _plot_x_regions(self, ax, spec, i, x_regions):
        if spec.id not in x_regions:
            return i

        fs = 10

        for r in x_regions[spec.id]:
            start = r[0]
            end = r[1]
            w = end - start
            box_y = i * fs * 0.65

            spec = self._mark_small_regions(spec, w)
            label = self._get_x_legend_label(spec)

            rect = patches.Rectangle((start, 0), w, 0x100, linewidth=0, edgecolor='b', facecolor=spec.color,
                                     alpha=spec.alpha, label=label)
            ax.add_patch(rect)
            ax.text(start, box_y, spec.label, fontsize=fs, bbox=dict(facecolor=spec.box_color, alpha=0.75,
                                                                     pad=1, linewidth=0, edgecolor='b'))

            i += 1

        return i

    def _mark_small_regions(self, spec, w):
        if w < 0x50:
            spec = spec._replace(alpha=0.25)
        return spec

    def _get_x_legend_label(self, spec):
        '''
        Handling legend feature to skip label starting with an '_'.
        '''
        label = spec.label
        if label[0] == '_':
            label = " " + label
        return label

    def _add_extended_labels(self, subplot):
        subplot.set_xlabel('Byte location')
        subplot.set_ylabel('Byte value')
        # subplot.set_title('{} ({} kB)'.format(self._short_filename, round(1.0 * (self._file_size / 1024))))
        xticks(rotation=315)

    # def _add_labels(self, subplot):
    #     subplot.set_xlabel('Byte location')
    #     subplot.set_ylabel('Byte value')
    #     subplot.set_title('{} ({} kB)'.format(self._short_filename, round(1.0 * (self._file_size / 1024))))
    #     xticks(rotation=315)

    # def _build_filename(self, resultdir):
    #     '''
    #     Usage???
    #     :param resultdir:
    #     :return:
    #     '''
    #     fi_splitext = os.path.splitext(self._short_filename)
    #
    #     if fi_splitext[1]:
    #         filename_template = '{}_{}'.format(fi_splitext[0], fi_splitext[1][1:])  # dot-extension
    #     else:
    #         filename_template = fi_splitext[0]  # Elf-Binaries without dot-extension
    #
    #     return os.path.join(resultdir, '{}.png'.format(filename_template))

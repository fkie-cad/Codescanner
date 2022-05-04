import os
import matplotlib as mpl

mpl.use('agg')

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from codescanner_analysis.plot_base import PlotBase

# This is the minimum for which it makes sense to analyze or plot a file.
# No way to have an X-axis for a couple of bytes only. Applies to both colormap and byteplots.
MIN_FILE_SIZE = 0x100


class ColorMap(PlotBase):
    FIG_SIZE = (16, 3.5)
    filesize = 0
    PAD_AREA_ID = 'Data'

    def __init__(self, file_name, regions):
        super(ColorMap, self).__init__(file_name, regions)
        self.filesize = os.path.getsize(file_name)

    def __del__(self):
        pass

    def plot_to_buffer(self, dpi, fig_size=None):
        
        if (self.filesize < MIN_FILE_SIZE):
            raise IOError("File is too small to even have a proper x-axis!")
        
        if (dpi < PlotBase.MIN_DPI):
            raise ValueError("DPI must be at mimimum %d!" % PlotBase.MIN_DPI)

        if (fig_size is None):
            fig_size = self.FIG_SIZE
        
        return self._plot_to_buffer(dpi, fig_size)

    def plot_to_dynamic_size_buffer(self, dpi, width, height):
        
        if (self.filesize < MIN_FILE_SIZE):
            raise IOError("File is too small to even have a proper x-axis!")
        
        if (dpi < PlotBase.MIN_DPI):
            raise ValueError("DPI must be at mimimum %d!" % PlotBase.MIN_DPI)
            
        if (width == 0):
            raise ValueError("Width must not be zero!")
            
        if (height == 0):
            raise ValueError("Height must not be zero!")

        width = width / float(self.DEFAULT_DPI)
        height = height / float(self.DEFAULT_DPI)
        fig_size = (width, height)

        # if width * dpi > PlotBase.MAX_PLOT_AXIS_SIZE:
        #     raise ValueError("Width to big!")
        # if height * dpi > PlotBase.MAX_PLOT_AXIS_SIZE:
        #     raise ValueError("Height to big!")

        return self._plot_to_buffer(dpi, fig_size)

    def _plot_to_buffer(self, dpi, fig_size):
        
        if (self.filesize < MIN_FILE_SIZE):
            raise IOError("File is too small to even have a proper x-axis!")
        
        if len(self._regions) == 0:
            return ''

        plot = self._create_plot(fig_size)

        return self._save_plot_to_buffer(plot, dpi)

    def _create_plot(self, fig_size):
        ax, plot = self._init_plot(fig_size)
        cb, ticks = self._create_bar(ax)
        self._add_labels(cb, ticks)

        return plot

    def _init_plot(self, fig_size):
        plot = plt.figure(figsize=fig_size)
        _, ax = plt.subplots(figsize=fig_size)
        # plt.subplots_adjust(left=0.05, right=0.98, top=.80, bottom=0.35, hspace=0.1)
        # plot.tight_layout()
        pad = 4.2 + self._file_size.bit_length() / 30.0
        plt.tight_layout(pad=pad, w_pad=0.0, h_pad=0.0)
        return ax, plot

    def _create_bar(self, ax):
        area_list = self._convert_dict_to_list_of_areas()
        area_list = self._pad_area_list(area_list)
        cmap = self._create_color_map(area_list)
        bounds = self._create_bounds(area_list)
        ticks = self._create_ticks()

        norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
        cb = mpl.colorbar.ColorbarBase(ax,
                                       cmap=cmap,
                                       norm=norm,
                                       boundaries=bounds,
                                       ticks=ticks,
                                       spacing='proportional',
                                       orientation='horizontal')

        return cb, ticks

    def _convert_dict_to_list_of_areas(self):
        '''
        The regions dictionary will be converted into a list of ascending region tuples.
        The tuples contain the region tuple (start, end) and the area label.
        '''
        areas = []

        for idx in self._regions:
            for r in self._regions[idx]:
                areas.append((r, idx))

        areas.sort(key=lambda tup: tup[0][0])

        return areas

    def _pad_area_list(self, areas):
        '''
        Fill up area gaps with PAD_AREA_ID.
        '''
        self._pad_first_area(areas)
        self._pad_last_area(areas)
        self._pad_mid_areas(areas)

        return areas

    def _pad_first_area(self, areas):
        first_el = areas[0]
        if first_el[0][0] != 0:
            pad_el = ((0, first_el[0][0]), self.PAD_AREA_ID)
            areas.insert(0, pad_el)

    def _pad_last_area(self, areas):
        last_el = areas[len(areas) - 1]
        if last_el[0][1] < self._file_size:
            pad_el = ((last_el[0][1], self._file_size), self.PAD_AREA_ID)
            areas.append(pad_el)

    def _pad_mid_areas(self, areas):
        paddings = []
        for i in range(len(areas) - 1):
            act_el = areas[i]
            next_el = areas[i + 1]
            if self._area_has_gap_to_next_area(act_el, next_el):
                pad = ((act_el[0][1], next_el[0][0]), self.PAD_AREA_ID)
                paddings.append(pad)
        areas.extend(paddings)
        areas.sort(key=lambda tup: tup[0][0])

    def _area_has_gap_to_next_area(self, act, next_el):
        return act[0][1] != next_el[0][0]

    def _create_color_map(self, area_list):
        colors = []
        for a in area_list:
            a_id = a[1]
            # maybe there is a better way to find the corresponding spec
            spec = [s for s in self._area_specs if s.id == a_id]
            colors.append(spec[0].dot_color)

        return mpl.colors.ListedColormap(colors)

    def _create_bounds(self, area_list):
        bounds = []
        for a in area_list:
            bounds.append(a[0][0])

        # the end position of the last region
        bounds.append(area_list[len(area_list) - 1][0][1])

        return bounds

    def _create_ticks(self):
        '''
        Create evenly distributed ticks relative to the file size.
        '''
        tick_step = self._determine_resolution(self._file_size)
        ticks = [i for i in range(0, self._file_size + 1, tick_step)]

        return ticks

    def _add_labels(self, cb, ticks):
        cb.set_label('Byte location')
        cb.ax.set_title('{} ({} kB)'.format(self._short_filename, self._get_printable_file_size()))
        self._set_tick_format(cb.ax, ticks)
        self._add_legend()

    def _get_printable_file_size(self):
        return round(1.0 * (self._file_size / 1024))

    def _set_tick_format(self, ax, ticks):
        hex_ticks = ["0x%04x" % (t + self._offsets[0]) for t in ticks]
        formatter = mpl.ticker.FixedFormatter(hex_ticks)
        ax.xaxis.set_major_formatter(formatter)

        ax.xaxis.set_tick_params(rotation=-60)
        ax.xaxis.set_tick_params(labelsize=10)

        plt.setp(ax.xaxis.get_majorticklabels(), ha="left", rotation_mode="anchor")

    def _add_legend(self):
        handles = []
        for s in self._area_specs:
            if self._spec_is_in_regions(s.id):
                handles.append(mpatches.Patch(color=s.dot_color, label=s.label))

        plt.legend(handles=handles, loc='upper right')

    def _spec_is_in_regions(self, id):
        if self._regions.get(id):
            return len(self._regions.get(id)) > 0
        else:
            return False

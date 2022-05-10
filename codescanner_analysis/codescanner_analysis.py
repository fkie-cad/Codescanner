# -*- coding: utf-8 -*-
import os

from codescanner_analysis.utils import file_utils
from codescanner_analysis.codescan_interface import CodescanInterface
from codescanner_analysis.color_map import ColorMap
from codescanner_analysis.extended_analysis import make_decision
from codescanner_analysis.file_header_parser import FileHeaderParser
from codescanner_analysis.byte_plot import BytePlot


class CodescannerAnalysisData(object):
    '''
    Various applications of the codescanner (VZ)
    * architecture detection
    * binary visualization
    * tbc..
    '''

    # PIL.Image.MAX_IMAGE_PIXELS
    MAX_PLOT_FILE_SIZE = 5 * 1024 * 1024
    BYTE_PLOT = 1
    COLOR_MAP = 2

    def __init__(self, file_src, start=0, end=0, aggressive=0):
        '''
        Will analyse the referenced file, extract regions and provide additional methods.

        :param file_src: the source path of the file to analyse
        :param start: start offset of the codescanner (s= parameter)
        :param end: end offset of the codescanner (e= parameter)
        :aggressive: bool aggressive (a= parameter, affects code region search)
        '''
        
        self.file_path = file_utils.sanitize_file_name(file_src)
        self.file_size = os.path.getsize(self.file_path)

        start, end = self._sanitize_offset_numbers(start, end)
        
        if (aggressive): # anything not null
            aggressive = 1
        else:
            aggressive = 0

        self.file_header = FileHeaderParser.get_file_header(self.file_path)
        self._codescanner = CodescanInterface()
        self._analyze_file(start, end, aggressive)

    def __del__(self):
        self.file_path = None
        self.file_header = None
        self._codescanner = None
        self.regions = None
        self.sizes = None
        self.decision = None
        self.architecture = None

    def _sanitize_offset_numbers(self, start, end):
        '''
        Checks, if the user provided integers and they fit into the file size bounds.

        :return: start, end
        '''

        start = self._parse_int(start)
        end = self._parse_int(end)

        if start == 0 and end == 0:
            return start, end
        if start >= end:
            raise ValueError("Start offset '%d' is >= end offset %d." % (start, end))
        if start < 0:
            raise ValueError("Start offset '%d' is < 0." % start)
        if start >= os.path.getsize(self.file_path):
            raise ValueError("Start offset '%d' is >= the file size %d." % (start, os.path.getsize(self.file_path)))

        return start, end

    def _parse_int(self, value):
        '''
        isdigit() does not recognize hexadecimal numbers like '0x100'.
        '''
        try:
            return int(value)
        except ValueError:
            raise ValueError("Offset '%s' is not a number" % value)

    def _analyze_file(self, start, end, aggressive):
        '''
        Entering the function the referenced file will be analyzed by the codescanner.

        The resulting analysis contains
        regions containing a listing of found region types (e.g. Code, ASCII) with start-end offsets.
        '''
        self.regions = self._codescanner.run(self.file_path, start, end, aggressive)
        self.regions = self._codescanner.sanitize_regions(self.regions)

        self.sizes = self._codescanner.calculate_sizes(self.regions)
        self.decision = make_decision(self.sizes, self.file_header)
        self.architecture = self._codescanner.extract_architectures(self.regions)

    def plot_to_buffer(self, dpi, plot_type=BYTE_PLOT):
        '''
        Will plot the analysis to a image data buffer.
        If the analysed binary file exceeds the MAX_PLOT_FILE_SIZE, a color bar will be used instead of the image.
        The color bar plot can also be forced.

        :param dpi: dpi/size of the image. dpi * FIG_SIZE gives the resulting size
        :param plot_type: either BYTE_PLOT (1) or COLOR_MAP (2)
        :return: the bytes of the png image
        '''
        
        if (self.file_size < 0x100):
            raise IOError("The file is too small for visualization." )
        
        plotter = self._init_plotter(plot_type)
        image_bytes = plotter.plot_to_buffer(dpi)

        return image_bytes

    def plot_to_file(self, file_name, dpi, plot_type=BYTE_PLOT):
        '''
        Will plot the analysis to an image file.
        If the analysed binary file exceeds the MAX_PLOT_FILE_SIZE, a color bar will be used instead of the image.
        The color bar plot can also be forced.

        :param file_name: the image file source path
        :param dpi: dpi/size of the image. dpi * FIG_SIZE gives the resulting size
        :param plot_type: either BYTE_PLOT (1) or COLOR_MAP (2)
        '''
        
        if (self.file_size < 0x100):
            raise IOError("The file is too small for visualization." )
        
        plotter = self._init_plotter(plot_type)
        plotter.plot_to_file(file_name, dpi)

    def plot_to_dynamic_size_buffer(self, dpi, width, height, plot_type=BYTE_PLOT):
        '''
        Will plot the analysis to a image data buffer.
        The width will depend on the size of the analysed file.
        Where a dpi of 72 will result in a width equal to the file size in kb.
        If the analysed binary file exceeds the MAX_PLOT_FILE_SIZE, a color bar will be used instead of the image.
        The color bar plot can also be forced.

        :param dpi: dpi/size of the image. dpi * FIG_SIZE gives the resulting size
        :param width: The desired width of the image
        :param height: The desired height of the image.
        :param plot_type: either BYTE_PLOT (1) or COLOR_MAP (2)
        :return: the bytes of the png image
        '''
        
        if (self.file_size < 0x100):
            raise IOError("The file is too small for visualization." )

        plotter = self._init_plotter(plot_type)
        image_bytes = plotter.plot_to_dynamic_size_buffer(dpi, width, height)

        return image_bytes

    def plot_to_dynamic_size_file(self, file_name, dpi, width, height, plot_type=BYTE_PLOT):
        '''
        Will plot the analysis to an image file.
        The width will depend on the size of the analysed file.
        Where a dpi of 72 will result in a width equal to the file size in kb.
        If the analysed binary file exceeds the MAX_PLOT_FILE_SIZE, a color bar will be used instead of the image.
        The color bar plot can also be forced.

        :param file_name: the image file source path
        :param dpi: dpi/size of the image. dpi * FIG_SIZE gives the resulting size
        :param width: The desired width of the image.
        :param height: The desired height of the image.
        :param plot_type: either BYTE_PLOT (1) or COLOR_MAP (2)
        '''
        
        if (self.file_size < 0x100):
            raise IOError("The file is too small for visualization." )

        plotter = self._init_plotter(plot_type)
        plotter.plot_to_dynamic_size_file(file_name, dpi, width, height)

    def _init_plotter(self, plot_type):
        if plot_type == self.BYTE_PLOT:
            plotter = BytePlot(self.file_path, self.regions)
        elif plot_type == self.COLOR_MAP:
            plotter = ColorMap(self.file_path, self.regions)
        else:
            raise ValueError("Not supported plot type!")

        plotter._offsets = (self._codescanner.start, self._codescanner.end)
        plotter._file_size = self.sizes['FileSize']
        plotter.update_code_spec_label(self.regions.get("Code"))

        return plotter

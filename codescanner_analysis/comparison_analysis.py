import os
import subprocess
from collections import defaultdict

from codescanner_analysis import header_parser
from codescanner_analysis.utils import file_utils, file_to_array as fta
from codescanner_analysis.codescanner_analysis import CodescannerAnalysisData
from codescanner_analysis.overlay_plot import OverlayPlot


class ComparisonAnalysis(object):
    def __init__(self, file_src):
        self._file_path = file_utils.sanitize_file_name(file_src)
        self.cs_regions = self._parse_regions_with_code_scanner()
        
        self.x_regions = self._parse_x_regions_with_header_parser()
        
        # default headerParser: 
        # self.x_regions = self._parse_x_regions_with_header_parser()
        
        # uncomment this instead if you do not want to use headerParser, but objdump.
        # self.x_regions = self.parse_x_regions_with_objdump()

    def __del__(self):
        self._file_path = None
        self.cs_regions = None
        self.x_regions = None
        self.architecture = None

    def _parse_regions_with_code_scanner(self):
        cad = CodescannerAnalysisData(self._file_path)
        self.architecture = cad.architecture
        return cad.regions

    def _parse_x_regions_with_header_parser(self):
        root_directory = os.path.dirname(os.path.realpath(__file__))
        libheaderparser_src = os.path.join(root_directory, 'res/lib', 'libheaderparser.so')

        header_parser.init(libheaderparser_src)
        hp_result = header_parser.get_basic_info(self._file_path, 0, header_parser.FORCE_NONE)

        cr = {}

        for i in range(len(hp_result['regions'])):
            t = hp_result['regions'][i]
            cr[t[0]] = [[int(t[1]), int(t[2])]]

        return cr

    def parse_x_regions_with_objdump(self):
        '''
        Alternative way (instead of the headerParser) to get x_regions.

        :return: a regions dictionary
        '''
        result = defaultdict(list)

        parser_process = subprocess.Popen(["objdump", "-h", self._file_path], stdout=subprocess.PIPE)
        output = parser_process.communicate()[0].split(b'\n')

        for i in range(len(output) - 1):
            tokens = output[i].split()
            # if self._has_flags(output[i + 1]):
            if self._has_code(output[i + 1], tokens):
                tokens_len = len(tokens)
                size_id = tokens_len - 5
                start_id = tokens_len - 2
                start = int(tokens[start_id], base=16)
                end = int(tokens[start_id], base=16) + int(tokens[size_id], base=16)

                if tokens_len < 7:
                    name = ""
                elif tokens_len == 7:
                    name = tokens[1].decode('utf-8', 'backslashreplace').strip()
                elif tokens_len >= 8:
                    end_name_idx = tokens_len - 6
                    start_name = output[i].index(tokens[1])
                    end_name = output[i].index(tokens[end_name_idx], start_name) + len(tokens[end_name_idx])
                    name = output[i][start_name:end_name].decode('utf-8', 'backslashreplace').strip()

                result[name].append([start, end])

        return dict(result)

    def _has_code(self, next_line, tokens):
        return len(next_line) and (b"  CODE" in next_line or b", CODE" in next_line) and len(tokens) > 5

    def plot_to_file(self, file_name, dpi=100):
        '''
        Plot cs_regions and x_regions to file.

        :param file_name: the name of the resulting image
        :param dpi: the resolution of the image
        :return:
        '''
        if file_name is None or len(file_name) == 0:
            raise RuntimeError('RuntimeError: file_name is empty!')
        if self.cs_regions is None:
            raise RuntimeError('RuntimeError: cs_regions is empty!')
        if self.x_regions is None:
            raise RuntimeError('RuntimeError: x_regions is empty!')

        self._search_alien_code()

        plotter = OverlayPlot(self._file_path, self.cs_regions, self.x_regions)
        plotter.update_code_spec_label(self.architecture.get('Full'))
        plotter.update_alien_code_spec_label(self._get_alien_architecture())
        plotter.plot_to_file(file_name, dpi)

    def _search_alien_code(self):
        if not self.are_code_regions_in_file():
            return
        if not self.cs_regions.get('Code'):
            return
        if len(self.x_regions) == 0:
            return

        file_size = os.path.getsize(self._file_path)

        cs_code = [r[0:2] for r in self.cs_regions.get('Code')]
        x_code = []
        for a in self.x_regions:
            x_code.extend(self.x_regions[a])

        cs_regions_a = fta.Analog(cs_code, file_size)
        alien_regions = fta.toDigital(fta.Analog(x_code, file_size, '-', cs_regions_a))
        cs_regions_a = fta.Analog(cs_code, file_size)
        code_regions = fta.toDigital(fta.Analog(x_code, file_size, '*', cs_regions_a))

        original_regions = self.cs_regions['Code']

        self.cs_regions['Code'] = code_regions.tolist()
        self.cs_regions['AlienCode'] = alien_regions.tolist()
        self._restore_regions_architecture(original_regions)

    def _restore_regions_architecture(self, original_regions):
        for r in original_regions:
            for i, cr in enumerate(self.cs_regions['Code']):
                if r[0] <= cr[0] and cr[1] <= r[1]:
                    self.cs_regions['Code'][i] = cr[0:]
            for i, acr in enumerate(self.cs_regions['AlienCode']):
                if r[0] <= acr[0] and acr[1] <= r[1]:
                    self.cs_regions['AlienCode'][i] = (acr[0], acr[1], r[2])
            # i = 0
            # cr = self.cs_regions['Code'][i]
            # if r[0] <= cr[0] and cr[1] <= r[1]:
            #     self.cs_regions['Code'][i] = (cr[0], cr[1], r[2])
            # i = len(self.cs_regions['AlienCode']) - 1
            # acr = self.cs_regions['AlienCode'][i]
            # if r[0] <= acr[0] and acr[1] <= r[1]:
            #     self.cs_regions['AlienCode'][i] = (acr[0], acr[1], r[2])

    def _get_alien_architecture(self):
        if not self.cs_regions.get('AlienCode') or len(
                self.cs_regions['AlienCode'][len(self.cs_regions['AlienCode']) - 1]) < 3:
            return 'AlienCode'

        return self.cs_regions['AlienCode'][len(self.cs_regions['AlienCode']) - 1][2]

    def are_code_regions_in_file(self):
        '''
        Check if all executable regions, as found by the headerParser,
        are within file size.
        '''
        file_size = os.path.getsize(self._file_path)
        for key in self.x_regions:
            for r in self.x_regions[key]:
                if r[1] > file_size:
                    return False
        return True

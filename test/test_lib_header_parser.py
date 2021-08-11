import unittest
import os

import header_parser


class LibHeaderParserTest(unittest.TestCase):

    def setUp(self):
        test_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
        self.test_file = os.path.join(test_file_dir, 'testfile')

        root_directory = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self.libheaderparser_src = os.path.join(root_directory, 'res/lib', 'libheaderparser.so')
        header_parser.init(self.libheaderparser_src)

    def test_no_file(self):
        test_file = 'nofile'
        result = header_parser.get_basic_info(test_file)
        assert result == header_parser.get_initialized_hpd()

    def test_file(self):
        test_file = self.test_file

        result = header_parser.get_basic_info(test_file, 0)

        # print()
        # print("result['headertype']: %d %s (%s)" % (result['headertype'], header_parser.lib_header_parser.getHeaderDataHeaderType(result['headertype']), type(result['headertype'])))
        # print("result['bitness']: %d (%s)" % (result['bitness'], type(result['bitness'])))
        # print("result['endian']: %d (%s)" % (result['endian'], type(result['endian'])))
        # print("result['cpu']: %d %s" % (result['cpu'], header_parser.lib_header_parser.getHeaderDataArchitecture(result['cpu'])))
        # print("result['machine']: %s" % result['machine'])
        # print("result['regions'] (%d):" % result['regions_size'])
        # for i in range(result['regions_size']):
        #     region = result['regions'][i]
        #     print(" (%d) %s: ( 0x%x - 0x%x )" % (i + 1, region[0].decode('utf-8'), region[1], region[2]))

        assert 10 == result['headertype']
        assert header_parser.lib_header_parser.getHeaderDataHeaderType(result['headertype']) == 'ELF'
        assert 64 == result['bitness']
        assert 1 == result['endian']
        assert 45 == result['cpu']
        assert 'Intel' == header_parser.lib_header_parser.getHeaderDataArchitecture(result['cpu'])
        assert 5 == result['regions_size']

        expected_regions = [
            ('.init', 0xfb0, 0xfca),
            ('.plt', 0xfd0, 0x1140),
            ('.plt.got', 0x1140, 0x1148),
            ('.text', 0x1150, 0x1c22),
            ('.fini', 0x1c24, 0x1c2d)
        ]
        for i in range(result['regions_size']):
            region = result['regions'][i]
            assert expected_regions[i][0] == region[0]
            assert expected_regions[i][1] == region[1]
            assert expected_regions[i][2] == region[2]

    def test_arbitray_file(self):
        tfile = self.test_file

        force = header_parser.FORCE_NONE

        hp_result = header_parser.get_basic_info(tfile, 0, force)

        print()
        print(hp_result)

import collections
import os
import unittest

from codescanner_analysis import CodescanInterface


class CodescanInterfaceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        cls.test_file_dir = os.path.join(root_dir, 'test', 'data')
        cls.test_binary = os.path.join(cls.test_file_dir, 'testfile')
        cls.codescanner = CodescanInterface()

    def test_sanitize_regions(self):
        regions = self.codescanner.run(self.test_binary)
        regions = self.codescanner.sanitize_regions(regions)
        regions = collections.OrderedDict(sorted(regions.items()))

        expected = collections.OrderedDict([
            ('Ascii', [[2048, 4096], [23040, 27648], [34816, 36864]]),
            ('Code', [[4096, 7680, u'Intel', 64, 1]]),
            ('Data', [[0, 512], [1024, 2048], [7680, 8704], [11776, 23040], [27648, 34816], [36864, 37888], (38400, 38808)]),
            ('HighEntropy', [[512, 1024]]),
            ('Zero', [[8704, 11776], [37888, 38400]])
        ])

        # print()
        # print("regions")
        # print(regions)

        assert regions == expected

    def test_extract_architecture(self):
        regions = {'Code': [(0, 0, 'Intel', 64, 1)]}
        architecture = dict(self.codescanner.extract_architectures(regions))
        expected = {'Full': u'Intel-64', 'Endianess': u'le', 'ISA': u'Intel', 'Bitness': u'64'}
        assert expected == architecture

        regions = {'Code': [(0, 0, 'AMD', 31, 2)]}
        architecture = dict(self.codescanner.extract_architectures(regions))
        expected = {'Full': u'AMD-31-be', 'Endianess': u'be', 'ISA': u'AMD', 'Bitness': u'31'}
        assert expected == architecture

        regions = {'Code': [(0, 0, 'AMD', 0, 2)]}
        architecture = dict(self.codescanner.extract_architectures(regions))
        expected = {'Full': u'AMD-be', 'Endianess': u'be', 'ISA': u'AMD', 'Bitness': u''}
        assert expected == architecture

        regions = {'Code': [(0, 0, 'AMD', 16, 0)]}
        architecture = dict(self.codescanner.extract_architectures(regions))
        expected = {'Full': u'AMD-16', 'Endianess': u'', 'ISA': u'AMD', 'Bitness': u'16'}
        assert expected == architecture

    def test_check_data(self):
        d0 = self.codescanner.run(self.test_binary, 0x300, 0x400)
        d1 = self.codescanner.run(self.test_binary, 0x200, 0x400)

        assert d0['Data'] == [[0x300, 0x400]]
        assert d1['Data'] == [[0x200, 0x400]]

    def test_calculate_sizes_with_sparse_regions(self):
        regions = {'Ascii': [(0, 10)], 'Code': [(10, 20)]}
        sizes = self.codescanner.calculate_sizes(regions)
        expected_sizes = {'Ascii': 10, 'Code': 10, 'Data': 0, 'FileSize': 20, 'HighEntropy': 0, 'Zero': 0}

        assert collections.OrderedDict(sorted(sizes.items())) == expected_sizes

    def test_run_codescanner_with_offsets(self):
        start = 0x800
        end = 0x4000
        regions = self.codescanner.run(self.test_binary, start, end)
        regions = self.codescanner.sanitize_regions(regions)
        e = {'Data': [[0, 1024], [2048, 6656], [9728, 14336]], 'Zero': [[6656, 9728]], 'Ascii': [[1024, 2048]]}

        assert regions == e

    def test_merge_regions(self):
        regions = {'Data': [[0, 1024], [1024, 1536], [1536, 2560], [25600, 26112]],
                   'Dump': [[0, 1024], [1536, 2560], [2560, 2700], [2800, 2900], [2900, 2990], [25600, 26112]],
                   'Blah': [[0, 1024], [1536, 2560]],
                   'Code': [[2560, 21504, u'Intel-32', 32, 1], [21600, 21700, u'Intel-32', 32, 1], [21700, 21800, u'Intel-32', 32, 1]],
                   'Ascii': [[21504, 25600], [25600, 25700], [25700, 25800]]}
        # print()
        # print('original  : %s' % str(regions))

        sizes = self.codescanner.calculate_sizes(regions)
        self.codescanner._merge_regions(regions)

        expected = {'Data': [[0, 2560], [25600, 26112]],
                    'Dump': [[0, 1024], [1536, 2700], [2800, 2990], [25600, 26112]],
                    'Blah': [[0, 1024], [1536, 2560]],
                    'Code': [[2560, 21504, u'Intel-32', 32, 1], [21600, 21800, u'Intel-32', 32, 1]],
                    'Ascii': [[21504, 25800]]}

        expected_sizes = self.codescanner.calculate_sizes(expected)

        # print('merged    : %s' % str(regions))
        # print('expected  : %s' % str(expected))

        assert expected == regions
        assert expected_sizes == sizes

    def test_merge_regions_fanny(self):
        regions = {
            u'HighEntropy': [[94720, 102912], [108032, 136704], [138240, 143872]],
            u'Zero': [[1024, 3584], [54784, 57344], [64512, 65024], [67584, 69120], [72192, 75264], [89600, 91648],
                      [105472, 108032], [143872, 146944], [165888, 167424], [168448, 171008], [173056, 175104],
                      [182784, 184320]],
            u'Code': [[4096, 54784, u'Intel-32'], [75264, 89600, u'Intel-32'], [146944, 163328, u'Intel-32']],
            u'Ascii': [[62464, 64512], [66048, 67584], [102912, 105472], [164352, 165888], [167424, 168448]],
            u'Data': [[0, 1024], [3584, 4096], [57344, 61440], [61440, 61952], [61952, 62464], [65024, 65536],
                      [65536, 66048], [69120, 72192], [91648, 94720], [136704, 138240], [163328, 164352],
                      [171008, 173056], [175104, 179712], [179712, 182784]]
        }
        # print()
        # print('original  : %s' % str(regions))

        sizes = self.codescanner.calculate_sizes(regions)
        self.codescanner._merge_regions(regions)

        expected = {
            u'HighEntropy': [[94720, 102912], [108032, 136704], [138240, 143872]],
            u'Zero': [[1024, 3584], [54784, 57344], [64512, 65024], [67584, 69120], [72192, 75264], [89600, 91648],
                      [105472, 108032], [143872, 146944], [165888, 167424], [168448, 171008], [173056, 175104],
                      [182784, 184320]],
            u'Code': [[4096, 54784, u'Intel-32'], [75264, 89600, u'Intel-32'], [146944, 163328, u'Intel-32']],
            u'Ascii': [[62464, 64512], [66048, 67584], [102912, 105472], [164352, 165888], [167424, 168448]],
            u'Data': [[0, 1024], [3584, 4096], [57344, 62464], [65024, 66048], [69120, 72192], [91648, 94720],
                      [136704, 138240], [163328, 164352], [171008, 173056], [175104, 182784]]
        }

        # print('merged    : %s' % str(regions))
        # print('expected  : %s' % str(expected))

        expected_sizes = self.codescanner.calculate_sizes(expected)

        assert expected == regions
        assert expected_sizes == sizes

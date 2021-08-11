# -*- coding: utf-8 -*-
import os

import libcodescanpy  # (libcodescanpy.py)

CS_REGION_CODE = "Code"
CS_REGION_DATA = "Data"
CS_REGION_HIGHT_ENTROPY = "HighEntropy"
CS_REGION_ZERO = "Zero"


class CodescanInterface(object):
    BLOCK_SIZE = 0x200

    def __init__(self):
        self._file_name = ""
        self.start = 0
        self.end = 0
        
        libcodescanpy.init()

    def __del__(self):
        self._file_name = None
        self.start = None
        self.end = None

    def run(self, filename, start=0, end=0, aggressive=0):
        '''
        Runs libcodescan

        :param filename: the file path
        :param start: start offset of the codescanner (s= parameter)
        :param end: end offset of the codescanner (e= parameter)
        :param aggressive: affects code region search (a= parameter)
        :return: result dict
        '''

        self._file_name = filename
        self.start = start
        self.end = end
        self.aggressive = aggressive

        r = libcodescanpy.scan(filename, start, end, aggressive, libcodescanpy.RESULT_LIST)

        return r

    def sanitize_regions(self, regions):
        '''
        Sanitize regions dict resulting from the libcodescan.so

        :param regions: the data dict
        :return: regions dictionary
        '''

        self._merge_regions(regions)
        self._pad_regions(regions)

        return dict(regions)

    def calculate_sizes(self, regions):
        sizes = {'Ascii': 0, 'Code': 0, 'Data': 0, 'FileSize': 0, 'HighEntropy': 0, 'Zero': 0}
        file_size = 0

        if regions is None or len(regions) == 0:
            return sizes

        for t in regions:
            sizes[t] = 0

            for r in regions[t]:
                sizes[t] += r[1] - r[0]

            file_size += sizes[t]

        sizes["FileSize"] = file_size

        return sizes

    def _merge_regions(self, regions):
        '''
        Merge regions, with no space between them.
        '''
        for k in regions:
            ln = len(regions[k])

            # nothing merge
            if ln == 1:
                continue

            # sort region k by its 'start' value
            regions[k].sort(key=lambda tup: tup[0])

            i = ln - 1

            while i > 0:
                j = i

                # while prev end == act start
                # decrement j to find farest mergeable region
                while j > 0 and regions[k][j - 1][1] == regions[k][j][0]:
                    j -= 1

                # if there are mergeable regions, merge them
                # i.e. (1,2), (2,3), (3,4)
                #      j[0] = 1       i[1]=4
                # =>   (1,4)
                if j < i:
                    # => regions[k](1,4[,cpu,bitness,endianess])
                    if k == 'Code':
                        # t = regions[k][j][0]
                        regions[k][j][1:] = regions[k][i][1:]
                        # regions[k][j][0] = t
                    else:
                        regions[k][j] = [regions[k][j][0], regions[k][i][1]]
                    # delete merged regions, to i exclusive => i+1
                    del regions[k][j + 1:i + 1]
                    # update i to continue in next iteration
                    i = j - 1
                else:
                    # decrement i by 1 to continue in next iteration, because nothing has been merged
                    i -= 1

    def _pad_regions(self, regions):
        '''
        Pad regions with generic data if the filesize does not divide 512 without remainder.
        Because this bytes are unclassified by codescanner.
        '''

        if regions is None or len(regions) == 0:
            return

        if self.end == 0:
            file_size = os.path.getsize(self._file_name)
        else:
            file_size = self.end - self.start

        remainder = file_size % self.BLOCK_SIZE
        
        if (remainder != 0):
            if 'Data' not in regions:
                regions['Data'] = []
            regions['Data'].append((file_size - remainder, file_size))

    def extract_architectures(self, regions):
        '''
        Fill architecture dict with info out of the first code region
        :param region:
        :return: dict
        '''
        if not regions.get(CS_REGION_CODE):
            return {}

        cr_0 = regions.get(CS_REGION_CODE)[0]

        return CodescanInterface.get_architecture(cr_0)

    @staticmethod
    def get_architecture(region):
        '''
        Fill architecture dict with info out of a code region
        :param region:
        :return: dict
        '''
        if len(region) < 5:
            return {}

        architecture = {
            'ISA': region[2],
            'Bitness': str(region[3]) if region[3] > 0 else "",
            'Endianess': "le" if region[4] == 1 else "be" if region[4] == 2 else "",
            'Full': 'none',
        }

        architecture["Full"] = architecture["ISA"]

        if architecture["Bitness"]:
            architecture["Full"] = architecture["Full"] + "-" + architecture["Bitness"]

        if architecture["Endianess"] and region[2] != "Intel":
            architecture["Full"] = architecture["Full"] + "-" + architecture["Endianess"]

        return architecture

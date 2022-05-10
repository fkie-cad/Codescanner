from collections import defaultdict

import numpy

from PIL import Image

from codescanner_analysis.codescan_interface import CodescanInterface

MAGIC_PNG_BYTES = b'\x89\x50\x4e\x47\x0D\x0A\x1A\x0A'


def assert_image_size(expected_size, img_src):
    im = Image.open(img_src)
    width, height = im.size
    assert expected_size[0] == width
    assert expected_size[1] == height


def create_random_file(name, size):
    '''
    Create a random bytes file with size in bytes.

    :param name: the file path name
    :param size: the size in bytes
    '''
    r_bytes = numpy.random.bytes(size)
    with open(name, 'wb') as f:
        f.write(r_bytes)


def create_dense_regions(size, steps=5000, min_step=32):
    test_regions = defaultdict(list)
    step = size / steps
    if step < min_step:
        step = min_step

    step = int(step)

    breaks = [
        int(step * 0.15625),
        int(step * 0.4375),
        int(step * 0.6875),
        int(step * 1)
    ]

    for i in range(0, size, step):
        test_regions['A'].append((i, i + breaks[0]))
        test_regions['A'].append((i + breaks[0], i + breaks[1]))
        test_regions['B'].append((i + breaks[1], i + breaks[2]))
        test_regions['C'].append((i + breaks[2], i + breaks[3]))

    return test_regions


def extract_regions(src):
    csi = CodescanInterface()
    r = csi.run(src)
    return csi.sanitize_regions(r)

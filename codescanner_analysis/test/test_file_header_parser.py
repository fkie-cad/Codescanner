import numpy
import os
import pytest
from tempfile import TemporaryDirectory
import unittest

from codescanner_analysis.file_header_parser import FileHeaderParser


class FileHeaderParserTest(unittest.TestCase):

    def setUp(self):
        self._test_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
        self._test_binary_src = os.path.join(self._test_file_dir, 'testfile')
        self._test_binary_exe = os.path.join(self._test_file_dir, 'AdapterTroubleshooter.exe')

    def test_not_existing_file(self):
        with pytest.raises(IOError):
            FileHeaderParser.get_file_header('not.existi.ng')

    def test_tilde_directory_path(self):
        file_name = 'what/ever.exe'
        file_src = '~/' + file_name
        home = os.path.expanduser("~")
        expected = os.path.join(home, file_name)

        try:
            FileHeaderParser.get_file_header(file_src)
        except IOError as e:
            assert str(e) == 'IOError: Source file does not exist: ' + expected

    def test_get_elf_file_header(self):
        header = FileHeaderParser.get_file_header(self._test_binary_src)
        assert header == 'ELF'

    def test_get_pe_file_header(self):
        with TemporaryDirectory() as temp_dir:
            bin_src = os.path.join(temp_dir, 'FileHeaderParserTest_test_get_pe_file_header.exe')
            self._create_file(bin_src, 0x200, FileHeaderParser.MAGIC_PE_FILE_BYTES)

            header = FileHeaderParser.get_file_header(bin_src)

            assert header == 'PE'

    def test_get_undefined_file_header(self):
        with TemporaryDirectory() as temp_dir:
            bin_src = os.path.join(temp_dir, 'FileHeaderParserTest_test_get_pe_file_header.exe')
            self._create_file(bin_src, 0x200, bytearray(b'\xba\xd4\xea\xda'))

            header = FileHeaderParser.get_file_header(bin_src)

            assert header is None

    def test_get_too_small_file(self):
        with TemporaryDirectory() as temp_dir:
            bin_src = os.path.join(temp_dir, 'FileHeaderParserTest_test_get_too_small_file.exe')

            with open(bin_src, 'wb') as f:
                f.write(bytearray(b'\x00\x00\x00'))

            header = FileHeaderParser.get_file_header(bin_src)

            assert header is None

    def _create_file(self, name, size, magic):
        pe_bytes = numpy.random.bytes(size - 4)
        pe_bytes = magic + pe_bytes

        with open(name, 'wb') as f:
            f.write(pe_bytes)

import os

import codescanner_analysis.utils.file_utils as file_utils


class FileHeaderParser(object):
    MAGIC_ELF_FILE_BYTES = bytearray(b'\x7F\x45\x4C\x46')
    MAGIC_PE_FILE_BYTES = bytearray(b'\x4D\x5A')

    @staticmethod
    def get_file_header(file_src):
        file_src = file_utils.sanitize_file_name(file_src)

        if os.path.getsize(file_src) < 4:
            return None

        with open(file_src, "rb") as f:
            magic = f.read(4)

        if magic == FileHeaderParser.MAGIC_ELF_FILE_BYTES:
            return 'ELF'
        elif magic[0:2] == FileHeaderParser.MAGIC_PE_FILE_BYTES:
            return 'PE'
        else:
            return None

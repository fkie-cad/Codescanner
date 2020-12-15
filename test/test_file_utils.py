import os
import unittest

import pytest
from _pytest.monkeypatch import MonkeyPatch

import utils.file_utils as file_utils


class UtilsTest(unittest.TestCase):

    def test_sanitize_file_name_no_file(self):
        file_src = '~/sdfgsdfgdsfg'
        with pytest.raises(IOError):
            file_utils.sanitize_file_name(file_src)

    def test_sanitize_file_name(self):
        monkeypatch = MonkeyPatch()
        monkeypatch.setattr('os.path.isfile', lambda _: True)
        file_name = 'what/ever.exe'
        file_src = '~/' + file_name
        received = file_utils.sanitize_file_name(file_src)

        home = os.path.expanduser("~")
        expected = os.path.join(home, file_name)

        assert expected == received
        monkeypatch.undo()

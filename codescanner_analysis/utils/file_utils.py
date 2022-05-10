import os


def sanitize_file_name(file_name, check_existence=True):
    file_name = os.path.expanduser(file_name)
    if check_existence and not os.path.isfile(file_name):
        raise IOError('IOError: Source file does not exist: %s' % file_name)
    return file_name

VERSION = (1, 2, 4)


def get_version(tail=''):
    return ".".join(map(str, VERSION)) + tail

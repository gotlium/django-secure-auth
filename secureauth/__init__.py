VERSION = (1, 2, 5)


def get_version(tail=''):
    return ".".join(map(str, VERSION)) + tail

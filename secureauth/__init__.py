VERSION = (1, 2, 2)


def get_version(tail=''):
    return ".".join(map(str, VERSION)) + tail

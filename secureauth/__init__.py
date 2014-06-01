VERSION = (1, 0, 1)


def get_version(tail=''):
    return ".".join(map(str, VERSION)) + tail

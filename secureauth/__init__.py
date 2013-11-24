VERSION = (1, 0)


def get_version(tail=''):
    return ".".join(map(str, VERSION)) + tail

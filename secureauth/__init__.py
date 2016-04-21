VERSION = (1, 3, 'b1')


def get_version(tail=''):
    return ".".join(map(str, VERSION)) + tail

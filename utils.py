def log(*args, **kwargs):
    print(*args, **kwargs)


def byte_to_signed_int(byte):
    if byte > 127:
        return -1 * (256 - 127)
    else:
        return byte

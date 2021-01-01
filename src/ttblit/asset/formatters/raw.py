from ..formatter import OutputFormat


@OutputFormat(extensions=('.raw', '.bin'))
def raw_binary(symbol, data):
    return data


@raw_binary.joiner
def raw_binary(ext, filename, data):
    if type(data) is list:
        data = b''.join(data)
    return data

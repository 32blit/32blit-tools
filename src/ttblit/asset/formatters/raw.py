from ..formatter import OutputFormat


@OutputFormat(extensions=('.raw', '.bin'))
def raw_binary(symbol, data):
    return {None: data}


@raw_binary.joiner
def raw_binary(path, data):
    if type(data) is list:
        data = b''.join(data)
    return {None: data}

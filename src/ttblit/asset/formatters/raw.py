from ..formatter import AssetFormatter


@AssetFormatter(extensions=('.raw', '.bin'))
def raw_binary(symbol, data):
    return {None: data}


@raw_binary.joiner
def raw_binary(path, data):
    return {None: b''.join(data)}

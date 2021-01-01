from ..formatter import OutputFormat


class RawBinary(OutputFormat):
    name = 'raw_binary'
    extensions = ('.raw', '.bin')

    def fragments(self, symbol, data):
        return data

    def join(self, ext, filename, data):
        if type(data) is list:
            data = b''.join(data)
        return data

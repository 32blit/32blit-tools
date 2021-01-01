from ..formatter import OutputFormat


class RawBinary(OutputFormat):
    name = 'raw_binary'
    extensions = ('.raw', '.bin')

    def __init__(self):
        OutputFormat.__init__(self)

    def output(self, input_data, symbol_name):
        return input_data

    def join(self, ext, filename, data):
        if type(data) is list:
            data = b''.join(data)
        return data

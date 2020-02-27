class OutputFormat():
    name = 'none'
    components = None
    extensions = ()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def build(self, input_data, symbol_name):
        if self.components is None:
            return self.output(input_data, symbol_name)
        else:
            output_components = {}
            for extension in self.components:
                output_components[extension] = getattr(self, f'output_{extension}')(input_data, symbol_name)
            return output_components


class CHeader(OutputFormat):
    name = 'c_header'
    extensions = ('.hpp', '.h')

    def __init__(self):
        OutputFormat.__init__(self)

    def _helper_raw_to_c_source_hex(self, input_data):
        if type(input_data) is str:
            input_data = bytes(input_data, encoding='utf-8')
        return ', '.join([f'0x{c:02x}' for c in input_data])

    def output(self, input_data, symbol_name):
        input_data = self._helper_raw_to_c_source_hex(input_data)
        return f'''inline const uint8_t {symbol_name}[] = {{{input_data}}};
inline const uint32_t {symbol_name}_length = sizeof({symbol_name});'''

    def join(self, ext, filename, data):
        if type(data) is list:
            data = '\n'.join(data)
        return f'''// Auto Generated File - DO NOT EDIT!
#pragma once
#include <cstdint>
{data}
'''


class CSource(CHeader):
    name = 'c_source'
    components = ('hpp', 'cpp')
    extensions = ('.cpp', '.c')

    def __init__(self):
        OutputFormat.__init__(self)

    def output_hpp(self, input_data, symbol_name):
        return f'''extern const uint8_t {symbol_name}[];
extern const uint32_t {symbol_name}_length;'''

    def output_cpp(self, input_data, symbol_name):
        input_data = self._helper_raw_to_c_source_hex(input_data)
        return f'''const uint8_t {symbol_name}[] = {{{input_data}}};
const uint32_t {symbol_name}_length = sizeof({symbol_name});'''

    def join(self, ext, filename, data):
        if type(data) is list:
            data = '\n'.join(data)
        if ext == 'cpp':
            header = filename.with_suffix('.hpp').name
            return f'''// Auto Generated File - DO NOT EDIT!
#include "{header}"
{data}
'''
        else:
            return f'''// Auto Generated File - DO NOT EDIT!
#pragma once
#include <cstdint>
{data}
'''


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


output_formats = {}
name = None
object = None


def parse_output_format(value):
    if type(value) is str:
        return output_formats.get(value, None)
    if issubclass(value, OutputFormat):
        return value
    return output_formats[value]


for name, object in globals().items():
    try:
        if issubclass(object, OutputFormat) and not name == 'OutputFormat':
            output_formats[object.name] = object
    except TypeError:
        pass

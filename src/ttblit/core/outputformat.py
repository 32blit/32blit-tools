class OutputFormat():
    name = 'none'
    components = None
    extensions = ()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class CHeader(OutputFormat):
    name = 'c_header'
    extensions = ('.hpp', '.h')

    def join(self, ext, filename, data):
        if type(data) is list:
            data = '\n'.join(data)
        return f'''// Auto Generated File - DO NOT EDIT!
#pragma once
#include <cstdint>
{data}
'''


class CSource(OutputFormat):
    name = 'c_source'
    components = ('hpp', 'cpp')
    extensions = ('.cpp', '.c')

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

    def join(self, ext, filename, data):
        if type(data) is list:
            data = ''.join(data)
        return data


output_formats = {}
name = None
object = None


def parse_output_format(value):
    if issubclass(value, OutputFormat):
        return value
    return output_formats[value]


for name, object in globals().items():
    try:
        if issubclass(object, OutputFormat):
            output_formats[name] = object
    except TypeError:
        pass

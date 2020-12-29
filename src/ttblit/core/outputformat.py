import textwrap


class OutputFormat():
    name = 'none'
    components = None
    extensions = ()

    by_name = {}
    by_extension = {}

    def __init_subclass__(cls):
        OutputFormat.by_name[cls.name] = cls
        for ext in cls.extensions:
            OutputFormat.by_extension[ext] = cls

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
    wrapper = textwrap.TextWrapper(
        initial_indent='    ',
        subsequent_indent='    ',
        width=80,
    )

    def _initializer(self, input_data):
        if type(input_data) is str:
            input_data = input_data.encode('utf-8')
        values = ', '.join(f'0x{c:02x}' for c in input_data)
        return f' = {{\n{self.wrapper.fill(values)}\n}}'

    def _declaration(self, types, symbol_name, data=None):
        return textwrap.dedent('''\
        {types} uint8_t {symbol_name}[]{initializer};
        {types} uint32_t {symbol_name}_length{size};
        ''').format(
            types=types,
            symbol_name=symbol_name,
            initializer=self._initializer(data) if data else '',
            size=f' = sizeof({symbol_name})' if data else '',
        )

    def _boilerplate(self, data, include, header=True):
        lines = ['// Auto Generated File - DO NOT EDIT!']
        if header:
            lines.append('#pragma once')
        lines.append(f'#include <{include}>')
        lines.append('')
        if type(data) is list:
            lines.extend(data)
        else:
            lines.append(data)
        return '\n'.join(lines)

    def output(self, input_data, symbol_name):
        return self._declaration('inline const', symbol_name, input_data)

    def join(self, ext, filename, data):
        return self._boilerplate(data, include="cstdint", header=True)


class CSource(CHeader):
    name = 'c_source'
    components = ('hpp', 'cpp')
    extensions = ('.cpp', '.c')

    def output_hpp(self, input_data, symbol_name):
        return self._declaration('extern const', symbol_name)

    def output_cpp(self, input_data, symbol_name):
        return self._declaration('const', symbol_name, input_data)

    def join(self, ext, filename, data):
        include = filename.with_suffix('.hpp').name if ext == 'cpp' else 'cstdint'
        return self._boilerplate(data, include=include, header=(ext != 'cpp'))


class RawBinary(OutputFormat):
    name = 'raw_binary'
    extensions = ('.raw', '.bin')

    def output(self, input_data, symbol_name):
        return input_data

    def join(self, ext, filename, data):
        if type(data) is list:
            data = b''.join(data)
        return data


def parse_output_format(value):
    if type(value) is str:
        return OutputFormat.by_name.get(value, None)
    if issubclass(value, OutputFormat):
        return value
    return OutputFormat.by_name[value]

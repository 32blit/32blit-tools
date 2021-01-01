import textwrap

from ..formatter import OutputFormat


class CHeader(OutputFormat):
    name = 'c_header'
    extensions = ('.hpp', '.h')
    wrapper = textwrap.TextWrapper(
        initial_indent='    ',
        subsequent_indent='    ',
        width=80,
    )

    def _initializer(self, data):
        if type(data) is str:
            data = data.encode('utf-8')
        values = ', '.join(f'0x{c:02x}' for c in data)
        return f' = {{\n{self.wrapper.fill(values)}\n}}'

    def _declaration(self, types, symbol, data=None):
        return textwrap.dedent('''\
        {types} uint8_t {symbol}[]{initializer};
        {types} uint32_t {symbol}_length{size};
        ''').format(
            types=types,
            symbol=symbol,
            initializer=self._initializer(data) if data else '',
            size=f' = sizeof({symbol})' if data else '',
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

    def fragments(self, symbol, data):
        return self._declaration('inline const', symbol, data)

    def join(self, ext, filename, data):
        return self._boilerplate(data, include="cstdint", header=True)


class CSource(CHeader):
    name = 'c_source'
    components = ('hpp', 'cpp')
    extensions = ('.cpp', '.c')

    def fragments(self, symbol, data):
        return {
            'hpp': self._declaration('extern const', symbol),
            'cpp': self._declaration('const', symbol, data),
        }

    def join(self, ext, filename, data):
        include = filename.with_suffix('.hpp').name if ext == 'cpp' else 'cstdint'
        return self._boilerplate(data, include=include, header=(ext != 'cpp'))

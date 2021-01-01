import textwrap

from ..formatter import OutputFormat

wrapper = textwrap.TextWrapper(
    initial_indent='    ', subsequent_indent='    ', width=80
)


def c_initializer(data):
    if type(data) is str:
        data = data.encode('utf-8')
    values = ', '.join(f'0x{c:02x}' for c in data)
    return f' = {{\n{wrapper.fill(values)}\n}}'


def c_declaration(types, symbol, data=None):
    return textwrap.dedent('''\
    {types} uint8_t {symbol}[]{initializer};
    {types} uint32_t {symbol}_length{size};
    ''').format(
        types=types,
        symbol=symbol,
        initializer=c_initializer(data) if data else '',
        size=f' = sizeof({symbol})' if data else '',
    )


def c_boilerplate(data, include, header=True):
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


@OutputFormat(extensions=('.hpp', '.h'))
def c_header(symbol, data):
    return c_declaration('inline const', symbol, data)


@c_header.joiner
def c_header(ext, filename, data):
    return c_boilerplate(data, include="cstdint", header=True)


@OutputFormat(components=('hpp', 'cpp'), extensions=('.cpp', '.c'))
def c_source(symbol, data):
    return {
        'hpp': c_declaration('extern const', symbol),
        'cpp': c_declaration('const', symbol, data),
    }


@c_source.joiner
def c_source(ext, filename, data):
    include = filename.with_suffix('.hpp').name if ext == 'cpp' else 'cstdint'
    return c_boilerplate(data, include=include, header=(ext != 'cpp'))


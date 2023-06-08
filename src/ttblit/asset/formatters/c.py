import textwrap

from ..formatter import AssetFormatter

wrapper = textwrap.TextWrapper(
    break_on_hyphens=False, initial_indent='    ', subsequent_indent='    ', width=80
)


def c_initializer(data):
    if type(data) is str:
        data = data.encode('utf-8')
    values = ', '.join(f'0x{c:02x}' for c in data)
    return f' = {{\n{wrapper.fill(values)}\n}}'


def c_declaration(types, symbol, data=None):
    return textwrap.dedent(
        '''\
        {types} uint8_t {symbol}[]{initializer};
        {types} uint32_t {symbol}_length{size};
        '''
    ).format(
        types=types,
        symbol=symbol,
        initializer=c_initializer(data) if data else '',
        size=f' = sizeof({symbol})' if data else '',
    )

def c_index(symbol, path):
    return f'{{"{path}", {symbol}, sizeof({symbol})}}' if path else None

def c_boilerplate(data, include, header=True, index=None):
    lines = ['// Auto Generated File - DO NOT EDIT!']

    if header:
        lines.append('#pragma once')
    else:
        lines.append('#include <string>')

    lines.append(f'#include <{include}>')
    lines.append('')
    lines.extend(data)

    if (not header) and index:
        lines.append(textwrap.dedent('''\
        std::pair<const uint8_t*, uint32_t> get_asset_by_name(const std::string& name) {{
            struct Entry {{
                const char *name;
                const uint8_t *data;
                uint32_t size;
            }};
            static const Entry entries[] = {{
                {entries}
            }};
            for (uint32_t i = 0; i < sizeof(entries)/sizeof(entries[0]); ++i) {{
                if (name == entries[i].name)
                    return {{entries[i].data, entries[i].size}};
            }}
            return {{nullptr, 0}};
        }}
        ''').format(
            entries=',\n        '.join(index)
        ))
    return '\n'.join(lines)


@AssetFormatter(extensions=('.hpp', '.h'))
def c_header(symbol, data):
    return {None: c_declaration('inline const', symbol, data)}


@c_header.joiner
def c_header(path, fragments):
    return {None: c_boilerplate(fragments[None], include="cstdint", header=True)}


@AssetFormatter(components=('hpp', 'cpp', 'index'), extensions=('.cpp', '.c'))
def c_source(symbol, data, path):
    return {
        'hpp': c_declaration('extern const', symbol),
        'cpp': c_declaration('const', symbol, data),
        'index': c_index(symbol, path)
    }


@c_source.joiner
def c_source(path, fragments):
    include = path.with_suffix('.hpp').name
    return {
        'hpp': c_boilerplate(fragments['hpp'], include='cstdint', header=True),
        'cpp': c_boilerplate(fragments['cpp'],
                             include=include,
                             header=False,
                             index=[x for x in fragments['index'] if x]),
    }

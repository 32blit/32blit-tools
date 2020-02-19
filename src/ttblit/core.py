import pathlib
import sys
import re
import struct


class OutputFormat():
    name = 'none'
    components = None

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class CHeader(OutputFormat):
    name = 'c_header'
    extensions = ('.hpp', '.h')

    def join(self, ext, data):
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

    def join(self, ext, data):
        if type(data) is list:
            data = ''.join(data)
        return data


def output_format(value):
    return {
        'c_source': CSource,
        'h_header': CHeader,
        'raw_binary': RawBinary
    }


class Tool():
    options = {}

    def __init__(self, parser):
        self.parser = parser.add_parser(self.command, help=self.help)

    def run(self, args):
        raise NotImplementedError

    def stop(self, error_code=1):
        sys.exit(error_code)

    def output(self, output_data, output_file, output_format, force=False):
        if output_file is None:
            output_data = output_format().join(extension, output_file, output_data)
            print(output_data)
        else:
            if type(output_data) is dict:
                for extension, data in output_data.items():
                    data = output_format().join(extension, output_file, data)
                    self.write_file(output_file.with_suffix(f'.{extension}'), data, force)
            else:
                output_data = output_format().join(extension, output_file, output_data)
                self.write_file(output_file, output_data, force)

    def write_file(self, output_file, output_data, force=False):
        if output_file.exists() and not force:
            raise ValueError(f'Refusing to overwrite {output_file} (use force)')
        else:
            print(f'Writing {output_file}')
            if type(output_data) is str:
                open(output_file, 'wb').write(output_data.encode('utf-8'))
            else:
                open(output_file, 'wb').write(output_data)


class AssetBuilder(Tool):
    formats = (
        CSource,
        CHeader,
        RawBinary
    )
    no_output_file_default_format = CHeader

    def __init__(self, parser):
        Tool.__init__(self, parser)
        self.parser.add_argument('--input', type=pathlib.Path, required=True, help=f'Input file')
        if(len(self.types) > 1):
            self.parser.add_argument('--type', type=str, default=None, choices=self.types, help=f'Input file type')
        self.parser.add_argument('--output', type=pathlib.Path, default=None)
        self.parser.add_argument('--format', type=output_format, default=None, choices=self.formats, help=f'Output file format')
        self.parser.add_argument('--var', type=str, default=None, help=f'Output variable name')
        self.parser.add_argument('--force', action='store_true', help=f'Force file overwrite')

    def run(self, args):
        self._guess_format(args)

        if args.var is None:
            name = '_'.join(args.input.parts)
            name = name.replace('.', '_')
            name = re.sub('[^0-9A-Za-z_]', '_', name)
            args.var = name.lower()

    def prepare_options(self, options):
        # Helper for external callers which aren't using argparse
        # `prepare_options` will use the internal
        result = {}
        if self.options is not None and options is not None:
            for option_name, option_value in options.items():
                result[option_name] = self.options[option_name](option_value)
        return result

    def build(self, input_file, input_type, format, extra_args=None):
        if input_type not in self.types:
            raise ValueError(f'Invalid type {input_type}, choices {self.types}')
        if not issubclass(format, OutputFormat):
            formats = tuple([str(f()) for f in self.formats])
            raise ValueError(f'Invalid format {format}, choices {formats}')
        if extra_args is None:
            extra_args = {}

        if isinstance(input_file, pathlib.PurePath):
            input_data = open(input_file, 'rb').read()
        else:
            input_data = input_file

        if format.components is not None:
            output_data = {}
            for component in format.components:
                dispatch = f'{input_type}_to_{format.name}_{component}'
                output_data[component] = getattr(self, dispatch)(input_data, **extra_args)
        else:
            dispatch = f'{input_type}_to_{format.name}'
            output_data = getattr(self, dispatch)(input_data, **extra_args)

        return output_data

    def _helper_raw_to_c_source_hex(self, input_data):
        if type(input_data) is str:
            input_data = bytes(input_data, encoding='utf-8')
        return ', '.join([f'0x{c:02x}' for c in input_data])

    def string_to_c_header(self, input_string, variable):
        return f'''const uint8_t {variable}[] = {{{input_string}}};'''

    def binary_to_c_header(self, input_data, variable=None):
        input_data = self._helper_raw_to_c_source_hex(input_data)
        return self.string_to_c_header(input_data, variable)

    def binary_to_c_source_hpp(self, input_data, variable=None):
        # input_data = self._helper_raw_to_c_source_hex(input_data)
        return f'''extern const uint8_t {variable}[];'''

    def binary_to_c_source_cpp(self, input_data, variable=None):
        input_data = self._helper_raw_to_c_source_hex(input_data)
        return self.string_to_c_header(input_data, variable)

    def _guess_type(self, args):
        if args.type is not None:
            return
        for type in self.types.items():
            for extension in extensions:
                if args.input.name.endswith(extension):
                    args.type = type
                    print(f"Guessed type {type} for {args.input}")
                    return
        print(f"Unable to identify type of input file {args.input}")
        self.stop()

    def _guess_format(self, args):
        if args.format is not None:
            return
        if args.output is None:
            args.format = self.no_output_file_default_format()
            print(f"No --output given, writing to stdout assuming {self.no_output_file_default_format}")
            return
        for output_format in self.formats:
            for extension in output_format.extensions:
                if args.output.name.endswith(extension):
                    args.format = output_format
                    print(f"Guessed output format {output_format.name} for {args.output}")
                    return
        print(f"Unable to identify type of output file {args.output}")
        self.stop()
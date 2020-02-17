import pathlib
import sys
import re


class Tool():
    def __init__(self, parser):
        self.parser = parser.add_parser(self.command, help=self.help)

    def run(self, args):
        raise NotImplementedError

    def stop(self, error_code=1):
        sys.exit(error_code)


class AssetBuilder(Tool):
    formats = (
        'c_source',
        'c_header',
        'binary'
    )
    formatmap = {
        'c_source': ('.hpp', '.cpp', '.h', '.c'),
        'binary': ('.raw', '.bin')
    }
    formatcomponents = {
        'c_source': {'hpp', 'cpp'}
    }
    no_output_file_default_format = 'c_header'

    def __init__(self, parser):
        Tool.__init__(self, parser)
        self.parser.add_argument('--input', type=pathlib.Path)
        if(len(self.types) > 1):
            self.parser.add_argument('--type', type=str, default=None, choices=self.types, help=f'Input file type')
        self.parser.add_argument('--output', type=pathlib.Path, default=None)
        self.parser.add_argument('--format', type=str, default=None, choices=self.formats, help=f'Output file format')
        self.parser.add_argument('--var', type=str, default=None, help=f'Output variable name')
        self.parser.add_argument('--force', action='store_true', help=f'Force file overwrite')

    def run(self, args):
        self._guess_format(args)

        if args.var is None:
            name = '_'.join(args.input.parts)
            name = name.replace('.', '_')
            name = re.sub('[^0-9A-Za-z_]', '_', name)
            args.var = name.lower()

    def build(self, input_file, type, format, extra_args=None):
        if type not in self.types:
            raise ValueError(f'Invalid type {type}, choices {self.types}')
        if format not in self.formats:
            raise ValueError(f'Invalid type {format}, choices {self.formats}')
        if extra_args is None:
            extra_args = {}

        if isinstance(input_file, pathlib.PurePath):
            input_data = open(input_file, 'rb').read()
        else:
            input_data = input_file

        if format in self.formatcomponents:
            output_data = {}
            for component in self.formatcomponents[format]:
                dispatch = f'{type}_to_{format}_{component}'
                output_data[component] = getattr(self, dispatch)(input_data, **extra_args)
        else:
            dispatch = f'{type}_to_{format}'
            output_data = getattr(self, dispatch)(input_data, **extra_args)

        return output_data

    def _helper_raw_to_c_source_hex(self, input_data):
        return ', '.join([f'0x{c:02x}' for c in input_data])

    def binary_to_c_header(self, input_data, variable=None):
        input_data = self._helper_raw_to_c_source_hex(input_data)
        return f'''#prama once
#include <cstdint>
const uint8_t {variable}[] = {{{input_data}}};
'''

    def binary_to_c_source_hpp(self, input_data, variable=None):
        input_data = self._helper_raw_to_c_source_hex(input_data)
        return f'''#prama once
extern const uint8_t {variable}[];
'''

    def binary_to_c_source_cpp(self, input_data, variable=None):
        input_data = self._helper_raw_to_c_source_hex(input_data)
        return f'''#include <cstdint>
#include <asset.hpp>
const uint8_t {variable}[] = {{{input_data}}};
'''

    def _guess_type(self, args):
        if args.type is not None:
            return
        for type, extensions in self.typemap.items():
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
            args.format = self.no_output_file_default_format
            print(f"No --output given, writing to stdout assuming {self.no_output_file_default_format}")
            return
        for type, extensions in self.formatmap.items():
            for extension in extensions:
                if args.output.name.endswith(extension):
                    args.format = type
                    print(f"Guessed type {type} for {args.output}")
                    return
        print(f"Unable to identify type of output file {args.output}")
        self.stop()

    def output(self, output_data, output_file, output_format, force=False):
        if output_file is None:
            print(output_data)
        else:
            if type(output_data) is dict:
                for extension, data in output_data.items():
                    self.write_file(output_file.with_suffix(f'.{extension}'), data, force)
            else:
                self.write_file(output_file, output_data, force)

    def write_file(self, output_file, output_data, force=False):
        if output_file.exists() and not force:
            raise ValueError(f'Refusing to overwrite {output_file} (use force)')
        else:
            print(f'Writing {output_file}')
            open(output_file, 'wb').write(output_data.encode('utf-8'))

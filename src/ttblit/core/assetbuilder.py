import pathlib
import re

from .tool import Tool
from .outputformat import OutputFormat, output_formats, parse_output_format, CHeader


class AssetBuilder(Tool):
    formats = output_formats
    no_output_file_default_format = CHeader

    options = {
        'input_file': pathlib.Path,
        'input_type': str,
        'output_file': pathlib.Path,
        'output_format': parse_output_format,
        'symbol_name': str,
        'force': bool,
        'prefix': str
    }

    def __init__(self, parser):
        Tool.__init__(self, parser)
        self.parser.add_argument('--input_file', type=pathlib.Path, required=True, help=f'Input file')
        if(len(self.types) > 1):
            self.parser.add_argument('--input_type', type=str, default=None, choices=self.types, help=f'Input file type')
        self.parser.add_argument('--output_file', type=pathlib.Path, default=None)
        self.parser.add_argument('--output_format', type=parse_output_format, default=None, choices=self.formats, help=f'Output file format')
        self.parser.add_argument('--symbol_name', type=str, default=None, help=f'Output symbol name')
        self.parser.add_argument('--force', action='store_true', help=f'Force file overwrite')

    def _prepare(self, opts):
        """Imports a dictionary of options to class variables.

        Requires options to already be in their correct types.

        """
        for option, option_type in self.options.items():
            setattr(self, option, opts.get(option))

        if self.symbol_name is None:
            name = '_'.join(self.input_file.parts)
            name = name.replace('.', '_')
            name = re.sub('[^0-9A-Za-z_]', '_', name)
            self.symbol_name = name.lower()

        if type(self.prefix) is str:
            self.symbol_name = self.prefix + self.symbol_name

        if self.output_format is None:
            self._guess_format()
        elif not issubclass(self.output_format, OutputFormat):
            formats = tuple([str(f()) for f in self.formats])
            raise ValueError(f'Invalid format {self.output_format}, choices {formats}')

        if self.input_type is None:
            self._guess_type()
        elif self.input_type not in self.types:
            raise ValueError(f'Invalid type {self.input_type}, choices {self.types}')

    def run(self, args):
        self._prepare(vars(args))

        output_data = self.build()

        self.output(output_data, self.output_file, self.output_format, self.force)

    def prepare_options(self, opts):
        """Imports a dictionary of options to class variables.

        Used for external callers which don't invoke `run` on this class.

        Converts all options into their correct types via the specified validators.

        """
        if self.options is not None and opts is not None:
            for option_name, option_value in opts.items():
                if option_name in self.options:
                    if option_value is not None:
                        opts[option_name] = self.options[option_name](option_value)
                else:
                    print(f'Ignoring unsupported {self.command} option {option_name}')

        self._prepare(opts)

    def build(self):
        input_data = open(self.input_file, 'rb').read()

        output_data = {}

        if self.output_format.components is not None:
            for component in self.output_format.components:
                dispatch = f'{self.input_type}_to_{self.output_format.name}_{component}'
                output_data[component] = getattr(self, dispatch)(input_data)
        else:
            dispatch = f'{self.input_type}_to_{self.output_format.name}'
            output_data[self.output_file.suffix[1:]] = getattr(self, dispatch)(input_data)

        return output_data

    def _helper_raw_to_c_source_hex(self, input_data):
        if type(input_data) is str:
            input_data = bytes(input_data, encoding='utf-8')
        return ', '.join([f'0x{c:02x}' for c in input_data])

    def string_to_c_header(self, input_string):
        return f'''const uint8_t {self.symbol_name}[] = {{{input_string}}};'''

    def binary_to_c_header(self, input_data):
        input_data = self._helper_raw_to_c_source_hex(input_data)
        return self.string_to_c_header(input_data)

    def binary_to_c_source_hpp(self, input_data):
        return f'''extern const uint8_t {self.symbol_name}[];'''

    def binary_to_c_source_cpp(self, input_data):
        input_data = self._helper_raw_to_c_source_hex(input_data)
        return self.string_to_c_header(input_data)

    def _guess_type(self):
        for input_type, extensions in self.typemap.items():
            for extension in extensions:
                if self.input_file.name.endswith(extension):
                    self.input_type = input_type
                    print(f"Guessed type {input_type} for {self.input_file}")
                    return
        raise TypeError(f"Unable to identify type of input file {self.input_file}")

    def _guess_format(self):
        if self.output_file is None:
            self.output_format = self.no_output_file_default_format
            print(f"No --output given, writing to stdout assuming {self.no_output_file_default_format.name}")
            return
        for format_name, format_class in self.formats.items():
            for extension in format_class.extensions:
                if self.output_file.name.endswith(extension):
                    self.output_format = format_class
                    print(f"Guessed output format {format_class.name} for {self.output_file}")
                    return
        raise TypeError(f"Unable to identify type of output file {self.output_file}")

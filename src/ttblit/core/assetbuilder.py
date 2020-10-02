import logging
import pathlib
import re

from .outputformat import (CHeader, OutputFormat, output_formats,
                           parse_output_format)
from .tool import Tool


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
        self.parser.add_argument('--output_format', type=str, default=None, choices=self.formats.keys(), help=f'Output file format')
        self.parser.add_argument('--symbol_name', type=str, default=None, help=f'Output symbol name')
        self.parser.add_argument('--force', action='store_true', help=f'Force file overwrite')

    def prepare(self, opts):
        """Imports a dictionary of options to class variables.

        Requires options to already be in their correct types.

        """
        Tool.prepare(self, opts)

        if self.symbol_name is None:
            name = '_'.join(self.input_file.parts)
            name = name.replace('.', '_')
            name = re.sub('[^0-9A-Za-z_]', '_', name)
            self.symbol_name = name.lower()

        if type(self.prefix) is str:
            self.symbol_name = self.prefix + self.symbol_name

        if self.output_format is None:
            self._guess_format()
        elif type(self.output_format) is str:
            self.output_format = parse_output_format(self.output_format)
        elif not issubclass(self.output_format, OutputFormat):
            raise ValueError(f'Invalid format {self.output_format}, choices {self.formats.keys()}')

        if self.input_type is None:
            self._guess_type()
        elif self.input_type not in self.types:
            raise ValueError(f'Invalid type {self.input_type}, choices {self.types}')

    def run(self, args):
        self.prepare_options(vars(args))

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
                    option_type = self.options[option_name]
                    default_value = None
                    if type(option_type) is tuple:
                        option_type, default_value = option_type
                    if option_value is not None:
                        opts[option_name] = option_type(option_value)
                    else:
                        opts[option_name] = default_value
                else:
                    logging.info(f'Ignoring unsupported {self.command} option {option_name}')

        self.prepare(opts)

    def build(self):
        input_data = open(self.input_file, 'rb').read()

        output_data = self.to_binary(input_data)

        return self.output_format().build(output_data, self.symbol_name)

    def _guess_type(self):
        for input_type, extensions in self.typemap.items():
            for extension in extensions:
                if self.input_file.name.endswith(extension):
                    self.input_type = input_type
                    logging.info(f"Guessed type {input_type} for {self.input_file}")
                    return

        raise TypeError(f"Unable to identify type of input file {self.input_file}")

    def _guess_format(self):
        if self.output_file is None:
            self.output_format = self.no_output_file_default_format
            logging.warning(f"No --output given, writing to stdout assuming {self.no_output_file_default_format.name}")
            return

        for format_name, format_class in self.formats.items():
            for extension in format_class.extensions:
                if self.output_file.name.endswith(extension):
                    self.output_format = format_class
                    logging.info(f"Guessed output format {format_class.name} for {self.output_file}")
                    return

        raise TypeError(f"Unable to identify type of output file {self.output_file}")

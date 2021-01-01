import logging
import pathlib
import re

from ..core.tool import Tool
from .formatter import OutputFormat


class AssetBuilder(Tool):
    no_output_file_default_format = OutputFormat.parse('c_header')

    options = {
        'input_file': pathlib.Path,
        'input_type': str,
        'output_file': pathlib.Path,
        'output_format': OutputFormat.parse,
        'symbol_name': str,
        'force': bool,
        'prefix': str,
        'working_path': pathlib.Path
    }

    def __init__(self, parser=None):
        Tool.__init__(self, parser)

        if self.parser is not None:
            self.parser.add_argument('--input_file', type=pathlib.Path, required=True, help='Input file')
            if(len(self.types) > 1):
                self.parser.add_argument('--input_type', type=str, default=None, choices=self.types, help='Input file type')
            self.parser.add_argument('--output_file', type=pathlib.Path, default=None)
            self.parser.add_argument('--output_format', type=str, default=None, choices=OutputFormat.names(), help='Output file format')
            self.parser.add_argument('--symbol_name', type=str, default=None, help='Output symbol name')
            self.parser.add_argument('--force', action='store_true', help='Force file overwrite')

    def prepare(self, opts):
        """Imports a dictionary of options to class variables.

        Requires options to already be in their correct types.

        """
        Tool.prepare(self, opts)

        if self.symbol_name is None:
            if self.working_path is None:
                name = '_'.join(self.input_file.parts)
            else:
                name = '_'.join(self.input_file.relative_to(self.working_path).parts)
            name = name.replace('.', '_')
            name = re.sub('[^0-9A-Za-z_]', '_', name)
            self.symbol_name = name.lower()

        if type(self.prefix) is str:
            self.symbol_name = self.prefix + self.symbol_name

        self.output_format = self._get_format(self.output_format, self.output_file)

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

        return self.output_format.fragments(self.symbol_name, output_data)

    def _guess_type(self):
        for input_type, extensions in self.typemap.items():
            for extension in extensions:
                if self.input_file.name.endswith(extension):
                    self.input_type = input_type
                    logging.info(f"Guessed type {input_type} for {self.input_file}")
                    return

        raise TypeError(f"Unable to identify type of input file {self.input_file}")

    def _get_format(self, value, path):
        if value is None:
            if path is None:
                logging.warning(f"No --output given, writing to stdout assuming {self.no_output_file_default_format.name}")
                return self.no_output_file_default_format
            else:
                fmt = OutputFormat.guess(path)
                logging.info(f"Guessed output format {fmt} for {path}")
                return fmt
        else:
            return OutputFormat.parse(value)

import importlib
import logging
import pathlib
import pkgutil
import re

from ..core.tool import Tool
from . import builders
from .formatter import AssetFormatter
from .writer import AssetWriter


def make_symbol_name(base=None, working_path=None, input_file=None, input_type=None, input_subtype=None, prefix=None):
    if base is None:
        if input_file is None:
            raise NameError("No base name or input file provided.")
        if working_path is None:
            name = '_'.join(input_file.parts)
        else:
            name = '_'.join(input_file.relative_to(working_path).parts)
    else:
        name = base.format(
            filename=input_file.with_suffix('').name,
            filepath=input_file.with_suffix(''),
            fullname=input_file.name,
            fullpath=input_file,
            type=input_type,
            subtype=input_subtype
        )
    name = name.replace('.', '_')
    name = re.sub('[^0-9A-Za-z_]', '_', name)
    name = name.lower()

    if type(prefix) is str:
        name = prefix + name

    return name


class AssetBuilder:

    _by_name = {}
    _by_extension = {}

    def __init__(self, typemap):
        self.typemap = typemap

    def __call__(self, build_func):
        self.name = build_func.__name__
        self.build = build_func
        self._by_name[self.name] = self
        for subtype, extensions in self.typemap.items():
            for ext, auto in extensions.items():
                if auto:
                    if ext in self._by_extension:
                        raise KeyError(f'An automatic handler for {ext} has already been registered ({self._by_extension[ext]}).')
                    self._by_extension[ext] = f'{self.name}/{subtype}'
        return self

    def __repr__(self):
        return self.name

    @staticmethod
    def build(self, data, subtype, **kwargs):
        raise NotImplementedError

    def from_file(self, path, subtype, **kwargs):
        if subtype is None:
            subtype = self.guess_subtype(path)
        elif subtype not in self.typemap.keys():
            raise ValueError(f'Invalid subtype {subtype}, choices {self.typemap.keys()}')
        return self.build(path.read_bytes(), subtype, **kwargs)

    def guess_subtype(self, path):
        for input_type, extensions in self.typemap.items():
            if path.suffix in extensions:
                return input_type
        raise TypeError(f"Unable to identify type of input file {path.name}.")


class AssetTool(Tool):

    builder = None

    _by_name = {}
    _by_extension = {}

    options = {
        'input_file': pathlib.Path,
        'input_type': str,
        'output_file': pathlib.Path,
        'output_format': AssetFormatter.parse,
        'symbol_name': str,
        'force': bool,
        'prefix': str,
        'working_path': pathlib.Path
    }

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls._by_name[cls.command] = cls
        for type_, extensions in cls.builder.typemap.items():
            for ext, auto in extensions.items():
                if auto:
                    cls._by_extension[ext] = f'{cls.command}/{type_}'

    def __init__(self, parser=None):
        Tool.__init__(self, parser)

        if self.parser is not None:
            self.parser.add_argument('--input_file', type=pathlib.Path, required=True, help='Input file')
            if(self.builder and len(self.builder.typemap.keys()) > 1):
                self.parser.add_argument('--input_type', type=str, default=None, choices=self.builder.typemap.keys(), help='Input file type')
            self.parser.add_argument('--output_file', type=pathlib.Path, default=None)
            self.parser.add_argument('--output_format', type=str, default=None, choices=AssetFormatter.names(), help='Output file format')
            self.parser.add_argument('--symbol_name', type=str, default=None, help='Output symbol name')
            self.parser.add_argument('--force', action='store_true', help='Force file overwrite')

    def prepare(self, opts):
        """Imports a dictionary of options to class variables.

        Requires options to already be in their correct types.

        """
        for option, option_type in self.options.items():
            default_value = None
            if type(option_type) is tuple:
                option_type, default_value = option_type
            setattr(self, option, opts.get(option, default_value))

        if self.input_type is None:
            self.input_type = self.builder.guess_subtype(self.input_file)
            logging.info(f"Guessed type {self.input_type} for {self.input_file}.")
        elif self.input_type not in self.builder.typemap.keys():
            raise ValueError(f'Invalid type {self.input_type}, choices {self.builder.typemap.keys()}')

        self.symbol_name = make_symbol_name(
            base=self.symbol_name, working_path=self.working_path, input_file=self.input_file,
            input_type=self.builder.name, input_subtype=self.input_type, prefix=self.prefix
        )

    def run(self, args):
        self.prepare_options(vars(args))
        aw = AssetWriter()
        aw.add_asset(*self.build())
        aw.write(self.output_format, self.output_file, self.force, report=False)

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
        return self.symbol_name, self.to_binary()

    @classmethod
    def guess_builder(cls, path):
        try:
            return cls._by_extension[path.suffix]
        except KeyError:
            raise TypeError('Could not find a builder for {path}.')


# Load all the implementations dynamically.
for loader, module_name, is_pkg in pkgutil.walk_packages(builders.__path__, builders.__name__ + '.'):
    # We don't need to import anything from the modules. We just need to load them.
    # This will cause the decorators to run, which registers the builders.
    importlib.import_module(module_name, builders.__name__)

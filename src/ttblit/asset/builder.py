import functools
import importlib
import pathlib
import pkgutil
import re

import click

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

    @classmethod
    def guess_builder(cls, path):
        try:
            return cls._by_extension[path.suffix]
        except KeyError:
            raise TypeError('Could not find a builder for {path}.')


class AssetTool:

    _commands = {}

    def __init__(self, builder, help):
        self.builder = builder
        self.name = builder.name
        self.help = help

    def __call__(self, f):
        @click.command(self.name, help=self.help)
        @click.option('--input_file', type=pathlib.Path, required=True, help='Input file')
        @click.option('--input_type', type=click.Choice(self.builder.typemap.keys(), case_sensitive=False), default=None, help='Input file type')
        @click.option('--output_file', type=pathlib.Path, default=None, help='Output file')
        @click.option('--output_format', type=click.Choice(AssetFormatter.names(), case_sensitive=False), default=None, help='Output file format')
        @click.option('--symbol_name', type=str, default=None, help='Output symbol name')
        @click.option('--force/--keep', default=False, help='Force file overwriting')
        @functools.wraps(f)
        def cmd(input_file, input_type, output_file, output_format, symbol_name, force, **kwargs):
            aw = AssetWriter()
            aw.add_asset(symbol_name, f(input_file, input_type, **kwargs))
            aw.write(output_format, output_file, force, report=False)

        self._commands[self.name] = cmd


# Load all the implementations dynamically.
for loader, module_name, is_pkg in pkgutil.walk_packages(builders.__path__, builders.__name__ + '.'):
    # We don't need to import anything from the modules. We just need to load them.
    # This will cause the decorators to run, which registers the builders.
    importlib.import_module(module_name, builders.__name__)

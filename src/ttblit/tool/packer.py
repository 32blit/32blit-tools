import yaml
import argparse
import pathlib
import re

from ttblit.core import Tool

class Packer(Tool):
    command = 'pack'
    help = 'Pack a collection of assets for 32Blit'

    def __init__(self, parser):
        Tool.__init__(self, parser)
        self.parser.add_argument('--config', type=pathlib.Path, help='Asset config file')
        self.parser.add_argument('--output', type=pathlib.Path, help='Name for <output>.cpp and <output>.hpp')
        self.parser.add_argument('--files', nargs='+', type=pathlib.Path, help='Input files')

        self.config = {}
        self.assets = []
        self.general_options = {}

        self.asset_builders = {}

    def register_asset_builders(self, asset_builders):
        for k, v in asset_builders.items():
            self.asset_builders[k] = v

    def get_types(self):
        types = {}
        for command, asset_builder in self.asset_builders.items():
            for type, extensions in asset_builder.typemap.items():
                types[f'{command}/{type}'] = (asset_builder, extensions)
        return types

    def parse_config(self, config_file):
        config = open(config_file).read()
        config = yaml.load(config)

        self.config = config

    def filelist_to_config(self, filelist):
        config = {}

        for file in filelist:
            config[file] = {}

        self.config = {'assets.hpp': config}

    def get_general_options(self):
        for key, value in self.config.items():
            if key in ():
                self.general_options[key] = value

        for key, value in self.general_options.items():
            self.config.items.pop(key)

    def run(self, args):
        self.working_path = pathlib.Path('.')

        if args.config is not None:
            if args.config.is_file():
                self.working_path = args.config.parent
            else:
                print(f'Unable to find config at {args.config}')

        if args.config is not None:
            self.parse_config(args.config)
            print(f'Using config at {args.config}')

        elif args.files is not None:
            self.filelist_to_config(args.files)

        self.get_general_options()

        # Top level of our config is filegroups and general settings
        for target, target_options in self.config.items():
            output_file = self.working_path / target
            print(f'Preparing output target {output_file}')

            asset_sources = []
            asset_options = {}

            for key, value in target_options.items():
                if key in AssetTarget.supported_options:
                    asset_options[key] = value
            
            # Strip high-level options from the dict
            # Leaving just file source globs
            for key, value in asset_options.items():
                    target_options.pop(key)

            for file_glob, file_options in target_options.items():
                # Treat the input string as a glob, and get an input filelist
                if type(file_glob) is str:
                    input_files = list(self.working_path.glob(file_glob))
                else:
                    input_files = [file_glob]
                if len(input_files) == 0:
                    print(f'Warning: Input file(s) not found {self.working_path / file_glob}')
                    continue

                # Default file_options to an empty dict for kwargs expansion
                if file_options is None:
                    file_options = {}

                # Rewrite a single string option to `name: option`
                # This handles: `inputfile.bin: filename` entries
                if type(file_options) is str:
                    file_options = {'name': file_options}
        
                asset_sources.append(
                    AssetSource(input_files, types=self.get_types(), **file_options)
                )

            self.assets.append(AssetTarget(
                output_file,
                asset_sources,
                **asset_options
            ))

        for target in self.assets:
            output = target.build()
            print(output)


class AssetSource():
    supported_options =  ('name', 'type', 'join')

    def __init__(self, input_files, types, **kwargs):
        self.input_files = input_files
        self.types = types
        self.type = None
        self.parse_source_options(**kwargs)

    def parse_source_options(self, name=None, type=None, join=False):
        self.join = True if join else False

        self.name = name
        if type is None:
            # Glob files all have the same suffix, so we only care about the first one
            type = self.guess_type(self.input_files[0], self.types)
        self.type = type

    def guess_type(self, file, types):
        for type, settings in self.types.items():
            builder, suffixes = settings
            if file.suffix in suffixes:
                return type
        print(f'Warning: Unable to guess type, assuming raw/binary {file}')
        return 'raw/binary'

    def variable_name(self, file, prefix=None):
        if self.name is not None and self.join:
            variable = self.name
        else:
            variable = '_'.join(file.parts)
            variable = variable.replace('.', '-')
            variable = re.sub('[^0-9A-Za-z_]', '_', variable)
        return f'{prefix}{variable}'

    def build(self, format, prefix=None):
        builder, extensions = self.types[self.type]
        type = self.type.split('/')[-1]
        if prefix is None:
            prefix = ''

        output = []

        if self.join:
            file = ', '.join([str(file) for file in self.input_files])
            variable = self.variable_name(file, prefix=prefix)
            output.append(builder.build(file, type, format, {'variable': variable}))
            print(f' - {source.type} {file} -> {variable}')
        else:
            for file in self.input_files:
                variable = self.variable_name(file, prefix=prefix)
                output.append(builder.build(file, type, format, {'variable': variable}))
                print(f' - {self.type} {file} -> {variable}')

        return output

class AssetTarget():
    supported_options =  ('prefix', 'type')
    types = {
        '.hpp': 'c_header',
        '.blit': 'blit_asset',
        '.raw': 'raw_binary'
    }

    def __init__(self, output_file, sources, **kwargs):
        self.output_file = output_file
        self.sources = sources
        self.parse_asset_options(**kwargs)

    def parse_asset_options(self, prefix=None, type=None):
        self.prefix = '' if prefix is None else prefix
        if type is None:
            type = self.guess_type(self.output_file)
        else:
            if type not in self.types.values():
                raise ValueError(f'Unknown asset output type {type}')
        self.type = type

    def build(self):
        for source in self.sources:
            data = source.build(format=self.type, prefix=self.prefix)
        return data

    def guess_type(self, file):
        if file.suffix in self.types:
            return self.types[file.suffix]
        print(f'Warning: Unable to guess type, assuming raw/bin {file}')
        return 'raw'

    def pack(self):
        pass
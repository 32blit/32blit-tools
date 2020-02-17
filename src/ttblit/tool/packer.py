import yaml
import argparse
import pathlib
import re

from ttblit.core import Tool

class Packer(Tool):
    command = 'packer'
    help = 'Pack a collection of assets for 32Blit'

    def __init__(self, parser):
        Tool.__init__(self, parser)
        self.parser.add_argument('--config', type=pathlib.Path, help='Asset config file')
        self.parser.add_argument('--output', type=pathlib.Path, help='Name for <output>.cpp and <output>.hpp')
        self.parser.add_argument('--files', nargs='+', type=pathlib.Path, help='Input files')

        self.config = {}
        self.assets = []
        self.general_options = {}

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
                input_files = list(self.working_path.glob(file_glob))
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
                    AssetSource(input_files, **file_options)
                )

            self.assets.append(AssetTarget(
                output_file,
                asset_sources,
                **asset_options
            ))

        for target in self.assets:
            target.inspect_target()


class AssetSource():
    supported_options =  ('name', 'type', 'join')
    types = {
        '.png': 'sprite_packed',
        '.tmx': 'map_tiled',
        '.raw': 'raw',
        '.bin': 'bin',
    }

    def __init__(self, input_files, **kwargs):
        self.input_files = input_files
        self.parse_source_options(**kwargs)

    def parse_source_options(self, name=None, type=None, join=False):
        self.join = True if join else False

        # We're dealing with one file so it's.. kinda joined
        if len(self.input_files) == 1:
            self.join = True

        self.name = name
        if type is None:
            # Glob files all have the same suffix, so we only care about the first one
            type = self.guess_type(self.input_files[0])
        self.type = type

    def guess_type(self, file):
        if file.suffix in self.types:
            return self.types[file.suffix]
        print(f'Warning: Unable to guess type, assuming raw/bin {file}')
        return 'raw'

    def symbol_name(self, file):
        if self.name is not None and self.join:
            symbol = self.name
        else:
            symbol = '_'.join(file.parts)
        symbol = symbol.replace('.', '-')
        symbol = re.sub('[^0-9A-Za-z_]', '_', symbol)
        return symbol


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

    def inspect_target(self):
        for source in self.sources:
            if source.join:
                file = ', '.join([str(file) for file in source.input_files])
                symbol = self.symbol_name(file, source)
                print(f' - {source.type} {file} -> {symbol} -> {self.output_file}')
            else:
                for file in source.input_files:
                    symbol = self.symbol_name(file, source)
                    print(f' - {source.type} {file} -> {symbol} -> {self.output_file}')

    def guess_type(self, file):
        if file.suffix in self.types:
            return self.types[file.suffix]
        print(f'Warning: Unable to guess type, assuming raw/bin {file}')
        return 'raw'

    def symbol_name(self, file, source):
        symbol = source.symbol_name(file)

        return f'{self.prefix}{symbol}'

    def pack(self):
        pass
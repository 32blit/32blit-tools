import logging
import pathlib
import re

import yaml

from ..asset.builders import font, image, map, raw
from ..asset.writer import AssetWriter
from ..core.palette import Palette
from ..core.tool import Tool


class Packer(Tool):
    command = 'pack'
    help = 'Pack a collection of assets for 32Blit'

    def __init__(self, parser):
        Tool.__init__(self, parser)
        self.parser.add_argument('--config', type=pathlib.Path, help='Asset config file')
        self.parser.add_argument('--output', type=pathlib.Path, help='Name for output file(s) or root path when using --config')
        self.parser.add_argument('--files', nargs='+', type=pathlib.Path, help='Input files')
        self.parser.add_argument('--force', action='store_true', help='Force file overwrite')

        self.config = {}
        self.targets = []

    def parse_config(self, config_file):
        config = open(config_file).read()
        config = yaml.safe_load(config)

        self.config = config

    def filelist_to_config(self, filelist, output):
        config = {}

        for file in filelist:
            config[file] = {}

        self.config = {f'{output}': config}

    def run(self, args):
        self.working_path = pathlib.Path('.')

        if args.config is not None:
            if args.config.is_file():
                self.working_path = args.config.parent
            else:
                logging.warning(f'Unable to find config at {args.config}')
            self.parse_config(args.config)
            logging.info(f'Using config at {args.config}')

        elif args.files is not None and args.output is not None:
            self.filelist_to_config(args.files, args.output)

        if args.output is not None:
            self.destination_path = args.output
        else:
            self.destination_path = self.working_path

        # Top level of our config is filegroups and general settings
        for target, options in self.config.items():
            output_file = self.working_path / target
            logging.info(f'Preparing output target {output_file}')

            asset_sources = []
            target_options = {}

            for key, value in options.items():
                if key in ('prefix', 'type'):
                    target_options[key] = value

            # Strip high-level options from the dict
            # Leaving just file source globs
            for key in target_options:
                options.pop(key)

            for file_glob, file_options in options.items():
                # Treat the input string as a glob, and get an input filelist
                if type(file_glob) is str:
                    input_files = list(self.working_path.glob(file_glob))
                else:
                    input_files = [file_glob]
                if len(input_files) == 0:
                    logging.warning(f'Input file(s) not found {self.working_path / file_glob}')
                    continue

                # Rewrite a single string option to `name: option`
                # This handles: `inputfile.bin: filename` entries
                if type(file_options) is str:
                    file_options = {'name': file_options}

                elif file_options is None:
                    file_options = {}

                # Handle both an array of options dicts or a single dict
                if type(file_options) is not list:
                    file_options = [file_options]

                for file_opts in file_options:
                    asset_sources.append(
                        AssetSource(input_files, file_options=file_opts, working_path=self.working_path)
                    )

            self.targets.append((
                output_file,
                asset_sources,
                target_options
            ))

        self.destination_path.mkdir(parents=True, exist_ok=True)

        for path, sources, options in self.targets:
            aw = AssetWriter()
            for source in sources:
                for asset in source.build(output_file=path, prefix=options.get('prefix')):
                    aw.add_asset(*asset)

            aw.write(options.get('type'), self.destination_path / path.name, force=args.force)


class AssetSource():
    supported_options = ('name', 'type')

    def __init__(self, input_files, file_options, working_path):
        self.asset_builders = {
            image.ImageAsset.command: image.ImageAsset,
            font.FontAsset.command: font.FontAsset,
            map.MapAsset.command: map.MapAsset,
            raw.RawAsset.command: raw.RawAsset
        }

        self.input_files = input_files
        self.working_path = working_path
        self.builder_options = {}
        self.type = None
        self.name = None
        self.parse_source_options(file_options)

    def parse_source_options(self, opts):
        for option, value in opts.items():
            if option not in self.supported_options:
                # These options are passed into the Map/Image/Raw builder
                self.builder_options[option] = value
            else:
                setattr(self, option, value)

        if self.type is None:
            # Glob files all have the same suffix, so we only care about the first one
            self.type = self.guess_type(self.input_files[0])

    def guess_type(self, file):
        # We need a high-level guess type that can query the types each builder supports
        # and dispatch our builds to the right one
        for command, asset_builder in self.asset_builders.items():
            for input_type, suffixes in asset_builder.typemap.items():
                if file.suffix in suffixes:
                    return f'{command}/{input_type}'
        logging.warning(f'Unable to guess type, assuming raw/binary {file}')
        return 'raw/binary'

    def build(self, prefix=None, output_file=None):
        input_type, input_subtype = self.type.split('/')
        builder = self.asset_builders[input_type]()

        # Now we know our target builder, one last iteration through the options
        # allows some pre-processing stages to remap paths or other idiosyncrasies
        # of the yml config format.
        for option_name, option_value in builder.options.items():
            if option_name in self.builder_options:
                option_type = builder.options[option_name]
                if type(option_type) is tuple:
                    option_type, default_value = option_type

                # Ensure Palette and pathlib.Path type options for this asset builder
                # are prefixed with the working directory if they are not absolute paths
                if option_type in (Palette, pathlib.Path):
                    if not pathlib.Path(self.builder_options[option_name]).is_absolute():
                        self.builder_options[option_name] = self.working_path / self.builder_options[option_name]

        for file in self.input_files:
            symbol_name = self.name
            if symbol_name is not None:
                symbol_name = symbol_name.format(
                    filename=file.with_suffix('').name,
                    filepath=file.with_suffix(''),
                    fullname=file.name,
                    fullpath=file,
                    type=input_type,
                    subtype=input_subtype
                )
                symbol_name = symbol_name.replace('.', '_')
                symbol_name = re.sub('[^0-9A-Za-z_]', '_', symbol_name)

            self.builder_options.update({
                'input_file': file,
                'output_file': output_file,
                'input_type': input_subtype,
                'symbol_name': symbol_name,
                'working_path': self.working_path,
                'prefix': prefix
            })
            builder.prepare_options(self.builder_options)
            yield builder.build()
            logging.info(f' - {self.type} {file} -> {builder.symbol_name}')

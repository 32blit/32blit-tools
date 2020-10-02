import logging
import pathlib

import yaml

from ..core.outputformat import CHeader, CSource, RawBinary
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
        self.assets = []
        self.general_options = {}

        self.asset_builders = {}

    def register_asset_builders(self, asset_builders):
        """Register class instances for each asset builder with the packer tool."""
        for k, v in asset_builders.items():
            self.asset_builders[k] = v

    def parse_config(self, config_file):
        config = open(config_file).read()
        config = yaml.safe_load(config)

        self.config = config

    def filelist_to_config(self, filelist, output):
        config = {}

        for file in filelist:
            config[file] = {}

        self.config = {f'{output}': config}

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
                logging.warning(f'Unable to find config at {args.config}')

        if args.output is not None:
            self.destination_path = args.output
        else:
            self.destination_path = self.working_path

        if args.config is not None:
            self.parse_config(args.config)
            logging.info(f'Using config at {args.config}')

        elif args.files is not None and args.output is not None:
            self.filelist_to_config(args.files, args.output)

        self.get_general_options()

        # Top level of our config is filegroups and general settings
        for target, options in self.config.items():
            output_file = self.working_path / target
            logging.info(f'Preparing output target {output_file}')

            asset_sources = []
            target_options = {}

            for key, value in options.items():
                if key in AssetTarget.supported_options:
                    target_options[key] = value

            # Strip high-level options from the dict
            # Leaving just file source globs
            for key, value in target_options.items():
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

                asset_sources.append(
                    AssetSource(input_files, builders=self.asset_builders, file_options=file_options, working_path=self.working_path)
                )

            self.assets.append(AssetTarget(
                output_file,
                asset_sources,
                target_options
            ))

        self.destination_path.mkdir(parents=True, exist_ok=True)

        for target in self.assets:
            output = target.build()
            self.output(output, self.destination_path / target.output_file.name, target.output_format, force=args.force)


class AssetSource():
    supported_options = ('name', 'type')

    def __init__(self, input_files, builders, file_options, working_path):
        self.input_files = input_files
        self.asset_builders = builders
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

    def build(self, format, prefix=None, output_file=None):
        builder, input_type = self.type.split('/')
        builder = self.asset_builders[builder]

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

        output = []

        for file in self.input_files:
            self.builder_options.update({
                'input_file': file,
                'output_file': output_file,
                'input_type': input_type,
                'output_format': format,
                'symbol_name': self.name,
                'prefix': prefix
            })
            builder.prepare_options(self.builder_options)
            output.append(builder.build())
            logging.info(f' - {self.type} {file} -> {builder.symbol_name}')

        return output


class AssetTarget():
    supported_options = ('prefix', 'type')
    output_formats = {
        '.hpp': CHeader,
        '.cpp': CSource,
        '.blit': RawBinary,
        '.raw': RawBinary
    }

    def __init__(self, output_file, sources, target_options):
        self.output_file = output_file
        self.sources = sources
        self.parse_target_options(target_options)

    def parse_target_options(self, target_options):
        self.prefix = target_options.get('prefix')
        output_format = target_options.get('type')
        if output_format is None:
            output_format = self.guess_output_format(self.output_file)
        else:
            if type not in self.output_formats.values():
                raise ValueError(f'Unknown asset output format {output_format}')
        self.output_format = output_format

    def build(self):
        # TODO I hate this code, but because we're dealing with multiple input files
        # the output can potentially be spread across multiple files with multiple snippets
        # We need to gather each input files declarations/definitions (or otherwise) into
        # the right output file.
        output = []

        # If the output_format deals with multiple files, switch to a dict and prep the files
        if self.output_format.components is not None:
            output = {}
            for ext in self.output_format.components:
                output[ext] = []

        # Iterate through all the sources (input files) and build them
        for source in self.sources:
            data = source.build(format=self.output_format, output_file=self.output_file, prefix=self.prefix)
            for snippet in data:
                if self.output_format.components is not None:
                    # If there are multiple output files, collect all the snippets into their respective outputs
                    for ext, content in snippet.items():
                        output[ext].append(content)
                else:
                    # If it's a single file format just append the snippet to the list
                    output.append(snippet)

        return output

    def guess_output_format(self, file):
        if file.suffix in self.output_formats:
            return self.output_formats[file.suffix]
        logging.warning(f'Unable to guess type of {file}, assuming raw/binary')
        return RawBinary

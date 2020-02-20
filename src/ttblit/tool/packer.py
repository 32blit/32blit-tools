import yaml
import pathlib

from ttblit.core.tool import Tool
from ttblit.core.outputformat import CHeader, CSource, RawBinary


class Packer(Tool):
    command = 'pack'
    help = 'Pack a collection of assets for 32Blit'

    def __init__(self, parser):
        Tool.__init__(self, parser)
        self.parser.add_argument('--config', type=pathlib.Path, help='Asset config file')
        self.parser.add_argument('--output', type=pathlib.Path, help='Name for <output>.cpp and <output>.hpp')
        self.parser.add_argument('--files', nargs='+', type=pathlib.Path, help='Input files')
        self.parser.add_argument('--force', action='store_true', help=f'Force file overwrite')

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
        for target, options in self.config.items():
            output_file = self.working_path / target
            print(f'Preparing output target {output_file}')

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
                    print(f'Warning: Input file(s) not found {self.working_path / file_glob}')
                    continue

                # Rewrite a single string option to `name: option`
                # This handles: `inputfile.bin: filename` entries
                if type(file_options) is str:
                    file_options = {'name': file_options}

                elif file_options is None:
                    file_options = {}

                asset_sources.append(
                    AssetSource(input_files, builders=self.asset_builders, file_options=file_options)
                )

            self.assets.append(AssetTarget(
                output_file,
                asset_sources,
                **target_options
            ))

        for target in self.assets:
            output = target.build()
            self.output(output, target.output_file, target.output_format, force=args.force)


class AssetSource():
    supported_options = ('name', 'type')

    def __init__(self, input_files, builders, file_options):
        self.input_files = input_files
        self.asset_builders = builders
        self.builder_options = {}
        self.type = None
        self.name = None
        self.parse_source_options(file_options)

    def parse_source_options(self, opts):
        for option, value in opts.items():
            if option not in self.supported_options:
                self.builder_options[option] = value
            else:
                setattr(self, option, value)

        if self.type is None:
            # Glob files all have the same suffix, so we only care about the first one
            self.type = self.guess_type(self.input_files[0])

    def guess_type(self, file):
        for command, asset_builder in self.asset_builders.items():
            for input_type, suffixes in asset_builder.typemap.items():
                if file.suffix in suffixes:
                    return f'{command}/{input_type}'
        print(f'Warning: Unable to guess type, assuming raw/binary {file}')
        return 'raw/binary'

    def build(self, format, prefix=None, output_file=None):
        builder, input_type = self.type.split('/')
        builder = self.asset_builders[builder]

        if prefix is None:
            prefix = ''

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
            print(f' - {self.type} {file} -> {builder.symbol_name}')

        return output


class AssetTarget():
    supported_options = ('prefix', 'type')
    types = {
        '.hpp': CHeader,
        '.cpp': CSource,
        '.blit': RawBinary,
        '.raw': RawBinary
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
        self.output_format = type

    def build(self):
        output = {}
        for source in self.sources:
            data = source.build(format=self.output_format, output_file=self.output_file, prefix=self.prefix)
            for file in data:
                for ext, content in file.items():
                    if ext not in output:
                        output[ext] = []
                    output[ext].append(content)

        return output

    def guess_type(self, file):
        if file.suffix in self.types:
            return self.types[file.suffix]
        print(f'Warning: Unable to guess type, assuming raw/binary {file}')
        return 'raw/binary'

import yaml
import pathlib
import re

from ttblit.core import Tool, CHeader, CSource, RawBinary


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

            for file_glob, asset_options in options.items():
                # Treat the input string as a glob, and get an input filelist
                if type(file_glob) is str:
                    input_files = list(self.working_path.glob(file_glob))
                else:
                    input_files = [file_glob]
                if len(input_files) == 0:
                    print(f'Warning: Input file(s) not found {self.working_path / file_glob}')
                    continue

                # Default file_options to an empty dict for kwargs expansion
                file_options = {}

                # Rewrite a single string option to `name: option`
                # This handles: `inputfile.bin: filename` entries
                if type(asset_options) is str:
                    file_options = {'name': file_options}
                elif asset_options is not None:
                    for valid_option in AssetSource.supported_options:
                        value = asset_options.pop(valid_option, None)
                        if value is not None:
                            file_options[valid_option] = value

                asset_sources.append(
                    AssetSource(input_files, types=self.get_types(), builder_options=asset_options, **file_options)
                )

            self.assets.append(AssetTarget(
                output_file,
                asset_sources,
                **target_options
            ))

        for target in self.assets:
            output = target.build()
            self.output(output, target.output_file, target.type, force=args.force)


class AssetSource():
    supported_options = ('name', 'type')

    def __init__(self, input_files, types, **kwargs):
        self.input_files = input_files
        self.types = types
        self.type = None
        self.parse_source_options(**kwargs)

    def parse_source_options(self, builder_options=None, name=None, type=None, join=False):
        self.join = True if join else False
        self.builder_options = builder_options
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
        if self.name is not None and len(self.input_files) == 1:
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

        options = {}

        options.update(builder.prepare_options(self.builder_options))

        for file in self.input_files:
            variable = self.variable_name(file, prefix=prefix)
            options['variable'] = variable
            output.append(builder.build(file, type, format, extra_args=options))
            print(f' - {self.type} {file} -> {variable}')

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
        self.type = type

    def build(self):
        output = {}
        for source in self.sources:
            data = source.build(format=self.type, prefix=self.prefix)
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

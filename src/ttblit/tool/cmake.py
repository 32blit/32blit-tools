import logging
import pathlib

import yaml

from ..core.tool import Tool
from ..tool.packer import AssetTarget


class CMake(Tool):
    command = 'cmake'
    help = 'Generate CMake configuration for the asset packer'

    def __init__(self, parser):
        Tool.__init__(self, parser)
        self.parser.add_argument('--config', type=pathlib.Path, help='Asset config file')
        self.parser.add_argument('--cmake', type=pathlib.Path, help='Output CMake file', required=True)
        self.parser.add_argument('--output', type=pathlib.Path, help='Name for output file(s) or root path when using --config')

        self.config = {}
        self.general_options = {}

    def parse_config(self, config_file):
        config = open(config_file).read()
        config = yaml.safe_load(config)

        self.config = config

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

        if args.config is not None:
            self.parse_config(args.config)
            logging.info(f'Using config at {args.config}')

        if args.output is not None:
            self.destination_path = args.output
        else:
            self.destination_path = self.working_path

        if 'title' in self.config and 'description' in self.config:
            logging.info('Detected metadata config')
            self.run_for_metadata_config(args)
        else:
            logging.info('Detected asset config')
            self.run_for_asset_config(args)

    def run_for_metadata_config(self, args):
        all_inputs = []

        if 'splash' in self.config:
            file = pathlib.Path(self.config['splash']['file'])
            if file.is_absolute():
                all_inputs += [file]
            else:
                all_inputs += list(self.working_path.glob(str(file)))

        if 'icon' in self.config:
            file = pathlib.Path(self.config['icon']['file'])
            if file.is_absolute():
                all_inputs += [file]
            else:
                all_inputs += list(self.working_path.glob(str(file)))

        all_inputs = '\n'.join(f'"{x}"'.replace('\\', '/') for x in all_inputs)

        open(args.cmake, 'w').write(f'''# Auto Generated File - DO NOT EDIT!
    set(METADATA_DEPENDS
    {all_inputs}
    )
    set(METADATA_TITLE "{self.config['title']}")
    set(METADATA_AUTHOR "{self.config['author']}")
    set(METADATA_DESCRIPTION "{self.config['description']}")
    set(METADATA_VERSION "{self.config['version']}")
    ''')

    def run_for_asset_config(self, args):
        self.get_general_options()

        all_inputs = []
        all_outputs = []

        # Top level of our config is filegroups and general settings
        for target, options in self.config.items():
            target = pathlib.Path(target)

            if target.suffix in AssetTarget.output_formats:
                output_formatter = AssetTarget.output_formats[target.suffix]
            else:
                logging.warning(f'Unable to guess type of {target}, assuming raw/binary')
                output_formatter = AssetTarget.output_formats['.raw']

            if output_formatter.components is None:
                all_outputs.append(self.destination_path / target.name)
            else:
                for suffix in output_formatter.components:
                    all_outputs.append(self.destination_path / target.with_suffix(f'.{suffix}').name)

            # Strip high-level options from the dict
            # Leaving just file source globs
            for key in AssetTarget.supported_options:
                options.pop(key, None)

            for file_glob, file_options in options.items():
                # Rewrite a single string option to `name: option`
                # This handles: `inputfile.bin: filename` entries
                if type(file_options) is str:
                    file_options = {'name': file_options}

                input_files = []
                # Parse the options for any references to input files
                for key, value in file_options.items():
                    if key in ('palette') and type(value) is str:
                        input_files += list(self.working_path.glob(value))
                # Treat the input string as a glob, and get an input filelist
                if type(file_glob) is str:
                    input_files += list(self.working_path.glob(file_glob))
                else:
                    input_files += [file_glob]
                if len(input_files) == 0:
                    logging.warning(f'Input file(s) not found {self.working_path / file_glob}')
                    continue

                all_inputs += input_files

        all_inputs = '\n'.join(f'"{x}"'.replace('\\', '/') for x in all_inputs)
        all_outputs = '\n'.join(f'"{x}"'.replace('\\', '/') for x in all_outputs)

        open(args.cmake, 'w').write(f'''# Auto Generated File - DO NOT EDIT!
set(ASSET_DEPENDS
{all_inputs}
)

set(ASSET_OUTPUTS
{all_outputs}
)
''')

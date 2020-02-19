import yaml
import pathlib

from ttblit.core.tool import Tool

from ttblit.tool.packer import AssetTarget

class CMake(Tool):
    command = 'cmake'
    help = 'Generate CMake configuration for the asset packer'

    def __init__(self, parser):
        Tool.__init__(self, parser)
        self.parser.add_argument('--config', type=pathlib.Path, help='Asset config file')
        self.parser.add_argument('output')

        self.config = {}
        self.general_options = {}

    def parse_config(self, config_file):
        config = open(config_file).read()
        config = yaml.load(config)

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
                print(f'Unable to find config at {args.config}')

        if args.config is not None:
            self.parse_config(args.config)
            print(f'Using config at {args.config}')

        self.get_general_options()

        all_inputs = []
        all_outputs = []

        # Top level of our config is filegroups and general settings
        for target, options in self.config.items():
            all_outputs.append(self.working_path / target)
            
            # Strip high-level options from the dict
            # Leaving just file source globs
            for key in AssetTarget.supported_options:
                options.pop(key, None)

            for file_glob, _ in options.items():
                # Treat the input string as a glob, and get an input filelist
                if type(file_glob) is str:
                    input_files = list(self.working_path.glob(file_glob))
                else:
                    input_files = [file_glob]
                if len(input_files) == 0:
                    print(f'Warning: Input file(s) not found {self.working_path / file_glob}')
                    continue

                all_inputs += input_files

        all_inputs = '\n'.join(str(x) for x in all_inputs)
        all_outputs = '\n'.join(str(x) for x in all_outputs)

        open(args.output, 'w').write(f'''# Auto Generated File - DO NOT EDIT!
set(ASSET_DEPENDS
{all_inputs}
)

set(ASSET_OUTPUTS
{all_outputs}
)
''')

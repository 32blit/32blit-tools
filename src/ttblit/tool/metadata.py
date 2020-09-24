import pathlib
import argparse
import struct

import yaml

from ..core.outputformat import CHeader, CSource, RawBinary
from ..core.tool import Tool
from ..asset.image import ImageAsset


class Metadata(Tool):
    command = 'metadata'
    help = 'Tag a 32Blit .bin file with metadata'

    def __init__(self, parser):
        Tool.__init__(self, parser)
        self.parser.add_argument('--config', required=True, type=pathlib.Path, help='Metadata config file')
        self.parser.add_argument('--file', required=True, type=pathlib.Path, help='Input file')
        self.parser.add_argument('--force', action='store_true', help='Force file overwrite')

        self.config = {}

    def parse_config(self, config_file):
        config = open(config_file).read()
        config = yaml.safe_load(config)

        required = ['title', 'description', 'version']

        for option in required:
            if option not in config:
                raise ValueError(f'Missing required option "{option}" from {config_file}"')

        self.config = config

    def prepare_image_asset(self, name, config):
        image_file = pathlib.Path(config.get('file', ''))
        config['input_file'] = image_file
        config['output_file'] = image_file.with_suffix('.bin')
        if not image_file.is_file():
            raise ValueError(f'{name} "{image_file}"" does not exist!')
        asset = ImageAsset(argparse.ArgumentParser().add_subparsers())
        asset.prepare(config)

        return asset.to_binary(open(image_file, 'rb').read())

    def run(self, args):
        self.working_path = pathlib.Path('.')
        header = bytes('BLITGAME'.encode('utf-8'))
        eof = bytes('\0'.encode('utf-8'))

        icon = bytes()
        splash = bytes()
        bin = bytes()

        if args.file.is_file():
            print(f'Using bin file at {args.file}')
            bin = open(args.file, 'rb').read()
        else:
            print(f'Unable to find bin file at {args.file}')

        if args.config.is_file():
            self.parse_config(args.config)
            print(f'Using config at {args.config}')
        else:
            print(f'Unable to find metadata config at {args.config}')
        
        if 'icon' in self.config:
            icon = self.prepare_image_asset('icon', self.config['icon'])
        
        if 'splash' in self.config:
            splash = self.prepare_image_asset('splash', self.config['splash'])

        title = bytes(self.config.get('title').encode('utf-8'))
        description = bytes(self.config.get('description').encode('utf-8'))
        version = bytes(self.config.get('version').encode('utf-8'))

        output = (
            title + eof +
            description + eof +
            version + eof +
            icon +
            splash
        )

        length = struct.pack("H", len(output))
        output = header + length + output

        if bin.startswith(header):
            if args.force:
                length = struct.unpack("H", bin[8:10])[0]
                bin = bin[8 + 2 + length:]
                bin = output + bin
                open(args.file, 'wb').write(bin)
                print(f'Overwriting metadata in "{args.file}"')
            else:
                print(f'Refusing to overwrite metadata in "{args.file}"')
                return 1
        else:
            bin = output + bin
            open(args.file, 'wb').write(bin)

        return 0

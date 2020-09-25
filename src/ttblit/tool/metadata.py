import argparse
import pathlib
import struct

import yaml

from ..asset.image import ImageAsset
from ..core.outputformat import CHeader, CSource, RawBinary
from ..core.tool import Tool


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
                raise ValueError(f'Missing required option "{option}" from {config_file}')

        self.config = config

    def prepare_image_asset(self, name, config):
        image_file = pathlib.Path(config.get('file', ''))
        config['input_file'] = image_file
        config['output_file'] = image_file.with_suffix('.bin')
        if not image_file.is_file():
            raise ValueError(f'{name} "{image_file}" does not exist!')
        asset = ImageAsset(argparse.ArgumentParser().add_subparsers())
        asset.prepare(config)

        return asset.to_binary(open(image_file, 'rb').read())

    def binary_size(self, bin):
        return struct.unpack('<I', bin[16:20])[0] & 0xffffff

    def run(self, args):
        self.working_path = pathlib.Path('.')
        game_header = bytes('BLIT'.encode('utf-8'))
        meta_header = bytes('BLITMETA'.encode('utf-8'))
        eof = bytes('\0'.encode('utf-8'))
        has_meta = False

        icon = bytes()
        splash = bytes()
        bin = bytes()

        if args.file.is_file():
            bin = open(args.file, 'rb').read()
            if bin.startswith(game_header):
                binary_size = self.binary_size(bin)
                if len(bin) == binary_size:
                    has_meta = False
                elif len(bin) > binary_size:
                    if bin[binary_size:binary_size+8] == meta_header:
                        has_meta = True
                        bin = bin[:binary_size]
                    else:
                        raise ValueError(f'Invalid 32blit binary file {args.file}, expected {binary_size} bytes')
                print(f'Using bin file at {args.file}')
            else:
                raise ValueError(f'Invalid 32blit binary file {args.file}')
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

        if len(title) > 64:
            raise ValueError('Title should be a maximum of 64 characters!"')

        if len(description) > 1024:
            raise ValueError('Description should be a maximum of 1024 characters!')

        if len(version) > 16:
            raise ValueError('Version should be a maximum of 16 characters! eg: "v1.0.2"')

        metadata = (
            title + eof +
            description + eof +
            version + eof +
            icon +
            splash
        )

        length = struct.pack('H', len(metadata))

        metadata = meta_header + length + metadata

        if has_meta:
            if not args.force:
                print(f'Refusing to overwrite metadata in {args.file}')
                return 1

        print(f'Adding metadata to {args.file}')
        bin = bin + metadata
        open(args.file, 'wb').write(bin)

        return 0

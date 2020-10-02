import argparse
import binascii
import logging
import pathlib
import struct
from datetime import datetime

import yaml

from ..asset.image import ImageAsset
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

        required = ['title', 'description', 'version', 'author']

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

    def checksum(self, bin):
        return struct.pack('<I', binascii.crc32(bin))

    def run(self, args):
        self.working_path = pathlib.Path('.')
        game_header = 'BLIT'.encode('ascii')
        meta_header = 'BLITMETA'.encode('ascii')
        eof = '\0'.encode('ascii')
        has_meta = False

        icon = bytes()
        splash = bytes()
        checksum = bytes(4)
        bin = bytes()

        if args.file.is_file():
            bin = open(args.file, 'rb').read()
            if bin.startswith(game_header):
                binary_size = self.binary_size(bin)
                checksum = self.checksum(bin[:binary_size])
                if len(bin) == binary_size:
                    has_meta = False
                elif len(bin) > binary_size:
                    if bin[binary_size:binary_size + 8] == meta_header:
                        has_meta = True
                        bin = bin[:binary_size]
                    else:
                        raise ValueError(f'Invalid 32blit binary file {args.file}, expected {binary_size} bytes')
                logging.info(f'Using bin file at {args.file}')
            else:
                raise ValueError(f'Invalid 32blit binary file {args.file}')
        else:
            logging.warning(f'Unable to find bin file at {args.file}')

        if args.config.is_file():
            self.parse_config(args.config)
            logging.info(f'Using config at {args.config}')
        else:
            logging.warning(f'Unable to find metadata config at {args.config}')

        if 'icon' in self.config:
            icon = self.prepare_image_asset('icon', self.config['icon'])

        if 'splash' in self.config:
            splash = self.prepare_image_asset('splash', self.config['splash'])

        title = self.config.get('title').encode('ascii')
        description = self.config.get('description').encode('ascii')
        version = self.config.get('version').encode('ascii')
        author = self.config.get('author').encode('ascii')

        if len(title) > 24:
            raise ValueError('Title should be a maximum of 24 characters!"')

        if len(description) > 128:
            raise ValueError('Description should be a maximum of 128 characters!')

        if len(version) > 16:
            raise ValueError('Version should be a maximum of 16 characters! eg: "v1.0.2"')

        if len(author) > 16:
            raise ValueError('Author should be a maximum of 16 characters!')

        metadata = checksum
        metadata += datetime.now().strftime("%Y%m%dT%H%M%S").encode('ascii') + eof
        metadata += title.ljust(24 + 1, eof)  # Left justify and pad with null chars to string length + 1 (terminator)
        metadata += description.ljust(128 + 1, eof)
        metadata += version.ljust(16 + 1, eof)
        metadata += author.ljust(16 + 1, eof)
        metadata += icon
        metadata += splash

        length = struct.pack('H', len(metadata))

        metadata = meta_header + length + metadata

        if has_meta:
            if not args.force:
                logging.critical(f'Refusing to overwrite metadata in {args.file}')
                return 1

        logging.info(f'Adding metadata to {args.file}')
        bin = bin + metadata
        open(args.file, 'wb').write(bin)

        return 0

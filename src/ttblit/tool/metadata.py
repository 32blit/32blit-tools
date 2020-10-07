import argparse
import binascii
import logging
import pathlib
import struct
from datetime import datetime

import yaml
from construct import Struct, Optional, Const, PrefixedArray, Prefixed, Int32ul, Int16ul, Bytes, Checksum, PaddedString, GreedyBytes, RawCopy, this, len_
from construct.core import StreamError

from ..asset.image import ImageAsset
from ..core.tool import Tool

struct_blit_meta = Struct(
        'header' / Const(b'BLITMETA'),
        'data' / Prefixed(Int16ul, Struct(
            'checksum' / Checksum(
                Int32ul,
                lambda data: binascii.crc32(data),
                this._._.bin.data
            ),
            'date' / PaddedString(16, 'ascii'),
            'title' / PaddedString(25, 'ascii'),
            'description' / PaddedString(129, 'ascii'),
            'version' / PaddedString(17, 'ascii'),
            'author' / PaddedString(17, 'ascii'),
            'images' / GreedyBytes
        ))
)

struct_blit_bin = Struct(
    'header' / Const(b'BLIT'),
    'render' / Int32ul,
    'update' / Int32ul,
    'init' / Int32ul,
    'length' / Int32ul,
    # The length above is actually the _flash_end symbol from startup_user.s
    # it includes the offset into 0x90000000 (external flash)
    # we mask out the highest nibble to correct this into the actual bin length
    # plus subtract 20 bytes for header, symbol and length dwords
    'bin' / Bytes((this.length & 0x0FFFFFFF) - 20)
)

struct_blit_relo = Struct(
    'header' / Const(b'RELO'),
    'relocs' / PrefixedArray(Int32ul, Struct(
        'reloc' / Int32ul
    ))
)

blit_game = Struct(
    'relo' / Optional(struct_blit_relo),
    'bin' / RawCopy(struct_blit_bin),
    'meta' / Optional(struct_blit_meta)
)

blit_game_with_meta = Struct(
    'relo' / Optional(struct_blit_relo),
    'bin' / RawCopy(struct_blit_bin),
    'meta' / struct_blit_meta
)

blit_game_with_meta_and_relo = Struct(
    'relo' / struct_blit_relo,
    'bin' / RawCopy(struct_blit_bin),
    'meta' / struct_blit_meta
)


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
        if not args.file.is_file():
            raise ValueError(f'Unable to find bin file at {args.file}')

        bin = open(args.file, 'rb').read()
        try:
            game = blit_game.parse(bin)
        except StreamError:
            raise ValueError(f'Invalid 32blit binary file {args.file}')

        if args.config.is_file():
            self.parse_config(args.config)
            logging.info(f'Using config at {args.config}')
        else:
            logging.warning(f'Unable to find metadata config at {args.config}')

        if 'icon' in self.config:
            icon = self.prepare_image_asset('icon', self.config['icon'])

        if 'splash' in self.config:
            splash = self.prepare_image_asset('splash', self.config['splash'])

        title = self.config.get('title')
        description = self.config.get('description')
        version = self.config.get('version')
        author = self.config.get('author')

        if len(title) > 24:
            raise ValueError('Title should be a maximum of 24 characters!"')

        if len(description) > 128:
            raise ValueError('Description should be a maximum of 128 characters!')

        if len(version) > 16:
            raise ValueError('Version should be a maximum of 16 characters! eg: "v1.0.2"')

        if len(author) > 16:
            raise ValueError('Author should be a maximum of 16 characters!')

        if game.meta is not None:
            if not args.force:
                logging.critical(f'Refusing to overwrite metadata in {args.file}')
                return 1

        game.meta = {
            'data': {
                'date': datetime.now().strftime("%Y%m%dT%H%M%S"),
                'title': title,
                'description': description,
                'version': version,
                'author': author,
                'images': icon + splash
            }
        }

        # Force through a non-optional builder if relo symbols exist
        # since we might have modified them and want to hit parser errors
        # if something has messed up
        if game.relo is not None:
            bin = blit_game_with_meta_and_relo.build(game)
        else:
            bin = blit_game_with_meta.build(game)

        logging.info(f'Adding metadata to {args.file}')
        open(args.file, 'wb').write(bin)

        return 0
import argparse
import binascii
import logging
import math
import pathlib
import struct
from datetime import datetime

import yaml
from bitstring import BitArray, BitStream
from PIL import Image

from construct import (Array, Bytes, Checksum, Computed, Const, Int8ul,
                       Int16ul, Int32ul, Optional, PaddedString, Prefixed,
                       PrefixedArray, RawCopy, Struct, this)
from construct.core import StreamError

from ..asset.image import ImageAsset
from ..core.tool import Tool


def compute_bit_length(ctx):
    """Compute the required bit length for image data.
    Uses the count of items in the palette to determine how
    densely we can pack the image data.
    """
    return (len(ctx.palette) - 1).bit_length()


def compute_data_length(ctx):
    """Compute the required data length for palette based images.
    We need this computation here so we can use `math.ceil` and
    byte-align the result.
    """
    return math.ceil((ctx.width * ctx.height * ctx.bit_length) / 8)


struct_blit_image = Struct(
    'header' / Const(b'SPRITEPK'),
    'size' / Int16ul,
    'width' / Int16ul,
    'height' / Int16ul,
    'rows' / Int16ul,
    'cols' / Int16ul,
    'format' / Int8ul,
    'palette' / PrefixedArray(Int8ul, Struct(
        'r' / Int8ul,
        'g' / Int8ul,
        'b' / Int8ul,
        'a' / Int8ul
    )),
    'bit_length' / Computed(compute_bit_length),
    'data_length' / Computed(compute_data_length),
    'data' / Array(this.data_length, Int8ul)
)

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
        'icon' / struct_blit_image,
        'splash' / struct_blit_image
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
        self.parser.add_argument('--config', type=pathlib.Path, help='Metadata config file')
        self.parser.add_argument('--file', required=True, type=pathlib.Path, help='Input file')
        self.parser.add_argument('--force', action='store_true', help='Force file overwrite')
        self.parser.add_argument('--dump-images', action='store_true', help='Dump images from metadata')

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

    def packed_to_image(self, image):
        num_pixels = image.width * image.height
        image_icon_data = BitArray().join(BitArray(uint=x, length=8) for x in image.data)
        image_icon_data = BitStream(image_icon_data).readlist(",".join(f"uint:{image.bit_length}" for _ in range(num_pixels)))

        raw_data = bytes()
        for i in image_icon_data:
            rgba = image.palette[i]
            raw_data += bytes([
                rgba.r,
                rgba.g,
                rgba.b,
                rgba.a,
            ])

        return Image.frombytes("RGBA", (image.width, image.height), raw_data)

    def binary_size(self, bin):
        return struct.unpack('<I', bin[16:20])[0] & 0xffffff

    def checksum(self, bin):
        return struct.pack('<I', binascii.crc32(bin))

    def run(self, args):
        if not args.file.is_file():
            raise ValueError(f'Unable to find bin file at {args.file}')

        icon = b''
        splash = b''

        bin = open(args.file, 'rb').read()
        try:
            game = blit_game.parse(bin)
        except StreamError:
            raise ValueError(f'Invalid 32blit binary file {args.file}')

        # No config supplied, so dump the game info
        if args.config is None:
            print(f"""
Parsed:      {args.file.name} ({game.bin.length:,} bytes)""")
            if game.relo is not None:
                print(f"""Relocations: Yes ({len(game.relo.relocs)})""")
            else:
                print(f"""Relocations: No""")
            if game.meta is not None:
                print(f"""Metadata:    Yes

    Title:       {game.meta.data.title}
    Description: {game.meta.data.description}
    Version:     {game.meta.data.version}
    Author:      {game.meta.data.author}
""")
                if game.meta.data.icon is not None:
                    game_icon = game.meta.data.icon
                    print(f"""    Icon:        {game_icon.width}x{game_icon.height} ({len(game_icon.palette)} colours)""")
                    if args.dump_images:
                        image_icon = self.packed_to_image(game_icon)
                        image_icon_filename = args.file.with_suffix(".icon.png")
                        image_icon.save(image_icon_filename)
                        print(f"    Dumped to:   {image_icon_filename}")
                if game.meta.data.splash is not None:
                    game_splash = game.meta.data.splash
                    print(f"""    Splash:      {game_splash.width}x{game_splash.height} ({len(game_splash.palette)} colours)""")
                    if args.dump_images:
                        image_splash = self.packed_to_image(game_splash)
                        image_splash_filename = args.file.with_suffix(".splash.png")
                        image_splash.save(image_splash_filename)
                        print(f"    Dumped to:   {image_splash_filename}")
                print("")
            else:
                print(f"""Metadata:    No
""")
            return

        if args.config.is_file():
            self.parse_config(args.config)
            logging.info(f'Using config at {args.config}')
        else:
            logging.warning(f'Unable to find metadata config at {args.config}')

        if 'icon' in self.config:
            icon = self.prepare_image_asset('icon', self.config['icon'])
        else:
            raise ValueError('An 8x8 pixel icon is required!"')

        if 'splash' in self.config:
            splash = self.prepare_image_asset('splash', self.config['splash'])
        else:
            raise ValueError('A 128x96 pixel splash is required!"')

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
                'icon': struct_blit_image.parse(icon),
                'splash': struct_blit_image.parse(splash)
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

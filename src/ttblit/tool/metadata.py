import argparse
import binascii
import io
import logging
import pathlib
import struct
from datetime import datetime

import yaml
from bitstring import BitArray, BitStream
from construct.core import StreamError
from PIL import Image

from ..asset.image import ImageAsset
from ..core.struct import (blit_game, blit_game_with_meta,
                           blit_game_with_meta_and_relo, blit_icns,
                           struct_blit_image)
from ..core.tool import Tool


class Metadata(Tool):
    command = 'metadata'
    help = 'Tag a 32Blit .bin file with metadata'

    def __init__(self, parser):
        Tool.__init__(self, parser)
        self.parser.add_argument('--config', type=pathlib.Path, help='Metadata config file')
        self.parser.add_argument('--icns', type=pathlib.Path, help='macOS icon output file')
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

    def build_icns(self, config):
        image_file = pathlib.Path(config.get('file', ''))
        if not image_file.is_file():
            raise ValueError(f'{name} "{image_file}" does not exist!')

        blit_icon = Image.frombytes("P", (22, 22), b'\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x02\x02\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x02\x02\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x02\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x02\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x02\x02\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x02\x02\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x02\x02\x00\x00\x01\x01\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x02\x02\x00\x00\x01\x01\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x02\x02\x00\x00\x00\x00\x01\x01\x00\x00\x01\x01\x00\x00\x01\x01\x00\x00\x01\x01\x00\x00\x02\x02\x00\x00\x00\x00\x01\x01\x00\x00\x01\x01\x00\x00\x01\x01\x00\x00\x01\x01\x00\x00\x02\x02\x00\x00\x00\x00\x01\x01\x00\x00\x01\x01\x00\x00\x01\x01\x00\x00\x01\x01\x00\x00\x02\x02\x00\x00\x00\x00\x01\x01\x00\x00\x01\x01\x00\x00\x01\x01\x00\x00\x01\x01\x00\x00\x02\x02\x01\x01\x01\x01\x01\x01\x00\x00\x01\x01\x00\x00\x01\x01\x00\x00\x01\x01\x01\x01\x02\x02\x01\x01\x01\x01\x01\x01\x00\x00\x01\x01\x00\x00\x01\x01\x00\x00\x01\x01\x01\x01')
        blit_icon.putpalette([0, 0, 0, 255, 255, 255, 0, 255, 0])
        blit_icon = blit_icon.convert("RGBA")

        source = Image.open(image_file).convert("RGBA")

        image = Image.new("RGB", (128, 128), (0, 0, 0))

        image.paste(source, (0, 0))
        image.paste(blit_icon, (101, 101), blit_icon)

        image_bytes = io.BytesIO()
        image.convert("RGB").save(image_bytes, format="PNG")
        image_bytes.seek(0)

        del image

        return blit_icns.build({'data': image_bytes.read()})

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
            if args.icns is not None:
                if not args.icns.is_file() or args.force:
                    open(args.icns, 'wb').write(self.build_icns(self.config['splash']))
                    logging.info(f'Saved macOS icon to {args.icns}')
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

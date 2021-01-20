import argparse
import binascii
import io
import logging
import pathlib
import struct
from datetime import datetime

from bitstring import Bits, ConstBitStream
from construct.core import StreamError
from PIL import Image

from ..asset.builders.image import ImageAsset
from ..core.struct import (blit_game, blit_game_with_meta,
                           blit_game_with_meta_and_relo, blit_icns,
                           struct_blit_image, struct_blit_pixel)
from ..core.tool import Tool


class Metadata(Tool):
    command = 'metadata'
    help = 'Tag a 32Blit .blit file with metadata'

    def __init__(self, parser):
        Tool.__init__(self, parser)
        self.parser.add_argument('--config', type=pathlib.Path, help='Metadata config file')
        self.parser.add_argument('--icns', type=pathlib.Path, help='macOS icon output file')
        self.parser.add_argument('--file', type=pathlib.Path, help='Input file')
        self.parser.add_argument('--force', action='store_true', help='Force file overwrite')
        self.parser.add_argument('--dump-images', action='store_true', help='Dump images from metadata')

        self.config = {}

    def prepare_image_asset(self, name, config, working_path):
        image_file = pathlib.Path(config.get('file', ''))
        if not image_file.is_file():
            image_file = working_path / image_file
        if not image_file.is_file():
            raise ValueError(f'{name} "{image_file}" does not exist!')
        config['input_file'] = image_file
        config['output_file'] = image_file.with_suffix('.bin')
        asset = ImageAsset(argparse.ArgumentParser().add_subparsers())
        asset.prepare(config)

        return asset.to_binary(open(image_file, 'rb').read())

    def packed_to_image(self, image):
        bits = Bits(bytes=image.data)
        if image.type == 'RL':
            num_pixels = image.width * image.height
            stream = ConstBitStream(bits)
            result = []
            while len(result) < num_pixels:
                t = stream.read(1)
                if t:
                    count = stream.read(8).uint + 1
                else:
                    count = 1
                pixel = struct_blit_pixel.build(image.palette[stream.read(image.bit_length).uint])
                result.extend([pixel] * count)
            raw_data = b''.join(result)
        else:
            raw_data = b''.join(struct_blit_pixel.build(image.palette[i.uint]) for i in bits.cut(image.bit_length))
        return Image.frombytes("RGBA", (image.width, image.height), raw_data)

    def binary_size(self, bin):
        return struct.unpack('<I', bin[16:20])[0] & 0xffffff

    def checksum(self, bin):
        return struct.pack('<I', binascii.crc32(bin))

    def build_icns(self, config, working_path):
        image_file = pathlib.Path(config.get('file', ''))
        if not image_file.is_file():
            image_file = working_path / image_file
        if not image_file.is_file():
            raise ValueError(f'splash "{image_file}" does not exist!')

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
        if args.file is None and args.config is None:
            self.parser.error('the following arguments are required: --config and/or --file')

        if args.file and not args.file.is_file():
            raise ValueError(f'Unable to find bin file at {args.file}')

        icon = b''
        splash = b''

        game = None

        if args.file:
            bin = open(args.file, 'rb').read()
            try:
                game = blit_game.parse(bin)
            except StreamError:
                raise ValueError(f'Invalid 32blit binary file {args.file}')

        # No config supplied, so dump the game info
        if args.config is None:
            print(f'\nParsed:      {args.file.name} ({game.bin.length:,} bytes)')
            if game.relo is not None:
                print(f'Relocations: Yes ({len(game.relo.relocs)})')
            else:
                print('Relocations: No')
            if game.meta is not None:
                print('Metadata:    Yes')
                for field in ['title', 'description', 'version', 'author', 'category', 'url']:
                    print(f'{field.title()+":":13s}{getattr(game.meta.data, field)}')
                if len(game.meta.data.filetypes) > 0:
                    print('    Filetypes:   ')
                    for filetype in game.meta.data.filetypes:
                        print('       ', filetype)
                if game.meta.data.icon is not None:
                    game_icon = game.meta.data.icon
                    print(f'    Icon:        {game_icon.width}x{game_icon.height} ({len(game_icon.palette)} colours)')
                    if args.dump_images:
                        image_icon = self.packed_to_image(game_icon)
                        image_icon_filename = args.file.with_suffix(".icon.png")
                        image_icon.save(image_icon_filename)
                        print(f'    Dumped to:   {image_icon_filename}')
                if game.meta.data.splash is not None:
                    game_splash = game.meta.data.splash
                    print(f'    Splash:      {game_splash.width}x{game_splash.height} ({len(game_splash.palette)} colours)')
                    if args.dump_images:
                        image_splash = self.packed_to_image(game_splash)
                        image_splash_filename = args.file.with_suffix('.splash.png')
                        image_splash.save(image_splash_filename)
                        print(f'    Dumped to:   {image_splash_filename}')
            else:
                print('Metadata:    No')
            print('')
            return

        self.setup_for_config(args.config, None)

        if 'icon' in self.config:
            icon = self.prepare_image_asset('icon', self.config['icon'], self.working_path)
        else:
            raise ValueError('An 8x8 pixel icon is required!"')

        if 'splash' in self.config:
            splash = self.prepare_image_asset('splash', self.config['splash'], self.working_path)
            if args.icns is not None:
                if not args.icns.is_file() or args.force:
                    open(args.icns, 'wb').write(self.build_icns(self.config['splash'], self.working_path))
                    logging.info(f'Saved macOS icon to {args.icns}')
        else:
            raise ValueError('A 128x96 pixel splash is required!"')

        if not game:
            return

        title = self.config.get('title', None)
        description = self.config.get('description', '')
        version = self.config.get('version', None)
        author = self.config.get('author', None)
        url = self.config.get('url', '')
        category = self.config.get('category', 'none')
        filetypes = self.config.get('filetypes', [])
        if type(filetypes) is str:
            filetypes = filetypes.split(' ')

        if title is None:
            raise ValueError('Title is required!')

        if version is None:
            raise ValueError('Version is required!')

        if author is None:
            raise ValueError('Author is required!')

        if len(title) > 24:
            raise ValueError('Title should be a maximum of 24 characters!"')

        if len(description) > 128:
            raise ValueError('Description should be a maximum of 128 characters!')

        if len(version) > 16:
            raise ValueError('Version should be a maximum of 16 characters! eg: "v1.0.2"')

        if len(author) > 16:
            raise ValueError('Author should be a maximum of 16 characters!')

        if len(category) > 16:
            raise ValueError('Category should be a maximum of 16 characters!')

        if len(url) > 128:
            raise ValueError('URL should be a maximum of 128 characters!')

        if len(filetypes) > 0:
            for filetype in filetypes:
                if len(filetype) > 4:
                    raise ValueError('Filetype should be a maximum of 4 characters! (Hint, don\'t include the .)')

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
                'category': category,
                'filetypes': filetypes,
                'url': url,
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

import io
import logging
import pathlib
import textwrap
from datetime import datetime

import click
from construct.core import StreamError
from PIL import Image

from ..asset.builder import AssetBuilder
from ..asset.formatters.c import c_initializer
from ..core.struct import (blit_game, blit_game_with_meta,
                           blit_game_with_meta_and_relo, blit_icns,
                           struct_blit_image, struct_blit_image_bi, struct_blit_pixel)
from ..core.yamlloader import YamlLoader


class Metadata(YamlLoader):

    def prepare_image_asset(self, name, config, working_path):
        image_file = pathlib.Path(config.get('file', ''))
        if not image_file.is_file():
            image_file = working_path / image_file
        if not image_file.is_file():
            raise ValueError(f'{name} "{image_file}" does not exist!')
        return AssetBuilder._by_name['image'].from_file(image_file, None)

    def blit_image_to_pil(self, image):
        data = b''.join(struct_blit_pixel.build(image.data.palette[i]) for i in image.data.pixels)
        return Image.frombytes("RGBA", (image.data.width, image.data.height), data)

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

    def dump_game_metadata(self, file, game, dump_images):
        print(f'\nParsed:      {file.name} ({game.bin.length:,} bytes)')
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
                print(f'    Icon:        {game_icon.data.width}x{game_icon.data.height} ({len(game_icon.data.palette)} colours) ({game_icon.type})')
                if dump_images:
                    image_icon = self.blit_image_to_pil(game_icon)
                    image_icon_filename = file.with_suffix(".icon.png")
                    image_icon.save(image_icon_filename)
                    print(f'    Dumped to:   {image_icon_filename}')
            if game.meta.data.splash is not None:
                game_splash = game.meta.data.splash
                print(f'    Splash:      {game_splash.data.width}x{game_splash.data.height} ({len(game_splash.data.palette)} colours) ({game_splash.type})')
                if dump_images:
                    image_splash = self.blit_image_to_pil(game_splash)
                    image_splash_filename = file.with_suffix('.splash.png')
                    image_splash.save(image_splash_filename)
                    print(f'    Dumped to:   {image_splash_filename}')
        else:
            print('Metadata:    No')
        print('')

    def write_pico_bi_source(self, pico_bi_file, metadata):

        title = metadata['title'].replace('"', r'\"')
        author = metadata['author'].replace('"', r'\"')
        description = metadata['description'].replace('"', r'\"')

        icon = struct_blit_image_bi.build({'data': metadata['icon']})
        splash = struct_blit_image_bi.build({'data': metadata['splash']})

        open(pico_bi_file, "w").write(textwrap.dedent(
            '''
            #include "pico/binary_info.h"

            #include "binary_info.hpp"

            bi_decl(bi_program_name("{title}"))
            bi_decl(bi_program_description("{description}"))
            bi_decl(bi_program_version_string("{version}"))
            bi_decl(bi_program_url("{url}"))

            bi_decl(bi_string(BINARY_INFO_TAG_32BLIT, BINARY_INFO_ID_32BLIT_AUTHOR, "{author}"))
            bi_decl(bi_string(BINARY_INFO_TAG_32BLIT, BINARY_INFO_ID_32BLIT_CATEGORY, "{category}"))

            static const uint8_t metadata_icon[]{icon};
            static const uint8_t metadata_splash[]{splash};

            __bi_decl(bi_metadata_icon, &((binary_info_raw_data_t *)metadata_icon)->core, ".binary_info.keep.", __used);
            __bi_decl(bi_metadata_splash, &((binary_info_raw_data_t *)metadata_splash)->core, ".binary_info.keep.", __used);
            ''').format(title=title, description=description, version=metadata['version'], url=metadata['url'],
                        author=author, category=metadata['category'], icon=c_initializer(icon), splash=c_initializer(splash)))

        logging.info(f'Wrote pico-sdk binary info to {pico_bi_file}')

    def run(self, config, icns, pico_bi, file, force, dump_images):
        if file is None and config is None:
            raise click.UsageError('the following arguments are required: --config and/or --file')

        if file and not file.is_file():
            raise ValueError(f'Unable to find bin file at {file}')

        icon = None
        splash = None

        game = None

        if file:
            bin = open(file, 'rb').read()
            try:
                game = blit_game.parse(bin)
            except StreamError:
                raise ValueError(f'Invalid 32blit binary file {file}')

        # No config supplied, so dump the game info
        if config is None:
            self.dump_game_metadata(file, game, dump_images)
            return

        self.setup_for_config(config, None)

        if 'icon' in self.config:
            icon = struct_blit_image.parse(self.prepare_image_asset('icon', self.config['icon'], self.working_path))
            if icon.data.width != 8 or icon.data.height != 8:
                icon = None

        if icon is None:
            raise ValueError('An 8x8 pixel icon is required!"')

        if 'splash' in self.config:
            splash = struct_blit_image.parse(self.prepare_image_asset('splash', self.config['splash'], self.working_path))

            if splash.data.width != 128 or splash.data.height != 96:
                splash = None

            if icns is not None:
                if not icns.is_file() or force:
                    open(icns, 'wb').write(self.build_icns(self.config['splash'], self.working_path))
                    logging.info(f'Saved macOS icon to {icns}')

        if splash is None:
            raise ValueError('A 128x96 pixel splash is required!"')

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


        metadata = {
            'date': datetime.now().strftime("%Y%m%dT%H%M%S"),
            'title': title,
            'description': description,
            'version': version,
            'author': author,
            'category': category,
            'filetypes': filetypes,
            'url': url,
            'icon': icon,
            'splash': splash
        }

        if pico_bi is not None:
            if not pico_bi.is_file() or force:
                self.write_pico_bi_source(pico_bi, metadata)

        # Add to the game file
        if not game:
            return

        if game.meta is not None:
            if not force:
                logging.critical(f'Refusing to overwrite metadata in {file}')
                return 1

        game.meta = {
            'data': metadata
        }

        # Force through a non-optional builder if relo symbols exist
        # since we might have modified them and want to hit parser errors
        # if something has messed up
        if game.relo is not None:
            bin = blit_game_with_meta_and_relo.build(game)
        else:
            bin = blit_game_with_meta.build(game)

        logging.info(f'Adding metadata to {file}')
        open(file, 'wb').write(bin)

        return 0


@click.command('metadata', help='Tag a 32Blit .blit file with metadata')
@click.option('--config', type=pathlib.Path, help='Metadata config file')
@click.option('--icns', type=pathlib.Path, help='macOS icon output file')
@click.option('--pico-bi', type=pathlib.Path, help='pico-sdk binary info source file output')
@click.option('--file', type=pathlib.Path, help='Input file')
@click.option('--force', is_flag=True, help='Force file overwrite')
@click.option('--dump-images', is_flag=True, help='Dump images from metadata')
def metadata_cli(config, icns, pico_bi, file, force, dump_images):
    Metadata().run(config, icns, pico_bi, file, force, dump_images)

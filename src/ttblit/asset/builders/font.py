import io
import struct

import click
import freetype
from PIL import Image

from ..builder import AssetBuilder, AssetTool

font_typemap = {
    'image': {
        '.png': False,
        '.gif': False,
    },
    'font': {
        # possibly other freetype supported formats...
        '.ttf': True,
    }
}


def process_image_font(data, num_chars, height, horizontal_spacing, space_width):
    # Since we already have bytes, we need to pass PIL an io.BytesIO object
    image = Image.open(io.BytesIO(data)).convert('1')
    w, h = image.size

    if height != 0 and height != h:
        raise TypeError("Specified height does not match image height")

    char_width = w // num_chars
    char_height = h

    font_data = []
    font_w = []  # per character width for variable-width mode

    for c in range(0, num_chars):
        char_w = 0

        for x in range(0, char_width):
            byte = 0

            for y in range(0, h):
                bit = y % 8

                # next byte
                if bit == 0 and y > 0:
                    font_data.append(byte)
                    byte = 0

                if image.getpixel((x + c * char_width, y)) != 0:
                    byte |= 1 << bit
                    if x + 1 > char_w:
                        char_w = x + 1

            font_data.append(byte)

        if c == 0:  # space
            font_w.append(space_width)
        else:
            font_w.append(char_w + horizontal_spacing)

    return font_data, font_w, char_width, char_height


def process_ft_font(data, num_chars, base_char, height):
    if height == 0:
        raise TypeError("Height must be specified for font files")

    face = freetype.Face(io.BytesIO(data))

    # request height
    face.set_pixel_sizes(0, height)

    char_width = 0
    char_height = 0
    min_y = height
    font_w = []

    # measure the actual size of the characters (may not match requested)
    for c in range(0, num_chars):
        face.load_char(c + base_char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO)

        font_w.append(face.glyph.advance.x >> 6)

        if face.glyph.bitmap.width + face.glyph.bitmap_left > char_width:
            char_width = face.glyph.bitmap.width + face.glyph.bitmap_left

        if (height - face.glyph.bitmap_top) + face.glyph.bitmap.rows > char_height:
            char_height = height - face.glyph.bitmap_top + face.glyph.bitmap.rows

        if height - face.glyph.bitmap_top < min_y:
            min_y = height - face.glyph.bitmap_top

    char_height -= min_y  # trim empty space at the top

    font_data = []

    # now do the conversion
    for c in range(0, num_chars):
        face.load_char(c + base_char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO)

        x_off = face.glyph.bitmap_left
        y_off = height - face.glyph.bitmap_top - min_y

        for x in range(0, char_width):
            byte = 0

            for y in range(0, char_height):
                bit = y % 8

                # next byte
                if bit == 0 and y > 0:
                    font_data.append(byte)
                    byte = 0

                if x < x_off or x - x_off >= face.glyph.bitmap.width or y < y_off or y - y_off >= face.glyph.bitmap.rows:
                    continue

                # freetype monochrome bitmaps are the other way around
                if face.glyph.bitmap.buffer[(x - x_off) // 8 + (y - y_off) * face.glyph.bitmap.pitch] & (
                        0x80 >> ((x - x_off) & 7)):
                    byte |= 1 << bit

            font_data.append(byte)

    return font_data, font_w, char_width, char_height


@AssetBuilder(typemap=font_typemap)
def font(data, subtype, num_chars=96, base_char=ord(' '), height=0, horizontal_spacing=1, vertical_spacing=1, space_width=3):
    if subtype == 'image':
        font_data, font_w_data, char_width, char_height = process_image_font(
            data, num_chars, height, horizontal_spacing, space_width
        )
    elif subtype == 'font':
        font_data, font_w_data, char_width, char_height = process_ft_font(
            data, num_chars, base_char, height
        )
    else:
        raise TypeError(f'Unknown subtype {subtype} for font.')

    head_data = struct.pack('<BBBB', num_chars, char_width, char_height, vertical_spacing)

    data = bytes('FONT', encoding='utf-8')
    data += head_data
    data += bytes(font_w_data)
    data += bytes(font_data)

    return data


@AssetTool(font, 'Convert fonts for 32Blit')
@click.option('--height', type=int, default=0, help='Font height (calculated from image if not specified)')
@click.option('--horizontal-spacing', type=int, default=1, help='Additional space between characters for variable-width mode')
@click.option('--vertical-spacing', type=int, default=1, help='Space between lines')
@click.option('--space-width', type=int, default=3, help='Width of the space character')
def font_cli(input_file, input_type, **kwargs):
    return font.from_file(input_file, input_type, **kwargs)

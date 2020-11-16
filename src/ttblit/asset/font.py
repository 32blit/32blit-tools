import io
import struct

import freetype
from PIL import Image

from ..core.assetbuilder import AssetBuilder


class FontAsset(AssetBuilder):
    command = 'font'
    help = 'Convert fonts for 32Blit'
    types = ['image', 'font']
    typemap = {
        'image': ('.png', '.gif'),
        'font': ('.ttf')  # possibly other freetype supported formats...
    }

    def __init__(self, parser):
        self.options.update({
            'height': (int, 0),
            'horizontal_spacing': (int, 1),
            'vertical_spacing': (int, 1),
            'space_width': (int, 3)
        })

        AssetBuilder.__init__(self, parser)

        self.height = 0
        self.horizontal_spacing = 1
        self.vertical_spacing = 1
        self.space_width = 3
        self.base_char = ord(' ')
        self.num_chars = 96

        self.parser.add_argument('--height', type=int, default=0, help='Font height (calculated from image if not specified)')
        self.parser.add_argument('--horizontal-spacing', type=int, default=1, help='Additional space between characters for variable-width mode')
        self.parser.add_argument('--vertical-spacing', type=int, default=1, help='Space between lines')
        self.parser.add_argument('--space-width', type=int, default=1, help='Width of the space character')

    def prepare(self, args):
        AssetBuilder.prepare(self, args)

    def process_image_font(self, input_data):
        # Since we already have bytes, we need to pass PIL an io.BytesIO object
        image = Image.open(io.BytesIO(input_data)).convert('1')
        w, h = image.size

        if self.height != 0 and self.height != h:
            raise TypeError("Specified height does not match image height")

        char_width = w // self.num_chars
        char_height = h

        font_data = []
        font_w = []  # per character width for variable-width mode

        for c in range(0, self.num_chars):
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
                font_w.append(self.space_width)
            else:
                font_w.append(char_w + self.horizontal_spacing)

        return font_data, font_w, char_width, char_height

    def process_ft_font(self, input_data):
        if self.height == 0:
            raise TypeError("Height must be specified for font files")

        face = freetype.Face(io.BytesIO(input_data))

        # request height
        face.set_pixel_sizes(0, self.height)

        char_width = 0
        char_height = 0
        min_y = self.height
        font_w = []

        # measure the actual size of the characters (may not match requested)
        for c in range(0, self.num_chars):
            face.load_char(c + self.base_char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO)

            font_w.append(face.glyph.advance.x >> 6)

            if face.glyph.bitmap.width + face.glyph.bitmap_left > char_width:
                char_width = face.glyph.bitmap.width + face.glyph.bitmap_left

            if (self.height - face.glyph.bitmap_top) + face.glyph.bitmap.rows > char_height:
                char_height = self.height - face.glyph.bitmap_top + face.glyph.bitmap.rows

            if self.height - face.glyph.bitmap_top < min_y:
                min_y = self.height - face.glyph.bitmap_top

        char_height -= min_y  # trim empty space at the top

        font_data = []

        # now do the conversion
        for c in range(0, self.num_chars):
            face.load_char(c + self.base_char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO)

            x_off = face.glyph.bitmap_left
            y_off = self.height - face.glyph.bitmap_top - min_y

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
                    if face.glyph.bitmap.buffer[(x - x_off) // 8 + (y - y_off) * face.glyph.bitmap.pitch] & (0x80 >> ((x - x_off) & 7)):
                        byte |= 1 << bit

                font_data.append(byte)

        return font_data, font_w, char_width, char_height

    def to_binary(self, input_data):
        if self.input_type == 'image':
            font_data, font_w_data, char_width, char_height = self.process_image_font(input_data)
        elif self.input_type == 'font':
            font_data, font_w_data, char_width, char_height = self.process_ft_font(input_data)

        font_data = bytes(font_data)

        head_data = struct.pack('<BBBB', self.num_chars, char_width, char_height, self.vertical_spacing)

        data = bytes('FONT', encoding='utf-8')
        data += head_data
        data += bytes(font_w_data)
        data += bytes(font_data)

        return data

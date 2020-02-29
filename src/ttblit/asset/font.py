import io
import struct

from PIL import Image

from ..core.assetbuilder import AssetBuilder


class FontAsset(AssetBuilder):
    command = 'font'
    help = 'Convert fonts for 32Blit'
    types = ['image']
    typemap = {
        'image': ('.png', '.gif')
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
        font_w = [] # per character width for variable-width mode

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

            if c == 0: # space
                font_w.append(self.space_width)
            else:
                font_w.append(char_w + self.horizontal_spacing)

        return font_data, font_w, char_width, char_height

    def to_binary(self, input_data):
        font_data, font_w_data, char_width, char_height = self.process_image_font(input_data)

        font_data = bytes(font_data)

        head_data = struct.pack('<BBBB', self.num_chars, char_width, char_height, self.vertical_spacing)

        data = bytes('FONT', encoding='utf-8')
        data += head_data
        data += bytes(font_w_data)
        data += bytes(font_data)

        return data

import pathlib
import argparse
import struct
import math

from ttblit.core import AssetBuilder

from PIL import Image
from bitstring import BitArray


class Sprite(AssetBuilder):
    command = 'sprite'
    help = 'Convert an image file into an RGBA palette-based 32Blit sprite'
    types = ['sprite']
    typemap = {
        'sprite': ('.png', '.gif')
    }

    def __init__(self, parser):
        AssetBuilder.__init__(self, parser)
        self.parser.add_argument('--palette', type=self.load_palette, default=[], help='Image or palette file of colours to use')
        self.parser.add_argument('--transparent', type=self.load_colour, help='Transparent colour')
        self.parser.add_argument('--packed', action='store_true', help='Pack into bits depending on palette colour count')
        self.palette = None

    def colour_distance(self, c1, c2):
        (r1, g1, b1, a1) = c1
        (r2, g2, b2, a2) = c2
        return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2 + (a1 - a2) ** 2)

    def run(self, args):
        AssetBuilder.run(self, args)

        self.palette = args.palette

        extra_args = {
            'variable': args.var,
            'palette': self.palette,
            'packed': args.packed
        }

        if args.transparent is not None:
            r, g, b = args.transparent
            if (r, g, b, 0xff) in self.palette:
                p = self.palette.index((r, g, b, 0xff))
                self.palette[p] = (r, g, b, 0x00)
                print(f'Found transparent colour ({r},{g},{b}) in palette')
                extra_args['transparent'] = p
            else:
                print(f'Could not find transparent colour ({r},{g},{b}) in palette')


        output_data = self.build(args.input, self.types[0], args.format, extra_args)

        self.output(output_data, args.output, args.format, args.force)

    def load_colour(self, colour):
        if len(colour) == 6:
            return tuple(bytes.fromhex(colour))
        if ',' in colour:
            return [int(c, 10) for c in colour.split(',')]

    def load_palette(self, palette_file):
        palette_file = pathlib.Path(palette_file)
        # TODO support more palette formats
        if palette_file.suffix == '.act':
            palette = open(palette_file, 'rb').read()
            if len(palette) < 772:
                raise argparse.ArgumentTypeError(f'palette {palette_file} is not a valid Adobe .act')

            size, _ = struct.unpack('>HH', palette[-4:])
            width = 1
            height = size
            palette = Image.frombytes('RGB', (width, height), palette)
        else:
            palette = Image.open(palette_file)
            palette = palette.convert('RGBA')
            width, height = palette.size
            if width * height > 256:
                raise argparse.ArgumentTypeError(f'palette {palette_file} has too many pixels {width}x{height}={width*height} (max 256)')
            print(f'Using palette {palette_file} {width}x{height}')

        palette_list = []
        for x in range(width):
            for y in range(height):
                if palette.mode == 'RGBA':
                    r, g, b, a = palette.getpixel((x, y))
                else:
                    r, g, b = palette.getpixel((x, y))
                    a = 0xff # Opaque
                palette_list.append((r, g, b, a))

        return palette_list

    def quantize_image(self, input_data, variable=None, palette=None, transparent=None):
        import io
        # Since we already have bytes, we need to pass PIL an io.BytesIO object
        image = Image.open(io.BytesIO(input_data)).convert('RGBA')
        w, h = image.size
        output_image = Image.new('P', (w, h))
        for y in range(h):
            for x in range(w):
                r, g, b, a = image.getpixel((x, y))
                if (r, g, b, a) in palette:
                    index = palette.index((r, g, b, a))
                    # print(f'Re-mapping ({r}, {g}, {b}, {a}) at ({x}x{y}) to ({index})')
                # Anything with 0 alpha that's not in the palette might as well be the transparent colour
                elif a == 0 and transparent is not None:
                    index = transparent
                    print(f'Re-mapping ({r}, {g}, {b}, {a}) at ({x}x{y}) to transparent at ({index})')
                elif len(palette) < 256:
                    palette.append((r, g, b, a))
                    index = len(palette) - 1
                    print(f'Failed to find ({r}, {g}, {b}, {a}) at ({x}x{y}), added at ({index})')
                else:
                    index = 0
                    print(f'Failed to find ({r}, {g}, {b}, {a}) at ({x}x{y}), re-mapped to ({index})')
                output_image.putpixel((x, y), index)

        return output_image

    def _palette_to_list(self, palette):
        result = []
        for r, g, b, a in palette:
            result.append(r)
            result.append(g)
            result.append(b)
            result.append(a)
        return result

    def _sprite_to_binary(self, input_data, variable=None, palette=None, transparent=None, packed=None):
        image = self.quantize_image(input_data, variable, palette, transparent)
        palette_data = bytes(self._palette_to_list(palette))

        if packed:
            bit_length = (len(palette) - 1).bit_length()
            image_data = BitArray().join(BitArray(uint=x, length=bit_length) for x in image.tobytes()).tobytes()
        else:
            image_data = image.tobytes()

        palette_length = struct.pack('<H', len(palette))
        image_size = struct.pack('<HH', *image.size)

        return palette_length, palette_data, image_size, image_data

    def sprite_to_binary(self, input_data, variable=None, palette=None, transparent=None, packed=None):
        palette_length, palette_data,
        image_size, image_data = self._sprite_to_binary(input_data, variable, palette, transparent, packed)

        data = bytes('SPRITEPK' if packed else 'SPRITERW')
        data += palette_length
        data += palette_data
        data += image_size
        data += image_data

        return data

    def sprite_to_c_header(self, input_data, variable=None, palette=None, transparent=None, packed=None):
        palette_length, palette_data, image_size, image_data = self._sprite_to_binary(input_data, variable, palette, transparent, packed)

        header = self._helper_raw_to_c_source_hex('SPRITEPK' if packed else 'SPRITERW')
        palette_data = self._helper_raw_to_c_source_hex(palette_data)
        image_data = self._helper_raw_to_c_source_hex(image_data)
        image_size = ', '.join([hex(x) for x in image_size])
        palette_size = ', '.join([hex(x) for x in palette_length])

        data = f'''
{header},
{palette_size}, // Palette entry count
// Palette entries
{palette_data},
{image_size}, // Image width / height
// Image data
{image_data}
'''

        return data
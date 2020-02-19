import pathlib
import argparse
import struct
import math
import io

from ttblit.core import AssetBuilder
from ttblit.palette import Palette, Colour

from PIL import Image
from bitstring import BitArray


class Sprite(AssetBuilder):
    command = 'sprite'
    help = 'Convert an image file into an RGBA palette-based 32Blit sprite'
    types = ['sprite']
    typemap = {
        'sprite': ('.png', '.gif')
    }
    # TODO: maybe expand this so that parser arguments can be generated from the options dict
    options = {
        'palette': Palette,
        'transparent': Colour,
        'packed': bool,
        'strict': bool
    }

    def __init__(self, parser):
        AssetBuilder.__init__(self, parser)
        self.parser.add_argument('--palette', type=Palette, default=Palette(), help='Image or palette file of colours to use')
        self.parser.add_argument('--transparent', type=Colour, help='Transparent colour')
        self.parser.add_argument('--packed', action='store_true', help='Pack into bits depending on palette colour count')
        self.parser.add_argument('--strict', action='store_true', help='Reject colours not in the palette')
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
            p = self.palette.set_transparent_colour(r, g, b)
            if p is not None:
                print(f'Found transparent colour ({r},{g},{b}) in palette')
                extra_args['transparent'] = args.transparent
            else:
                print(f'Could not find transparent colour ({r},{g},{b}) in palette')


        output_data = self.build(args.input, self.types[0], args.format, extra_args)

        self.output(output_data, args.output, args.format, args.force)

    def quantize_image(self, input_data, palette, transparent, strict):
        if strict and len(palette) == 0:
            raise TypeError("Attempting to enforce strict colours with an empty palette, did you really want to do this?")
        # Since we already have bytes, we need to pass PIL an io.BytesIO object
        image = Image.open(io.BytesIO(input_data)).convert('RGBA')
        w, h = image.size
        output_image = Image.new('P', (w, h))
        for y in range(h):
            for x in range(w):
                r, g, b, a = image.getpixel((x, y))
                if (r, g, b) == tuple(transparent):
                    a = 0x00
                index = palette.get_entry(r, g, b, a, strict=strict)
                output_image.putpixel((x, y), index)

        return output_image

    def _sprite_to_binary(self, input_data, **kwargs):
        variable = kwargs.get('variable', None)
        palette = kwargs.get('palette', None)
        transparent = kwargs.get('transparent', None)
        packed = kwargs.get('packed', None)
        strict = kwargs.get('strict', False)

        if transparent is not None:
            r, g, b = transparent
            palette.set_transparent_colour(r, g, b)

        if palette is None:
            palette = Palette()

        image = self.quantize_image(input_data, palette, transparent, strict)
        palette_data = palette.tobytes()

        if packed:
            bit_length = palette.bit_length()
            image_data = BitArray().join(BitArray(uint=x, length=bit_length) for x in image.tobytes()).tobytes()
        else:
            image_data = image.tobytes()

        palette_length = struct.pack('<H', len(palette))
        image_size = struct.pack('<HH', *image.size)

        return palette_length, palette_data, image_size, image_data

    def sprite_to_binary(self, input_data, variable=None, palette=None, transparent=None, packed=None):
        packed = kwargs.get('packed', None)

        palette_length, palette_data,
        image_size, image_data = self._sprite_to_binary(input_data, **kwargs)

        data = bytes('SPRITEPK' if packed else 'SPRITERW')
        data += palette_length
        data += palette_data
        data += image_size
        data += image_data

        return data

    def sprite_to_c_source_cpp(self, input_data, **kwargs):
        return self.sprite_to_c_header(input_data, **kwargs)

    def sprite_to_c_source_hpp(self, input_data, **kwargs):
        variable = kwargs.get('variable', None)
        return self.binary_to_c_source_hpp(input_data, variable)

    def sprite_to_c_header(self, input_data, **kwargs):
        packed = kwargs.get('packed', None)
        variable = kwargs.get('variable', None)
 
        palette_length, palette_data, image_size, image_data = self._sprite_to_binary(input_data, **kwargs)

        payload_size = len('SPRITEPK')
        payload_size += 2  # Payload bytes
        payload_size += 2  # Width
        payload_size += 2  # height
        payload_size += 2  # Rows
        payload_size += 2  # Cols
        payload_size += 1  # Format
        payload_size += 1  # Length of palette
        payload_size += len(palette_data) # Palette entries
        payload_size += len(image_data)

        payload_size = ', '.join([hex(x) for x in struct.pack('H', payload_size)])

        header = self._helper_raw_to_c_source_hex('SPRITEPK' if packed else 'SPRITERW')
        palette_data = self._helper_raw_to_c_source_hex(palette_data)
        image_data = self._helper_raw_to_c_source_hex(image_data)
        image_size = ', '.join([hex(x) for x in image_size])
        # palette_size = ', '.join([hex(x) for x in palette_length])
        palette_size = hex(palette_length[0])

        data = f'''
{header},
{payload_size},
0x80, 0x00,
0x80, 0x00,
0x10, 0x00,
0x10, 0x00,

0x02, // Format

{palette_size}, // Palette entry count
// Palette entries
{palette_data},
// Image data
{image_data}
'''
        return self.string_to_c_header(data, variable)
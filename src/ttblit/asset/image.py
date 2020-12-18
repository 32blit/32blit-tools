import io
import logging
from math import ceil

from bitstring import BitArray
from PIL import Image

from ..core.assetbuilder import AssetBuilder
from ..core.palette import Colour, Palette, type_palette
from ..core.struct import struct_blit_image


class ImageAsset(AssetBuilder):
    command = 'image'
    help = 'Convert images/sprites for 32Blit'
    types = ['image']
    typemap = {
        'image': ('.png', '.gif')
    }

    def __init__(self, parser=None):
        self.options.update({
            'palette': (Palette, Palette()),
            'transparent': Colour,
            'packed': (str, 'yes'),
            'strict': (bool, False)
        })

        AssetBuilder.__init__(self, parser)

        self.palette = None
        self.transparent = None
        self.packed = True
        self.strict = False

        if self.parser is not None:
            self.parser.add_argument('--palette', type=type_palette, default=None, help='Image or palette file of colours to use')
            self.parser.add_argument('--transparent', type=Colour, help='Transparent colour')
            self.parser.add_argument('--packed', type=str, nargs='?', default='yes', choices=('yes', 'no'), help='Pack into bits depending on palette colour count')
            self.parser.add_argument('--strict', action='store_true', help='Reject colours not in the palette')

    def prepare(self, args):
        AssetBuilder.prepare(self, args)

        if type(self.packed) is not bool:
            self.packed = self.packed == 'yes'

        if self.transparent is not None:
            r, g, b = self.transparent
            p = self.palette.set_transparent_colour(r, g, b)
            if p is not None:
                logging.info(f'Found transparent colour ({r},{g},{b}) in palette')
            else:
                logging.warning(f'Could not find transparent colour ({r},{g},{b}) in palette')

    def quantize_image(self, input_data):
        if self.strict and len(self.palette) == 0:
            raise TypeError("Attempting to enforce strict colours with an empty palette, did you really want to do this?")
        # Since we already have bytes, we need to pass PIL an io.BytesIO object
        image = Image.open(io.BytesIO(input_data)).convert('RGBA')
        w, h = image.size
        output_image = Image.new('P', (w, h))
        for y in range(h):
            for x in range(w):
                r, g, b, a = image.getpixel((x, y))
                if self.transparent is not None and (r, g, b) == tuple(self.transparent):
                    a = 0x00
                index = self.palette.get_entry(r, g, b, a, strict=self.strict)
                output_image.putpixel((x, y), index)

        return output_image

    def to_binary(self, input_data):
        image = self.quantize_image(input_data)

        if self.packed:
            bit_length = self.palette.bit_length()

            break_even = ceil(8 / (bit_length + 1))

            image_data_raw = image.tobytes()
            image_len = len(image_data_raw)
            image_bits = BitArray()
            i = 0
            while i < image_len:
                repeat = 0
                v = image_data_raw[i]

                for j in range(i + 1, image_len):
                    if image_data_raw[j] != v or repeat == 0xFF:
                        break

                    repeat += 1

                if repeat >= break_even:
                    image_bits.append('0b1')
                    image_bits.append(bytes([repeat]))
                    i += repeat
                else:
                    image_bits.append('0b0')

                image_bits.append(BitArray(uint=v, length=bit_length))
                i += 1

            image_data_rl = image_bits.tobytes()
            image_data_pk = BitArray().join(BitArray(uint=x, length=bit_length) for x in image.tobytes()).tobytes()

            if len(image_data_pk) < len(image_data_rl):
                image_type = 'PK'
                image_data = image_data_pk
            else:
                image_type = 'RL'
                image_data = image_data_rl

        else:
            image_data = image.tobytes()
            image_type = 'RW'

        return struct_blit_image.build({
            'type': image_type,
            'width': image.size[0],
            'height': image.size[1],
            'palette_entries': len(self.palette),
            'palette': self.palette.tostruct(),
            'data': image_data
        })

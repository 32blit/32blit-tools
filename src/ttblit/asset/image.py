import io
import struct

from bitstring import BitArray
from PIL import Image

from ..core.assetbuilder import AssetBuilder
from ..core.palette import Colour, Palette


class ImageAsset(AssetBuilder):
    command = 'image'
    help = 'Convert images/sprites for 32Blit'
    types = ['image']
    typemap = {
        'image': ('.png', '.gif')
    }

    def __init__(self, parser):
        self.options.update({
            'palette': Palette,
            'transparent': Colour,
            'packed': bool,
            'strict': bool
        })

        AssetBuilder.__init__(self, parser)

        self.palette = None
        self.transparent = None
        self.packed = False
        self.strict = False

        self.parser.add_argument('--palette', type=Palette, default=None, help='Image or palette file of colours to use')
        self.parser.add_argument('--transparent', type=Colour, help='Transparent colour')
        self.parser.add_argument('--packed', action='store_true', help='Pack into bits depending on palette colour count')
        self.parser.add_argument('--strict', action='store_true', help='Reject colours not in the palette')

    def _prepare(self, args):
        AssetBuilder._prepare(self, args)

        if self.transparent is not None:
            r, g, b = self.transparent
            p = self.palette.set_transparent_colour(r, g, b)
            if p is not None:
                print(f'Found transparent colour ({r},{g},{b}) in palette')
            else:
                print(f'Could not find transparent colour ({r},{g},{b}) in palette')

        if self.palette is None:
            self.palette = Palette()

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

    def _image_to_binary(self, input_data):
        image = self.quantize_image(input_data)
        palette_data = self.palette.tobytes()

        if self.packed:
            bit_length = self.palette.bit_length()
            image_data = BitArray().join(BitArray(uint=x, length=bit_length) for x in image.tobytes()).tobytes()
        else:
            image_data = image.tobytes()

        palette_length = struct.pack('<H', len(self.palette))
        image_size = struct.pack('<HH', *image.size)

        return palette_length, palette_data, image_size, image_data

    def to_binary(self, input_data):
        header_size = 20

        image = self.quantize_image(input_data)
        palette_data = self.palette.tobytes()

        if self.packed:
            bit_length = self.palette.bit_length()
            image_data = BitArray().join(BitArray(uint=x, length=bit_length) for x in image.tobytes()).tobytes()
        else:
            image_data = image.tobytes()

        palette_size = struct.pack('<B', len(self.palette))

        payload_size = struct.pack('<H', len(image_data) + len(palette_data) + header_size)
        image_size = struct.pack('<HH', *image.size)

        data = bytes('SPRITEPK' if self.packed else 'SPRITERW', encoding='utf-8')
        data += payload_size
        data += image_size
        data += bytes([0x10, 0x00, 0x10, 0x00])  # Rows/cols deprecated
        data += b'\x02'                          # Pixel format
        data += palette_size
        data += palette_data
        data += image_data

        return data

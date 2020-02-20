import struct
import io

from ttblit.core.assetbuilder import AssetBuilder
from ttblit.core.palette import Palette, Colour

from PIL import Image
from bitstring import BitArray


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

    def image_to_binary(self, input_data):
        palette_length, palette_data, image_size, image_data = self._image_to_binary(input_data)

        data = bytes('SPRITEPK' if self.packed else 'SPRITERW')
        data += palette_length
        data += palette_data
        data += image_size
        data += image_data

        return data

    def image_to_c_source_cpp(self, input_data):
        return self._image_to_c_header(input_data)

    def image_to_c_source_hpp(self, input_data):
        return self.binary_to_c_source_hpp(input_data)

    def image_to_c_header(self, input_data):
        return self._image_to_c_header(input_data)

    def _image_to_c_header(self, input_data):
        palette_length, palette_data, image_size, image_data = self._image_to_binary(input_data)

        payload_size = len('SPRITEPK')
        payload_size += 2  # Payload bytes
        payload_size += 2  # Width
        payload_size += 2  # height
        payload_size += 2  # Rows
        payload_size += 2  # Cols
        payload_size += 1  # Format
        payload_size += 1  # Length of palette
        payload_size += len(palette_data)  # Palette entries
        payload_size += len(image_data)

        payload_size = ', '.join([hex(x) for x in struct.pack('H', payload_size)])

        header = self._helper_raw_to_c_source_hex('SPRITEPK' if self.packed else 'SPRITERW')
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
        return self.string_to_c_header(data)

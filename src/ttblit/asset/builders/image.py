import io
import logging

from PIL import Image

from ...core.palette import Colour, Palette, type_palette
from ...core.struct import struct_blit_image
from ..builder import AssetBuilder, AssetTool

image_typemap = {
    'image': {
        '.png': True,
        '.gif': True,
    }
}


@AssetBuilder(typemap=image_typemap)
def image(data, subtype, palette=None, transparent=None, strict=False, packed=True):
    if palette is None:
        palette = Palette()
    else:
        palette = Palette(palette)
    if transparent is not None:
        transparent = Colour(transparent)
        p = palette.set_transparent_colour(*transparent)
        if p is not None:
            logging.info(f'Found transparent {transparent} in palette')
        else:
            logging.warning(f'Could not find transparent {transparent} in palette')
    # Since we already have bytes, we need to pass PIL an io.BytesIO object
    image = Image.open(io.BytesIO(data)).convert('RGBA')
    image = palette.quantize_image(image, transparent=transparent, strict=strict)
    return struct_blit_image.build({
        'type': None if packed else 'RW',  # None means let the compressor decide
        'data': {
            'width': image.size[0],
            'height': image.size[1],
            'palette': palette.tostruct(),
            'pixels': image.tobytes(),
        },
    })


class ImageAsset(AssetTool):
    command = 'image'
    help = 'Convert images/sprites for 32Blit'
    builder = image

    def __init__(self, parser=None):
        self.options.update({
            'palette': (Palette, Palette()),
            'transparent': Colour,
            'packed': (str, 'yes'),
            'strict': (bool, False)
        })

        super().__init__(parser)

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
        super().prepare(args)

        if type(self.packed) is not bool:
            self.packed = self.packed == 'yes'

        if self.transparent is not None:
            r, g, b = self.transparent
            p = self.palette.set_transparent_colour(r, g, b)
            if p is not None:
                logging.info(f'Found transparent colour ({r},{g},{b}) in palette')
            else:
                logging.warning(f'Could not find transparent colour ({r},{g},{b}) in palette')

    def to_binary(self):
        return self.builder.from_file(
            self.input_file, self.input_type,
            palette=self.palette, transparent=self.transparent, strict=self.strict, packed=self.packed
        )

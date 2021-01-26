import binascii
import math

from construct import (Adapter, Bytes, Checksum, Const, GreedyBytes, Int8ul,
                       Int16ul, Int32ub, Int32ul, Optional, PaddedString,
                       Prefixed, PrefixedArray, RawCopy, Rebuild, Struct, len_,
                       this)

from .compression import ImageCompressor


class PaletteCountAdapter(Adapter):
    def _decode(self, obj, context, path):
        if obj == 0:
            obj = 256
        return obj

    def _encode(self, obj, context, path):
        if obj == 256:
            obj = 0
        return obj


class ImageSizeAdapter(Adapter):
    """
    Adds the header and type size to the size field.
    The size field itself is already counted.
    """
    def _decode(self, obj, context, path):
        return obj - 8

    def _encode(self, obj, context, path):
        return obj + 8


struct_blit_pixel = Struct(
    'r' / Int8ul,
    'g' / Int8ul,
    'b' / Int8ul,
    'a' / Int8ul
)

struct_blit_image_compressed = Struct(
    'header' / Const(b'SPRITE'),
    'type' / PaddedString(2, 'ASCII'),
    'data' / Prefixed(ImageSizeAdapter(Int32ul), Struct(
        'width' / Int16ul,
        'height' / Int16ul,
        'format' / Const(0x02, Int8ul),
        'palette' / PrefixedArray(PaletteCountAdapter(Int8ul), struct_blit_pixel),
        'pixels' / GreedyBytes,
    ), includelength=True)
)

struct_blit_image = ImageCompressor(struct_blit_image_compressed)

struct_blit_meta = Struct(
    'header' / Const(b'BLITMETA'),
    'data' / Prefixed(Int16ul, Struct(
        'checksum' / Checksum(
            Int32ul,
            lambda data: binascii.crc32(data),
            this._._.bin.data
        ),
        'date' / PaddedString(16, 'ascii'),
        'title' / PaddedString(25, 'ascii'),
        'description' / PaddedString(129, 'ascii'),
        'version' / PaddedString(17, 'ascii'),
        'author' / PaddedString(17, 'ascii'),
        Const(b'BLITTYPE'),
        'category' / PaddedString(17, 'ascii'),
        'url' / PaddedString(129, 'ascii'),
        'filetypes' / PrefixedArray(Int8ul, PaddedString(5, 'ascii')),
        'icon' / struct_blit_image,
        'splash' / struct_blit_image
    ))
)

struct_blit_meta_standalone = Struct(
    'header' / Const(b'BLITMETA'),
    'data' / Prefixed(Int16ul, Struct(
        'checksum' / Int32ul,
        'date' / PaddedString(16, 'ascii'),
        'title' / PaddedString(25, 'ascii'),
        'description' / PaddedString(129, 'ascii'),
        'version' / PaddedString(17, 'ascii'),
        'author' / PaddedString(17, 'ascii'),
        Const(b'BLITTYPE'),
        'category' / PaddedString(17, 'ascii'),
        'url' / PaddedString(129, 'ascii'),
        'filetypes' / PrefixedArray(Int8ul, PaddedString(5, 'ascii')),
        'icon' / struct_blit_image,
        'splash' / struct_blit_image
    ))
)

struct_blit_bin = Struct(
    'header' / Const(b'BLIT'),
    'render' / Int32ul,
    'update' / Int32ul,
    'init' / Int32ul,
    'length' / Int32ul,
    # The length above is actually the _flash_end symbol from startup_user.s
    # it includes the offset into 0x90000000 (external flash)
    # we mask out the highest nibble to correct this into the actual bin length
    # plus subtract 20 bytes for header, symbol and length dwords
    'bin' / Bytes((this.length & 0x0FFFFFFF) - 20)
)

struct_blit_relo = Struct(
    'header' / Const(b'RELO'),
    'relocs' / PrefixedArray(Int32ul, Struct(
        'reloc' / Int32ul
    ))
)

blit_game = Struct(
    'relo' / Optional(struct_blit_relo),
    'bin' / RawCopy(struct_blit_bin),
    'meta' / Optional(struct_blit_meta)
)

blit_game_with_meta = Struct(
    'relo' / Optional(struct_blit_relo),
    'bin' / RawCopy(struct_blit_bin),
    'meta' / struct_blit_meta
)

blit_game_with_meta_and_relo = Struct(
    'relo' / struct_blit_relo,
    'bin' / RawCopy(struct_blit_bin),
    'meta' / struct_blit_meta
)


def compute_icns_data_length(ctx):
    """Compute the required data length for palette based images.
    We need this computation here so we can use `math.ceil` and
    byte-align the result.
    """
    return math.ceil((ctx.width * ctx.height * ctx.bit_length) / 8)


blit_icns = Struct(
    'header' / Const(b'icns'),
    'size' / Rebuild(Int32ub, len_(this.data) + 16),
    'type' / Const(b'ic07'),  # 128×128 icon in PNG format
    'data_length' / Rebuild(Int32ub, len_(this.data) + 8),
    'data' / Bytes(this.data_length - 8)
)

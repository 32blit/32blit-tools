import binascii
import math

from construct import (Adapter, Array, Bytes, Checksum, Computed, Const,
                       GreedyBytes, Int8ul, Int16ul, Int32ub, Int32ul,
                       Optional, PaddedString, Prefixed, PrefixedArray,
                       RawCopy, Rebuild, Struct, len_, this)


def compute_bit_length(ctx):
    """Compute the required bit length for image data.
    Uses the count of items in the palette to determine how
    densely we can pack the image data.
    """
    if ctx.type == "RW":
        return 8
    else:
        return max(1, (ctx.palette_entries - 1).bit_length())


def compute_data_length(ctx):
    """Compute the required data length for palette based images.
    We need this computation here so we can use `math.ceil` and
    byte-align the result.
    """
    return math.ceil((ctx.width * ctx.height * ctx.bit_length) / 8)


class PaletteCountAdapter(Adapter):
    def _decode(self, obj, context, path):
        if obj == 0:
            obj = 256
        return obj

    def _encode(self, obj, context, path):
        if obj == 256:
            obj = 0
        return obj


struct_blit_pixel = Struct(
    'r' / Int8ul,
    'g' / Int8ul,
    'b' / Int8ul,
    'a' / Int8ul
)

struct_blit_image = Struct(
    'header' / Const(b'SPRITE'),
    'type' / PaddedString(2, 'ASCII'),
    'size' / Rebuild(Int32ul, len_(this.data) + (this.palette_entries * 4) + 18),
    'width' / Int16ul,
    'height' / Int16ul,
    'format' / Const(0x02, Int8ul),
    'palette_entries' / PaletteCountAdapter(Int8ul),
    'palette' / Array(this.palette_entries, struct_blit_pixel),
    'bit_length' / Computed(compute_bit_length),
    'data_length' / Computed(compute_data_length),
    'data' / Array(this.data_length, Int8ul)
)

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

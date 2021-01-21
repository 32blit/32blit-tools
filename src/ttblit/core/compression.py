from math import ceil

from bitstring import BitArray, Bits, ConstBitStream
from construct import Adapter


class RL:
    @staticmethod
    def repetitions(seq):
        """Input: sequence of values, Output: sequence of (value, repeat count)."""
        i = iter(seq)
        prev = next(i)
        count = 1
        for v in i:
            if v == prev:
                count += 1
            else:
                yield prev, count
                prev = v
                count = 1
        yield prev, count

    @staticmethod
    def compress(data, bit_length):
        """Input: data bytes, bit length, Output: RLE'd bytes"""
        # TODO: This could be made more efficient by encoding the run-length
        # as count-n, ie 0 means a run of n, where n = break_even. Then we
        # can encode longer runs up to 255+n. But this needs changes in the
        # blit engine.
        break_even = ceil(8 / (bit_length + 1))
        bits = BitArray()

        for value, count in RL.repetitions(data):
            while count > break_even:
                chunk = min(count, 0x100)
                bits.append('0b1')
                bits.append(bytes([chunk - 1]))
                count -= chunk
                bits.append(BitArray(uint=value, length=bit_length))
            for x in range(count):
                bits.append('0b0')
                bits.append(BitArray(uint=value, length=bit_length))
        return bits.tobytes()

    @staticmethod
    def decompress(data, bit_length, output_length):
        stream = ConstBitStream(bytes=data)
        result = []
        while len(result) < output_length:
            t = stream.read(1)
            if t:
                count = stream.read(8).uint + 1
            else:
                count = 1
            result.extend([stream.read(bit_length).uint] * count)
        return bytes(result)


class PK:
    @staticmethod
    def compress(data, bit_length):
        return BitArray().join(BitArray(uint=x, length=bit_length) for x in data).tobytes()

    @staticmethod
    def decompress(data, bit_length, num_pixels):
        return bytes(i.uint for i in Bits(bytes=data).cut(bit_length))


packers = {cls.__name__: cls for cls in (PK, RL)}


class ImageCompressor(Adapter):

    def bit_length(self, obj):
        """Compute the required bit length for image data.
        Uses the count of items in the palette to determine how
        densely we can pack the image data.
        """
        if obj.get('type', None) == "RW":
            return 8
        else:
            return max(1, (len(obj['data']['palette']) - 1).bit_length())

    def num_pixels(self, obj):
        return obj['data']['width'] * obj['data']['height']

    def _decode(self, obj, context, path):
        if obj['type'] != 'RW':
            obj['data']['pixels'] = packers[obj['type']].decompress(
                obj['data']['pixels'], self.bit_length(obj), self.num_pixels(obj)
            )
        return obj

    def _encode(self, obj, context, path):
        obj = obj.copy()   # we are going to mutate this, so make a deep copy
        obj['data'] = obj['data'].copy()
        bl = self.bit_length(obj)
        if obj.get('type', None) is None:
            all_comp = [(k, v.compress(obj['data']['pixels'], bl)) for k, v in packers.items()]
            best = min(all_comp, key=lambda x: len(x[1]))
            # Put the best type back into the object.
            obj['type'] = best[0]
            obj['data']['pixels'] = best[1]
        elif obj['type'] != 'RW':
            obj['data']['pixels'] = packers[obj['type']].compress(obj['data']['pixels'], bl)
        return obj

def test_image_struct():
    from ttblit.core.struct import struct_blit_image
    from ttblit.core.palette import Palette

    def check_image(i, t):
        b = struct_blit_image.build(i)
        p = struct_blit_image.parse(b)
        assert p.type == t
        assert p.data.width == i['data']['width']
        assert p.data.height == i['data']['height']
        assert len(p.data.pixels) == i['data']['width'] * i['data']['height']
        # Building from a parsed object should always yield an identical result
        b1 = struct_blit_image.build(p)
        assert b1 == b

    # TODO: Use a real image to test?
    palette = Palette()
    palette.get_entry(255, 255, 255, 255)

    image_dict = {
        'data': {
            'width': 0x10,
            'height': 0x4,
            'palette': palette.tostruct(),
            'pixels': b'\x00' * 0x40,
        }
    }

    check_image(image_dict, 'RL')

    image_dict['type'] = 'RW'
    check_image(image_dict, 'RW')

    image_dict['type'] = 'PK'
    check_image(image_dict, 'PK')

    image_dict['type'] = 'RL'
    check_image(image_dict, 'RL')

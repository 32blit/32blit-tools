def test_image_struct(test_resources):
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

    # default splash image
    palette = Palette()
    palette.get_entry(  0,   0,   0, 255)
    palette.get_entry( 99, 175, 227, 255)
    palette.get_entry( 45, 100, 143, 255)
    palette.get_entry( 56,  66,  67, 255)
    palette.get_entry( 52,  62,  59, 255)
    palette.get_entry( 37,  55,  60, 255)
    palette.get_entry( 12,  29,  33, 255)
    palette.get_entry(234,  92, 181, 255)
    palette.get_entry(100, 246, 178, 255)
    palette.get_entry(234, 226,  81, 255)
    palette.get_entry(140, 139, 144, 255)

    image_dict = {
        'data': {
            'width': 128,
            'height': 96,
            'palette': palette.tostruct(),
            'pixels': open(test_resources / 'no_image.raw', 'rb').read(),
        }
    }

    check_image(image_dict, 'RL')

    image_dict['type'] = 'RW'
    check_image(image_dict, 'RW')

    image_dict['type'] = 'PK'
    check_image(image_dict, 'PK')

    image_dict['type'] = 'RL'
    check_image(image_dict, 'RL')

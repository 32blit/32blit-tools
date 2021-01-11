import base64
import tempfile

import pytest


@pytest.fixture
def test_input_file():
    temp_png = tempfile.NamedTemporaryFile('wb', suffix='.png')
    temp_png.write(base64.b64decode(b'iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAMAAAD04JH5AAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAyNpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+IDx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IkFkb2JlIFhNUCBDb3JlIDUuNi1jMTQ4IDc5LjE2NDAzNiwgMjAxOS8wOC8xMy0wMTowNjo1NyAgICAgICAgIj4gPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4gPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIgeG1sbnM6eG1wPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RSZWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZVJlZiMiIHhtcDpDcmVhdG9yVG9vbD0iQWRvYmUgUGhvdG9zaG9wIDIxLjAgKFdpbmRvd3MpIiB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOjE5NkU4OENBNTk3NDExRUFCMTgyODFBRDFGMTZDODJGIiB4bXBNTTpEb2N1bWVudElEPSJ4bXAuZGlkOjE5NkU4OENCNTk3NDExRUFCMTgyODFBRDFGMTZDODJGIj4gPHhtcE1NOkRlcml2ZWRGcm9tIHN0UmVmOmluc3RhbmNlSUQ9InhtcC5paWQ6MTk2RTg4Qzg1OTc0MTFFQUIxODI4MUFEMUYxNkM4MkYiIHN0UmVmOmRvY3VtZW50SUQ9InhtcC5kaWQ6MTk2RTg4Qzk1OTc0MTFFQUIxODI4MUFEMUYxNkM4MkYiLz4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz4ohDCNAAAACVBMVEUAAAD///8A/wDg4n4DAAAAmklEQVR42uzZMQqAMAxA0er9D+1Wl1ITijTi+6PQ8qYYsTVJUu/Ilj569gAAAABqAtIDM30UAAAAoDrAuwAAAODLK9nCdAQAAACoBHh/FD84AQAAALYDJEnpQTk6MPgCD98LAAAAUAiQXkXT9wIAAADUBEx/qEQBg2fhUQwAAAAAAAAAAHADFnbCKSC8EwIAAABsAkjST7sEGACd4xph9WtahAAAAABJRU5ErkJggg=='))
    temp_png.flush()
    return temp_png


def test_image_png_cli_no_args(parsers):
    from ttblit.asset.builders import image

    parser, subparser = parsers

    image = image.ImageAsset(subparser)

    with pytest.raises(SystemExit):
        parser.parse_args(['image'])


def test_image_png_cli(parsers, test_input_file):
    from ttblit.asset.builders import image

    parser, subparser = parsers

    image = image.ImageAsset(subparser)

    args = parser.parse_args(['image', '--input_file', test_input_file.name, '--output_format', 'c_header'])

    image.run(args)


def test_image_png_cli_unpacked(parsers, test_input_file):
    from ttblit.asset.builders import image

    parser, subparser = parsers

    image = image.ImageAsset(subparser)

    args = parser.parse_args(['image', '--input_file', test_input_file.name, '--packed', 'no', '--output_format', 'c_header'])

    image.run(args)


def test_image_png_cli_packed(parsers, test_input_file):
    from ttblit.asset.builders import image

    parser, subparser = parsers

    image = image.ImageAsset(subparser)

    args = parser.parse_args(['image', '--input_file', test_input_file.name, '--packed', '--output_format', 'c_header'])

    image.run(args)


def test_image_png_cli_strict_palette_act(parsers, test_input_file):
    from ttblit.asset.builders import image

    parser, subparser = parsers

    image = image.ImageAsset(subparser)

    with tempfile.NamedTemporaryFile('wb', suffix='.act') as test_palette_file:
        test_palette_file.write(b'\x00\x00\x00')  # Write black colour
        test_palette_file.write(b'\x00\xff\x00')  # Write green colour
        test_palette_file.write(b'\xff\xff\xff')  # Write white colour
        test_palette_file.write(b'\x00' * 759)  # Pad to 772 bytes
        test_palette_file.write(b'\x00\x03')  # Write size
        test_palette_file.write(b'\x00\x00')  # Ignored bytes
        test_palette_file.flush()
        args = parser.parse_args(['image', '--input_file', test_input_file.name, '--output_format', 'c_header', '--strict', '--palette', test_palette_file.name])
        image.run(args)


def test_image_png_cli_strict_palette_pal(parsers, test_input_file):
    from ttblit.asset.builders import image

    parser, subparser = parsers

    image = image.ImageAsset(subparser)

    with tempfile.NamedTemporaryFile('wb', suffix='.pal') as test_palette_file:
        test_palette_file.write(b'\x00\x00\x00')  # Write black colour
        test_palette_file.write(b'\x00\xff\x00')  # Write green colour
        test_palette_file.write(b'\xff\xff\xff')  # Write white colour
        test_palette_file.write(b'\x00' * (768 - 9))  # Pad to 768 bytes
        test_palette_file.flush()
        args = parser.parse_args(['image', '--input_file', test_input_file.name, '--output_format', 'c_header', '--strict', '--palette', test_palette_file.name])
        image.run(args)


def test_image_png_cli_strict_palette_pal_missing(parsers, test_input_file):
    from ttblit.asset.builders import image

    parser, subparser = parsers

    image = image.ImageAsset(subparser)

    with tempfile.NamedTemporaryFile('wb', suffix='.pal') as test_palette_file:
        test_palette_file.write(b'\x00\x00\x00')  # Write black colour
        test_palette_file.write(b'\xff\xff\xff')  # Write white colour
        test_palette_file.write(b'\x00' * (768 - 6))  # Pad to 768 bytes
        test_palette_file.flush()
        args = parser.parse_args(['image', '--input_file', test_input_file.name, '--output_format', 'c_header', '--strict', '--palette', test_palette_file.name])
        with pytest.raises(TypeError):
            image.run(args)


def test_image_png_cli_strict_nopalette(parsers, test_input_file):
    from ttblit.asset.builders import image

    parser, subparser = parsers

    image = image.ImageAsset(subparser)

    args = parser.parse_args(['image', '--input_file', test_input_file.name, '--output_format', 'c_header', '--strict'])

    with pytest.raises(TypeError):
        image.run(args)


def test_image_png_cli_strict_palette_pal_transparent(parsers, test_input_file):
    from ttblit.asset.builders import image

    parser, subparser = parsers

    image = image.ImageAsset(subparser)

    with tempfile.NamedTemporaryFile('wb', suffix='.pal') as test_palette_file:
        test_palette_file.write(b'\x00\x00\x00')  # Write black colour
        test_palette_file.write(b'\x00\xff\x00')  # Write green colour
        test_palette_file.write(b'\xff\xff\xff')  # Write white colour
        test_palette_file.write(b'\x00' * (768 - 9))  # Pad to 768 bytes
        test_palette_file.flush()

        args = parser.parse_args([
            'image',
            '--input_file', test_input_file.name,
            '--output_format', 'c_header',
            '--strict',
            '--palette', test_palette_file.name,
            '--transparent', '0,255,0'])  # Make green transparent

        image.run(args)

        args = parser.parse_args([
            'image',
            '--input_file', test_input_file.name,
            '--output_format', 'c_header',
            '--strict',
            '--palette', test_palette_file.name,
            '--transparent', '88,88,88'])  # Invalid colour

        image.run(args)


def test_image_png_cli_packed_blank(parsers):
    from ttblit.asset.builders import image

    parser, subparser = parsers

    image = image.ImageAsset(subparser)

    with tempfile.NamedTemporaryFile('wb', suffix='.png') as temp_png:
        # this is a solid white image
        temp_png.write(base64.b64decode(b'iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AcxV9TxQ8qDq0g4pChOlkQFXHUKhShQqgVWnUwufQLmjQkKS6OgmvBwY/FqoOLs64OroIg+AHi5Oik6CIl/i8ptIjx4Lgf7+497t4BQr3MNKtjHNB020wl4mImuyp2vaIHAwhDRFhmljEnSUn4jq97BPh6F+NZ/uf+HH1qzmJAQCSeZYZpE28QT2/aBud94ggryirxOfGYSRckfuS64vEb54LLAs+MmOnUPHGEWCy0sdLGrGhqxFPEUVXTKV/IeKxy3uKslauseU/+wlBOX1nmOs1hJLCIJUjUkYIqSijDRoxWnRQLKdqP+/iHXL9ELoVcJTByLKACDbLrB/+D391a+ckJLykUBzpfHOdjBOjaBRo1x/k+dpzGCRB8Bq70lr9SB2Y+Sa+1tOgR0L8NXFy3NGUPuNwBBp8M2ZRdKUhTyOeB9zP6piwQvgV617zemvs4fQDS1FXyBjg4BEYLlL3u8+7u9t7+PdPs7wdkRXKhyqpX4AAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+QJFRQDAWzTXhEAAAAZdEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIEdJTVBXgQ4XAAAAFUlEQVQI12P8//8/AzbAxIADDE4JAFbUAw1h62h+AAAAAElFTkSuQmCC'))
        temp_png.flush()

        args = parser.parse_args(['image', '--input_file', temp_png.name, '--packed', '--output_format', 'c_header'])

        image.run(args)


def test_image_png_cli_packed_multi_transparent(parsers):
    from ttblit.asset.builders import image

    parser, subparser = parsers

    image = image.ImageAsset(subparser)

    with tempfile.NamedTemporaryFile('wb', suffix='.png') as temp_png:
        # many colours with alpha 0
        temp_png.write(base64.b64decode(b'iVBORw0KGgoAAAANSUhEUgAAAIAAAAAICAYAAAAx3fd+AAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AcxV9TxQ8qDq0g4pChOlkQFXHUKhShQqgVWnUwufQLmjQkKS6OgmvBwY/FqoOLs64OroIg+AHi5Oik6CIl/i8ptIjx4Lgf7+497t4BQr3MNKtjHNB020wl4mImuyp2vaIHAwhDRFhmljEnSUn4jq97BPh6F+NZ/uf+HH1qzmJAQCSeZYZpE28QT2/aBud94ggryirxOfGYSRckfuS64vEb54LLAs+MmOnUPHGEWCy0sdLGrGhqxFPEUVXTKV/IeKxy3uKslauseU/+wlBOX1nmOs1hJLCIJUjUkYIqSijDRoxWnRQLKdqP+/iHXL9ELoVcJTByLKACDbLrB/+D391a+ckJLykUBzpfHOdjBOjaBRo1x/k+dpzGCRB8Bq70lr9SB2Y+Sa+1tOgR0L8NXFy3NGUPuNwBBp8M2ZRdKUhTyOeB9zP6piwQvgV617zemvs4fQDS1FXyBjg4BEYLlL3u8+7u9t7+PdPs7wdkRXKhyqpX4AAAAAZiS0dEAAAAAAD/1EFU8gAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+QJFRQALXUmYTEAAAAZdEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIEdJTVBXgQ4XAAACKUlEQVRYw71X7ZLjMAiTYN//jXd0P/yFCU7SvbvtDOPWgBCGxJQkYWYfCmHm+x4N5mcfmsEr/we/5Tt8li+73iMHM9DHHkHzENdAEu4+eZBL5zOWg86JZ+YbR6eBFs7NQx5cOFO3+fXvbmC2zRws1cYXRvbL8qQf8gUJ+P5u8vDRBzqllQ/+JywBsGIPAXfs6QZvCB8wmOxOeJb27uwz/ikWX3BQgVXlf9Jfbdiz+Q0hAP8L/b+IO/L1g92dzov1rd9TnKoOXvgz6SocP3AuYhM/7oBPq/UT+7tT8B+c8l1V86laUXH7Zfn/cb9IwGwJDXADzFTsReHVj4J5tlv2EyfaEfN70yvg84C1OLWVBUfuMQ2gCT7yHTEpuDc7M8HIpiNgPn73teDhA4sAh5+dZXC+O8tlo35XB84P+CfMIwaOd1n8psdJgABAlpeWAEDFrSsB3OeE5qKbW7QtjGvmqHVTrtlDoAgR01ndWwNr4nK+G1c89vS4pxDv1pnICNJ8tmMhj1MDyxPWxuPt5MHTRJS27d1Yxiu0Tu2gehIhFwpH8VmkwT6YqIDkOkTtfbSZkn2PwWwVVav3GgW1mEpdKy3OokI7ra4l2P2RGrCJlAYvoR4JJ2TsvHwSfD2Wvx247SPr7WlPk6aK3uP+lO4grAmrSJbXt4JC4PhkzhJNftrAJfXCs//upacSLgAq5diSIRWKc/3/wdvntHqbcuPIyPcyy3/w9+PF5w8xhbP1sQP9IwAAAABJRU5ErkJggg=='))
        temp_png.flush()

        args = parser.parse_args(['image', '--input_file', temp_png.name, '--packed', '--output_format', 'c_header'])

        image.run(args)

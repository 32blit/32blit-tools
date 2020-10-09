import base64
import pathlib
import tempfile

import pytest


@pytest.fixture
def png_file():
    temp_png = tempfile.NamedTemporaryFile('wb', suffix='.png')
    temp_png.write(base64.b64decode(b'iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAMAAAD04JH5AAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAyNpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+IDx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IkFkb2JlIFhNUCBDb3JlIDUuNi1jMTQ4IDc5LjE2NDAzNiwgMjAxOS8wOC8xMy0wMTowNjo1NyAgICAgICAgIj4gPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4gPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIgeG1sbnM6eG1wPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RSZWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZVJlZiMiIHhtcDpDcmVhdG9yVG9vbD0iQWRvYmUgUGhvdG9zaG9wIDIxLjAgKFdpbmRvd3MpIiB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOjE5NkU4OENBNTk3NDExRUFCMTgyODFBRDFGMTZDODJGIiB4bXBNTTpEb2N1bWVudElEPSJ4bXAuZGlkOjE5NkU4OENCNTk3NDExRUFCMTgyODFBRDFGMTZDODJGIj4gPHhtcE1NOkRlcml2ZWRGcm9tIHN0UmVmOmluc3RhbmNlSUQ9InhtcC5paWQ6MTk2RTg4Qzg1OTc0MTFFQUIxODI4MUFEMUYxNkM4MkYiIHN0UmVmOmRvY3VtZW50SUQ9InhtcC5kaWQ6MTk2RTg4Qzk1OTc0MTFFQUIxODI4MUFEMUYxNkM4MkYiLz4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz4ohDCNAAAACVBMVEUAAAD///8A/wDg4n4DAAAAmklEQVR42uzZMQqAMAxA0er9D+1Wl1ITijTi+6PQ8qYYsTVJUu/Ilj569gAAAABqAtIDM30UAAAAoDrAuwAAAODLK9nCdAQAAACoBHh/FD84AQAAALYDJEnpQTk6MPgCD98LAAAAUAiQXkXT9wIAAADUBEx/qEQBg2fhUQwAAAAAAAAAAHADFnbCKSC8EwIAAABsAkjST7sEGACd4xph9WtahAAAAABJRU5ErkJggg=='))
    temp_png.flush()
    return temp_png


@pytest.fixture
def output_dir():
    temp_output = tempfile.NamedTemporaryFile('w', suffix='.hpp')
    return pathlib.Path(temp_output.name).parents[0]


@pytest.fixture
def palette_file():
    temp_pal = tempfile.NamedTemporaryFile('wb', suffix='.act')
    temp_pal.write(b'\x00\x00\x00')  # Write black colour
    temp_pal.write(b'\x00\xff\x00')  # Write green colour
    temp_pal.write(b'\xff\xff\xff')  # Write white colour
    temp_pal.write(b'\x00' * 759)  # Pad to 772 bytes
    temp_pal.write(b'\x00\x03')  # Write size
    temp_pal.write(b'\x00\x00')  # Ignored bytes
    temp_pal.flush()
    return temp_pal


@pytest.fixture
def yml_file_relative_paths(png_file, palette_file):
    png_file = pathlib.Path(png_file.name)
    palette_file = pathlib.Path(palette_file.name)
    temp_yml = tempfile.NamedTemporaryFile('w', suffix='.yml')
    temp_yml.write(f'''assets.hpp:
  {png_file.name}:
    palette: {palette_file.name}
    name: asset_test
''')
    temp_yml.flush()
    return temp_yml


@pytest.fixture
def tools(parsers):
    from ttblit.asset import font, image, map, raw

    parser, subparser = parsers
    tools = {}
    tools[image.ImageAsset.command] = image.ImageAsset(subparser)
    tools[font.FontAsset.command] = font.FontAsset(subparser)
    tools[map.MapAsset.command] = map.MapAsset(subparser)
    tools[raw.RawAsset.command] = raw.RawAsset(subparser)
    return tools


def test_packer_cli_no_args(parsers):
    from ttblit.tool import packer

    parser, subparser = parsers

    packer = packer.Packer(subparser)

    args = parser.parse_args(['pack'])

    packer.run(args)


def test_packer_cli_relative_yml(parsers, tools, yml_file_relative_paths, output_dir):
    from ttblit.tool import packer

    parser, subparser = parsers

    packer = packer.Packer(subparser)
    packer.register_asset_builders(tools)

    args = parser.parse_args(['pack', '--force', '--config', yml_file_relative_paths.name, '--output', str(output_dir)])

    packer.run(args)

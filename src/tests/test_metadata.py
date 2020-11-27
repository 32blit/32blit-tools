import base64
import tempfile

import pytest


@pytest.fixture
def test_icns_file():
    temp_icns = tempfile.NamedTemporaryFile('rb+', suffix='.icns')
    return temp_icns


@pytest.fixture
def test_binary_file():
    temp_bin = tempfile.NamedTemporaryFile('wb', suffix='.bin')
    temp_bin.write(b'BLIT000000000000\x14\x00\x00\x00')
    temp_bin.flush()
    return temp_bin


@pytest.fixture
def test_invalid_binary_file():
    temp_bin = tempfile.NamedTemporaryFile('wb', suffix='.bin')
    temp_bin.write(b'BLIT000000000000\x10\x00\x00\x00')
    temp_bin.flush()
    return temp_bin


@pytest.fixture
def test_metadata_file():
    temp_icon = tempfile.NamedTemporaryFile('wb', suffix='.png')
    temp_icon.write(base64.b64decode(b'iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAMAAAD04JH5AAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAyNpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+IDx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IkFkb2JlIFhNUCBDb3JlIDUuNi1jMTQ4IDc5LjE2NDAzNiwgMjAxOS8wOC8xMy0wMTowNjo1NyAgICAgICAgIj4gPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4gPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIgeG1sbnM6eG1wPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RSZWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZVJlZiMiIHhtcDpDcmVhdG9yVG9vbD0iQWRvYmUgUGhvdG9zaG9wIDIxLjAgKFdpbmRvd3MpIiB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOjE5NkU4OENBNTk3NDExRUFCMTgyODFBRDFGMTZDODJGIiB4bXBNTTpEb2N1bWVudElEPSJ4bXAuZGlkOjE5NkU4OENCNTk3NDExRUFCMTgyODFBRDFGMTZDODJGIj4gPHhtcE1NOkRlcml2ZWRGcm9tIHN0UmVmOmluc3RhbmNlSUQ9InhtcC5paWQ6MTk2RTg4Qzg1OTc0MTFFQUIxODI4MUFEMUYxNkM4MkYiIHN0UmVmOmRvY3VtZW50SUQ9InhtcC5kaWQ6MTk2RTg4Qzk1OTc0MTFFQUIxODI4MUFEMUYxNkM4MkYiLz4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz4ohDCNAAAACVBMVEUAAAD///8A/wDg4n4DAAAAmklEQVR42uzZMQqAMAxA0er9D+1Wl1ITijTi+6PQ8qYYsTVJUu/Ilj569gAAAABqAtIDM30UAAAAoDrAuwAAAODLK9nCdAQAAACoBHh/FD84AQAAALYDJEnpQTk6MPgCD98LAAAAUAiQXkXT9wIAAADUBEx/qEQBg2fhUQwAAAAAAAAAAHADFnbCKSC8EwIAAABsAkjST7sEGACd4xph9WtahAAAAABJRU5ErkJggg=='))
    temp_icon.flush()

    tmp_splash = tempfile.NamedTemporaryFile('wb', suffix='.png')
    tmp_splash.write(base64.b64decode(b'iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAAS0lEQVR4nGNkYGD4Xy7PzoANdD78ycBSLs/OkOAAEVhwAELD+AwH2BmYYKoXHECSQFLMxIADwBTjVEDQBBiAK0hwQOhCBowMBLwJACzCE3PfXB5IAAAAAElFTkSuQmCC'))
    tmp_splash.flush()

    temp_yml = tempfile.NamedTemporaryFile('w', suffix='.yml')
    temp_yml.write(f'''title: Rocks & Diamonds
description: A pulse pounding, rock rollin', diamond hunting adventure
author: gadgetoid
icon:
  file: {temp_icon.name}
splash:
  file: {tmp_splash.name}
version: v1.0.0
''')
    temp_yml.flush()
    return temp_yml, temp_icon, tmp_splash


def test_metadata_no_args(parsers):
    from ttblit.tool import metadata

    parser, subparser = parsers

    metadata = metadata.Metadata(subparser)

    with pytest.raises(SystemExit):
        args = parser.parse_args(['metadata'])
        metadata.run(args)


def test_metadata(parsers, test_metadata_file, test_binary_file):
    from ttblit.tool import metadata

    test_metadata_file, test_metadata_icon_png, test_metadata_splash_png = test_metadata_file
    parser, subparser = parsers

    metadata = metadata.Metadata(subparser)

    args = parser.parse_args([
        'metadata',
        '--config', test_metadata_file.name,
        '--file', test_binary_file.name])

    metadata.run(args)


def test_metadata_icns(parsers, test_metadata_file, test_binary_file, test_icns_file):
    from ttblit.tool import metadata

    test_metadata_file, test_metadata_icon_png, test_metadata_splash_png = test_metadata_file
    parser, subparser = parsers

    metadata = metadata.Metadata(subparser)

    args = parser.parse_args([
        'metadata',
        '--config', test_metadata_file.name,
        '--file', test_binary_file.name,
        '--icns', test_icns_file.name,
        '--force'])

    metadata.run(args)

    test_icns_file.flush()
    assert test_icns_file.read()[:4] == b'icns'


def test_metadata_invalid_bin(parsers, test_metadata_file, test_invalid_binary_file):
    from ttblit.tool import metadata

    test_metadata_file, test_metadata_icon_png, test_metadata_splash_png = test_metadata_file
    parser, subparser = parsers

    metadata = metadata.Metadata(subparser)

    args = parser.parse_args([
        'metadata',
        '--config', test_metadata_file.name,
        '--file', test_invalid_binary_file.name])

    with pytest.raises(ValueError):
        metadata.run(args)

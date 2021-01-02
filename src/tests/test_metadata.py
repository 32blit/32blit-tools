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


def test_metadata_no_args(parsers):
    from ttblit.tool import metadata

    parser, subparser = parsers

    metadata = metadata.Metadata(subparser)

    with pytest.raises(SystemExit):
        args = parser.parse_args(['metadata'])
        metadata.run(args)


def test_metadata(parsers, test_resources, test_binary_file):
    from ttblit.tool import metadata

    parser, subparser = parsers

    metadata = metadata.Metadata(subparser)

    args = parser.parse_args([
        'metadata',
        '--config', str(test_resources / 'metadata-basic.yml'),
        '--file', test_binary_file.name])

    metadata.run(args)


def test_metadata_file_associations(parsers, test_resources, test_binary_file):
    from ttblit.tool import metadata

    parser, subparser = parsers

    metadata = metadata.Metadata(subparser)

    args = parser.parse_args([
        'metadata',
        '--config', str(test_resources / 'metadata-file-associations.yml'),
        '--file', test_binary_file.name])

    metadata.run(args)


def test_metadata_icns(parsers, test_resources, test_binary_file, test_icns_file):
    from ttblit.tool import metadata

    parser, subparser = parsers

    metadata = metadata.Metadata(subparser)

    args = parser.parse_args([
        'metadata',
        '--config', str(test_resources / 'metadata-basic.yml'),
        '--file', test_binary_file.name,
        '--icns', test_icns_file.name,
        '--force'])

    metadata.run(args)

    test_icns_file.flush()
    assert test_icns_file.read()[:4] == b'icns'


def test_metadata_invalid_bin(parsers, test_resources, test_invalid_binary_file):
    from ttblit.tool import metadata

    parser, subparser = parsers

    metadata = metadata.Metadata(subparser)

    args = parser.parse_args([
        'metadata',
        '--config', str(test_resources / 'metadata-basic.yml'),
        '--file', test_invalid_binary_file.name])

    with pytest.raises(ValueError):
        metadata.run(args)

import tempfile

import pytest


@pytest.fixture
def test_icns_file():
    temp_icns = tempfile.NamedTemporaryFile('rb+', suffix='.icns')
    return temp_icns

@pytest.fixture
def test_bi_source_file():
    temp_src = tempfile.NamedTemporaryFile('rb+', suffix='.cpp')
    return temp_src

@pytest.fixture
def test_blmeta_file():
    temp_src = tempfile.NamedTemporaryFile('rb+', suffix='.blmeta')
    return temp_src


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


def test_metadata_no_args():
    from ttblit import main

    with pytest.raises(SystemExit):
        main(['metadata'])


def test_metadata(test_resources, test_binary_file):
    from ttblit import main

    with pytest.raises(SystemExit):
        main([
            'metadata',
            '--config', str(test_resources / 'metadata-basic.yml'),
            '--file', test_binary_file.name
        ])


def test_metadata_file_associations(test_resources, test_binary_file):
    from ttblit import main

    with pytest.raises(SystemExit):
        main([
            'metadata',
            '--config', str(test_resources / 'metadata-file-associations.yml'),
            '--file', test_binary_file.name
        ])


def test_metadata_icns(test_resources, test_binary_file, test_icns_file):
    from ttblit import main

    with pytest.raises(SystemExit):
        main([
            'metadata',
            '--config', str(test_resources / 'metadata-basic.yml'),
            '--file', test_binary_file.name,
            '--icns', test_icns_file.name,
            '--force'
        ])

    test_icns_file.flush()
    assert test_icns_file.read()[:4] == b'icns'

def test_metadata_dump(test_resources):
    from ttblit import main

    with pytest.raises(SystemExit):
        main([
            'metadata',
            '--file', str(test_resources / 'doom-fire.blit')
        ])

def test_metadata_pico_bi(test_resources, test_binary_file, test_bi_source_file):
    from ttblit import main

    with pytest.raises(SystemExit):
        main([
            'metadata',
            '--config', str(test_resources / 'metadata-basic.yml'),
            '--pico-bi', test_bi_source_file.name,
            '--force'
        ])

def test_metadata_standalone(test_resources, test_binary_file, test_blmeta_file):
    from ttblit import main

    with pytest.raises(SystemExit):
        main([
            'metadata',
            '--config', str(test_resources / 'metadata-basic.yml'),
            '--metadata-file', test_blmeta_file.name,
            '--force'
        ])

def test_metadata_invalid_bin(test_resources, test_invalid_binary_file):
    from ttblit import main

    with pytest.raises(ValueError):
        main([
            'metadata',
            '--config', str(test_resources / 'metadata-basic.yml'),
            '--file', test_invalid_binary_file.name
        ])

def test_metadata_invalid_splash(test_resources, test_invalid_binary_file):
    from ttblit import main

    with pytest.raises(ValueError):
        main([
            'metadata',
            '--config', str(test_resources / 'metadata-invalid-splash.yml')
        ])

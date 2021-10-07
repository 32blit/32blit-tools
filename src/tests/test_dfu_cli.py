
import tempfile
import pathlib

import pytest


@pytest.fixture
def test_output_file():
    return tempfile.NamedTemporaryFile('wb', suffix='.dfu')


def test_dfu_build(test_resources, test_output_file):
    from ttblit import main

    with pytest.raises(SystemExit):
        main([
            'dfu',
            'build',
            '--input-file', str(test_resources / 'doom-fire.bin'),
            '--output-file', test_output_file.name
        ])


def test_dfu_read(test_resources, test_output_file):
    from ttblit import main

    with pytest.raises(SystemExit):
        main([
            'dfu',
            'build',
            '--input-file', str(test_resources / 'doom-fire.bin'),
            '--output-file', test_output_file.name
        ])

    with pytest.raises(SystemExit):
        main([
            'dfu',
            'read',
            '--input-file', test_output_file.name
        ])


def test_dfu_dump(test_resources, test_output_file):
    from ttblit import main

    with pytest.raises(SystemExit):
        main([
            'dfu',
            'build',
            '--input-file', str(test_resources / 'doom-fire.bin'),
            '--output-file', test_output_file.name
        ])

    with pytest.raises(SystemExit):
        main([
            'dfu',
            'dump',
            '--input-file', test_output_file.name
        ])

    output_bin_file = pathlib.Path(test_output_file.name.replace('.dfu', '-0-0x08000000.bin'))

    assert output_bin_file.is_file()

    output_bin_file.unlink()

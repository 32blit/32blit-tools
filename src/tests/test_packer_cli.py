import pathlib
import tempfile

import pytest


@pytest.fixture
def output_dir():
    temp_output = tempfile.TemporaryDirectory()
    return temp_output.name


def test_packer_cli_no_args():
    from ttblit import main

    with pytest.raises(SystemExit):
        main(['pack'])


def test_packer_cli_relative_yml(test_resources, output_dir):
    from ttblit import main

    with pytest.raises(SystemExit):
        main([
            'pack',
            '--force',
            '--config', str(test_resources / 'assets_relative.yml'),
            '--output', output_dir
        ])

    assert (pathlib.Path(output_dir) / "assets.hpp").exists()
    assert (pathlib.Path(output_dir) / "assets.cpp").exists()


def test_packer_cli_wildcard_format(test_resources, output_dir):
    from ttblit import main

    with pytest.raises(SystemExit):
        main([
            'pack',
            '--force',
            '--config', str(test_resources / 'assets_wildcard_format.yml'),
            '--output', output_dir
        ])

    assert (pathlib.Path(output_dir) / "assets.hpp").exists()
    assert (pathlib.Path(output_dir) / "assets.cpp").exists()

    hpp = open(pathlib.Path(output_dir) / "assets.hpp", "r").read()

    assert "asset_map_level_01" in hpp
    assert "asset_map_level_02" in hpp


def test_packer_cli_wildcard_default(test_resources, output_dir):
    from ttblit import main

    with pytest.raises(SystemExit):
        main([
            'pack',
            '--force',
            '--config', str(test_resources / 'assets_wildcard_default.yml'),
            '--output', output_dir
        ])

    assert (pathlib.Path(output_dir) / "assets.hpp").exists()
    assert (pathlib.Path(output_dir) / "assets.cpp").exists()

    hpp = open(pathlib.Path(output_dir) / "assets.hpp", "r").read()

    assert "asset_level_01_tmx" in hpp
    assert "asset_level_02_tmx" in hpp


def test_packer_cli_invalid_input(test_resources, output_dir):
    from ttblit import main

    with pytest.raises(SystemExit):
        main([
            'pack',
            '--force',
            '--config', str(test_resources / 'assets_invalid_input.yml'),
            '--output', output_dir
        ])

    # TODO: This attribute no longer exists
    # assert packer.targets[0][1][0].type == 'raw/binary'


def test_packer_cli_file_missing(test_resources, output_dir):
    from ttblit import main

    with pytest.raises(RuntimeError):
        main([
            'pack',
            '--force',
            '--config', str(test_resources / 'assets_file_missing.yml'),
            '--output', output_dir
        ])

    with pytest.raises(RuntimeError):
        main([
            'pack',
            '--force',
            '--config', str(test_resources / 'assets_one_file_missing.yml'),
            '--output', output_dir
        ])


def test_packer_cli_multiple_outputs(test_resources, output_dir):
    from ttblit import main

    with pytest.raises(SystemExit):
        main([
            'pack',
            '--force',
            '--config', str(test_resources / 'assets_multi_out.yml'),
            '--output', output_dir
        ])

    assert (pathlib.Path(output_dir) / "assets.hpp").exists()
    assert (pathlib.Path(output_dir) / "assets.cpp").exists()

    hpp = open(pathlib.Path(output_dir) / "assets.hpp", "r").read()

    assert "asset_image_packed" in hpp
    assert "asset_image_raw" in hpp

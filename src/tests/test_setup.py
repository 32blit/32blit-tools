import json
import pathlib
import tempfile


def test_visualstudio_windows():
    from ttblit.tool.setup import visualstudio_config

    with tempfile.TemporaryDirectory() as dir:
        project_path = pathlib.Path(dir)
        sdk_path = pathlib.PureWindowsPath('C:\\Users\\A User\\32blit-sdk')

        visualstudio_config(project_path, sdk_path)

        # check that the generated config parses
        conf_path = project_path / 'CMakeSettings.json'
        assert conf_path.exists()

        json.load(open(conf_path))


def test_vscode_windows():
    from ttblit.tool.setup import vscode_config

    with tempfile.TemporaryDirectory() as dir:
        project_path = pathlib.Path(dir)
        sdk_path = pathlib.PureWindowsPath('C:\\Users\\A User\\32blit-sdk')

        vscode_config(project_path, sdk_path)

        # check that the generated config parses
        conf_path = project_path / '.vscode' / 'settings.json'
        assert conf_path.exists()

        json.load(open(conf_path))

        conf_path = project_path / '.vscode' / 'cmake-kits.json'
        assert conf_path.exists()

        json.load(open(conf_path))
